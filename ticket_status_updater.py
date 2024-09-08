import json
import logging
import os
from datetime import datetime

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context, db_client=None) -> dict:
    db_client = db_client or boto3.client("rds-data")

    tickets_handled = []
    for record in event['Records']:
        message_body = json.loads(record['body'])
        user_id = message_body.get('user_id')
        ticket_id = message_body.get('ticket_id')
        response = message_body.get('response')

        if user_id and ticket_id and response is not None:
            update_db_with_response(db_client, user_id, ticket_id, response)
            tickets_handled.append(ticket_id)
        else:
            logger.error(f"Ticket: {ticket_id} body does not contain required fields. DB not updated!")

    return create_response(200, {"body": {"tickets_handled_successfully": tickets_handled}})


def update_db_with_response(db_client, user_id, ticket_id, response) -> None:
    try:
        query = get_update_query()
        parameters = get_query_params(response, ticket_id, user_id)

        db_client.execute_statement(
            resourceArn=os.getenv("DB_CLUSTER_ARN"),
            secretArn=os.getenv("SECRET_ARN"),
            database=os.getenv("DB_NAME"),
            sql=query,
            parameters=parameters
        )
        logger.info(f"Updated request in DB for user: {user_id}, ticket: {ticket_id} with response: {response}.")
    except Exception:
        logger.exception(f"Failed to update request in DB")
        raise


def get_update_query() -> str:
    return """
        UPDATE tickets
        SET response = :response,
            time_finished = :time_finished
        WHERE user_id = :user_id AND ticket_id = :ticket_id
        """


def get_query_params(response, ticket_id, user_id) -> list:
    return [
        {'name': 'response', 'value': {'stringValue': response}},
        {'name': 'time_finished', 'value': {'stringValue': str(datetime.now().isoformat())}},
        {'name': 'user_id', 'value': {'stringValue': user_id}},
        {'name': 'ticket_id', 'value': {'stringValue': ticket_id}},
    ]


def create_response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "body": json.dumps(body)
    }
