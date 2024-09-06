import json
import logging
import os
import random
import time
import uuid

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context, sqs_client=None, db_client=None) -> dict:
    sqs_client = sqs_client or boto3.client("sqs")
    db_client = db_client or boto3.client("rds-data")
    try:
        query_params = event.get("queryStringParameters")
        if not query_params:
            logger.error("Query parameter is missing, please provide 'user_id' as a query param and try again")
            return create_response(400, {"message": "Query param with User ID is required"})

        user_id = query_params.get("user_id")
        if not user_id:
            logger.error("User ID is missing in the request.")
            return create_response(400, {"message": "User ID is required"})

        ticket_id = str(uuid.uuid4())
        logger.info(f"Generated ticket ID: {ticket_id} for user: {user_id}")

        store_request_in_db(db_client, user_id, ticket_id)

        message = "Happy message" if simulate_ml_service() else "Sad message"
        send_response_to_sqs(sqs_client, ticket_id, user_id, message)

        return create_response(200, {"ticket_id": ticket_id})

    except json.JSONDecodeError:
        logger.error("Invalid JSON in request.")
        return create_response(400, {"message": "Invalid JSON format"})

    except Exception:
        logger.exception(f"Unexpected error")
        return create_response(500, {"message": "Internal server error"})


def store_request_in_db(db_client, user_id, ticket_id) -> None:
    try:
        query = f"INSERT INTO requests (user_id, ticket_id) VALUES ('{user_id}', '{ticket_id}')"
        db_client.execute_statement(
            resourceArn=os.getenv("DB_CLUSTER_ARN"),
            secretArn=os.getenv("SECRET_ARN"),
            database="dream",
            sql=query
        )
        logger.info(f"Stored request in DB for user: {user_id}, ticket: {ticket_id}")
    except ClientError:
        logger.exception(f"Failed to store request in DB")
        return


def simulate_ml_service() -> bool:
    processing_time = random.uniform(0.01, 1.5)
    time.sleep(processing_time)
    result = random.choice([True, False])
    logger.info(f"Simulated ML model, result: {result}, processing time: {processing_time:.3f} seconds")
    return result


def send_response_to_sqs(sqs_client, ticket_id, user_id, message) -> None:
    try:
        sqs_client.send_message(
            QueueUrl=os.getenv("SQS_QUEUE_URL"),
            MessageBody=json.dumps(create_sqs_message(message, ticket_id, user_id))
        )
        logger.info(f"Sent message to SQS for ticket: {ticket_id}, user: {user_id}")
    except ClientError:
        logger.exception(f"Failed to send message to SQS")
        raise


def create_sqs_message(message, ticket_id, user_id) -> dict:
    return {
        "ticket_id": ticket_id,
        "user_id": user_id,
        "message": message
    }


def create_response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "body": json.dumps(body)
    }
