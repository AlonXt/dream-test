import json
import logging
import os
import uuid
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context, db_client=None) -> dict:
    try:
        db_client = db_client or boto3.client("rds-data")
        user_id = str(uuid.uuid4())
        store_user_in_db(db_client, user_id)
        return create_response(200, {"user_id": user_id})
    except Exception:
        logger.exception(f"Unexpected error")
        return create_response(500, {"message": "Internal server error"})


def store_user_in_db(db_client, user_id):
    try:
        query = get_store_query()
        parameters = get_store_params(user_id)

        resp = db_client.execute_statement(
            resourceArn=os.getenv("DB_CLUSTER_ARN"),
            secretArn=os.getenv("SECRET_ARN"),
            database=os.getenv("DB_NAME"),
            sql=query,
            parameters=parameters
        )
        logger.info(f"Stored user in DB, ID: {user_id}")
        return resp

    except Exception:
        logger.exception(f"Failed to store user in DB")
        raise


def get_store_query() -> str:
    return """
            INSERT INTO users (user_id, time_created)
            VALUES (:user_id, :time_created)
        """


def get_store_params(user_id) -> list:
    return [
        {'name': 'user_id', 'value': {'stringValue': user_id}},
        {'name': 'time_created', 'value': {'stringValue': str(datetime.now().isoformat())}}
    ]


def create_response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "body": json.dumps(body)
    }
