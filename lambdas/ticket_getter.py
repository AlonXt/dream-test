import json
import logging
import os
from datetime import datetime, timedelta

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context, sqs_client=None, db_client=None) -> dict:
    db_client = db_client or boto3.client("rds-data")
    sqs_client = sqs_client or boto3.client("sqs")

    query_params = event.get("queryStringParameters")
    if not query_params:
        logger.error("Query parameter is missing")
        return create_response(400, {"message": "Query param with Ticket ID is required"})

    ticket_id = query_params.get("ticket_id")
    if not ticket_id:
        logger.error("Ticket ID is missing in the request.")
        return create_response(400, {"message": "Ticket ID is required"})

    response = get_ticket_record_from_db(db_client, ticket_id)

    if not ticket_record_found(response):
        logger.error(f"No record found for ticket: {ticket_id}")
        return create_response(404, {"message": "Ticket not found"})

    ticket_response = extract_ticket_response(response)
    if not ticket_response:
        return create_response(202, {"message": "Ticket response has not completed yet, try again soon"})

    if not processing_time_ok(sqs_client, ticket_id, response):
        return create_response(408, {"message": "Ticket processing request timeout"})

    return create_response(200, {"ticket_response": ticket_response})


def get_ticket_record_from_db(db_client, ticket_id):
    try:
        select_query = "SELECT time_created, response, time_finished FROM tickets WHERE ticket_id = :ticket_id"
        select_parameters = [{'name': 'ticket_id', 'value': {'stringValue': ticket_id}}]
        response = db_client.execute_statement(
            resourceArn=os.getenv("DB_CLUSTER_ARN"),
            secretArn=os.getenv("SECRET_ARN"),
            database=os.getenv("DB_NAME"),
            sql=select_query,
            parameters=select_parameters
        )
        return response

    except Exception:
        logger.exception("Failed to retrieve request from DB")
        raise


def ticket_record_found(response) -> bool:
    return bool(response['records'])


def processing_time_ok(sqs_client, ticket_id: str, response) -> bool:
    time_created_str = response['records'][0][0]['stringValue']
    time_created = datetime.fromisoformat(time_created_str)
    time_finished_str = response['records'][0][2]['stringValue']
    time_finished = datetime.fromisoformat(time_finished_str)

    time_elapsed = time_finished - time_created
    if time_elapsed <= timedelta(minutes=5):
        return True
    else:
        logger.error("Ticket processing time was more than 1.5 minute ago.")
        send_error_msg_to_sqs(sqs_client, ticket_id, time_elapsed.total_seconds())
        return False


def send_error_msg_to_sqs(sqs_client, ticket_id, processing_time: float) -> None:
    try:
        sqs_client.send_message(
            QueueUrl=os.getenv("SQS_QUEUE_URL"),
            MessageBody=json.dumps(create_sqs_message("Ticket processing request timeout", ticket_id, processing_time))
        )
        logger.info(f"Sent ERROR message to SQS for ticket: {ticket_id}")
    except Exception:
        logger.exception(f"Failed to send message to SQS")
        raise


def create_sqs_message(message, ticket_id, processing_time) -> dict:
    return {
        "ticket_id": ticket_id,
        "processing_time_in_seconds": processing_time,
        "message": message
    }


def extract_ticket_response(response) -> str:
    if "isNull" in response['records'][0][1]:
        return None
    return response['records'][0][1]['stringValue']


def create_response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "body": json.dumps(body)
    }
