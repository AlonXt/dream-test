import json
import logging
import os
import uuid
from datetime import datetime

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context, db_client=None, lambda_client=None) -> dict:
    db_client = db_client or boto3.client("rds-data")
    lambda_client = lambda_client or boto3.client('lambda')
    try:
        body = json.loads(event.get("body", "{}"))
        user_id = body.get("user_id")
        if not user_id:
            logger.error("User ID is missing in the request body.")
            return create_response(400, {"message": "User ID is required in the request body"})

        if not user_exists(db_client, user_id):
            logger.error(f"User ID {user_id} does not exist in the database.")
            return create_response(404, {"message": "User ID not found"})

        ticket_id = str(uuid.uuid4())
        logger.info(f"Generated ticket ID: {ticket_id} for user: {user_id}")
        store_request_in_db(db_client, ticket_id, user_id)

        invoke_ml_process(lambda_client, ticket_id, user_id)

        return create_response(200, {"ticket_id": ticket_id})

    except json.JSONDecodeError:
        logger.error("Invalid JSON in request.")
        return create_response(400, {"message": "Invalid JSON format"})

    except Exception:
        logger.exception(f"Unexpected error")
        return create_response(500, {"message": "Internal server error"})


def user_exists(db_client, user_id: str) -> bool:
    try:
        select_query = "SELECT user_id FROM users WHERE user_id = :user_id"
        parameters = [{'name': 'user_id', 'value': {'stringValue': user_id}}]

        response = db_client.execute_statement(
            resourceArn=os.getenv("DB_CLUSTER_ARN"),
            secretArn=os.getenv("SECRET_ARN"),
            database=os.getenv("DB_NAME"),
            sql=select_query,
            parameters=parameters
        )

        return len(response['records']) > 0

    except Exception:
        logger.exception("Failed to query user from the database")
        raise


def store_request_in_db(db_client, ticket_id, user_id) -> None:
    try:
        query = get_store_query()
        parameters = get_store_params(ticket_id, user_id)

        db_client.execute_statement(
            resourceArn=os.getenv("DB_CLUSTER_ARN"),
            secretArn=os.getenv("SECRET_ARN"),
            database=os.getenv("DB_NAME"),
            sql=query,
            parameters=parameters
        )
        logger.info(f"Stored request in DB for user: {user_id}, ticket: {ticket_id}")
    except Exception:
        logger.exception(f"Failed to store request in DB")
        raise


def get_store_query() -> str:
    return """
            INSERT INTO tickets (ticket_id, user_id, time_created, response)
            VALUES (:ticket_id, :user_id, :time_created, :response)
        """


def get_store_params(ticket_id, user_id) -> list:
    return [
        {'name': 'ticket_id', 'value': {'stringValue': ticket_id}},
        {'name': 'user_id', 'value': {'stringValue': user_id}},
        {'name': 'time_created', 'value': {'stringValue': str(datetime.now().isoformat())}},
        {'name': 'response', 'value': {'isNull': True}}
    ]


def create_response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "body": json.dumps(body)
    }


def invoke_ml_process(lambda_client, ticket_id, user_id) -> None:
    try:
        body = {"ticket_id": ticket_id, "user_id": user_id}
        event = {"body": json.dumps(body)}
        resp = lambda_client.invoke(
            FunctionName=os.getenv("ML_PROCESS_LAMBDA_ARN"),
            InvocationType='Event',
            Payload=json.dumps(event)
        )
        logger.info(resp)
    except Exception:
        logger.exception("failed to invoke ML process lambda")
        raise
