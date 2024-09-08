import json
import logging
import os
import random
import time

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context, sqs_client=None, ml_simulator_max_seconds: int = None) -> dict:
    sqs_client = sqs_client or boto3.client("sqs")
    ml_simulator_max_seconds = ml_simulator_max_seconds or 420
    try:
        body = json.loads(event.get("body", "{}"))
        user_id = body.get("user_id")
        if not user_id:
            logger.error("User ID is missing in the request.")
            return create_response(400, {"message": "User ID is required"})

        ticket_id = body.get("ticket_id")
        if not ticket_id:
            logger.error("Ticket ID is missing in the request.")
            return create_response(400, {"message": "Ticket ID is required"})

        response = "Happy message" if simulate_ml_service(ml_simulator_max_seconds) else "Sad message"
        send_response_to_sqs(sqs_client, ticket_id, user_id, response)

        return create_response(200, {"ticket_id": ticket_id, "response": response})

    except Exception:
        logger.exception(f"Unexpected error")
        return create_response(500, {"message": "Internal server error"})


def simulate_ml_service(ml_simulator_max_seconds: int) -> bool:
    processing_time = random.uniform(1, ml_simulator_max_seconds)
    time.sleep(processing_time)
    result = random.choice([True, False])
    logger.info(f"Simulated ML model, result: {result}, processing time: {processing_time:.3f} seconds")
    return result


def send_response_to_sqs(sqs_client, ticket_id, user_id, response) -> None:
    try:
        sqs_client.send_message(
            QueueUrl=os.getenv("SQS_QUEUE_URL"),
            MessageBody=json.dumps(create_sqs_message(response, ticket_id, user_id))
        )
        logger.info(f"Sent message to SQS for ticket: {ticket_id}, user: {user_id}")
    except Exception:
        logger.exception(f"Failed to send message to SQS")
        raise


def create_sqs_message(response, ticket_id, user_id) -> dict:
    return {
        "ticket_id": ticket_id,
        "user_id": user_id,
        "response": response
    }


def create_response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "body": json.dumps(body)
    }
