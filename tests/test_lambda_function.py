import json
import os
import unittest
from unittest.mock import MagicMock

from botocore.exceptions import ClientError

from lambda_function import lambda_handler, send_response_to_sqs


class TestLambdaFunction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mock_sqs_client = MagicMock()
        cls.mock_db_client = MagicMock()
        cls.valid_event = {
            "queryStringParameters": {
                "user_id": "12345"
            }
        }

    def setUp(self):
        os.environ["DB_CLUSTER_ARN"] = "arn:aws:rds:us-east-1:123456789012:cluster:test-cluster"
        os.environ["SECRET_ARN"] = "arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret"
        os.environ["SQS_QUEUE_URL"] = "https://sqs.us-east-1.amazonaws.com/123456789012/test-queue"

    def test_lambda_handler_success(self):
        self.mock_db_client.execute_statement.return_value = {}
        self.mock_sqs_client.send_message.return_value = {}

        response = lambda_handler(self.valid_event, None, sqs_client=self.mock_sqs_client, db_client=self.mock_db_client)

        self.assertEqual(response["statusCode"], 200)
        self.assertIn("ticket_id", json.loads(response["body"]))

    def test_lambda_handler_missing_user_id(self):
        event = {
            "queryStringParameters": {}
        }

        response = lambda_handler(event, None, sqs_client=self.mock_sqs_client, db_client=self.mock_db_client)

        self.assertEqual(response["statusCode"], 400)
        self.assertIn("User ID is required", json.loads(response["body"])["message"])

    def test_lambda_handler_no_query_params(self):
        event = {}

        response = lambda_handler(event, None, sqs_client=self.mock_sqs_client, db_client=self.mock_db_client)

        self.assertEqual(response["statusCode"], 400)
        self.assertIn("Query param with User ID is required", json.loads(response["body"])["message"])

    def test_no_failure_when_db_query_failed(self):
        self.mock_sqs_client.send_message.return_value = {}
        self.mock_db_client.execute_statement.side_effect = ClientError(
            error_response={'Error': {'Code': '500', 'Message': 'Internal Error'}},
            operation_name='ExecuteStatement'
        )

        response = lambda_handler(self.valid_event, None, sqs_client=self.mock_sqs_client, db_client=self.mock_db_client)

        self.assertEqual(response["statusCode"], 200)
        self.assertIn("ticket_id", json.loads(response["body"]))

    def test_send_response_to_sqs_failure(self):
        self.mock_sqs_client.send_message.side_effect = ClientError(
            error_response={'Error': {'Code': '500', 'Message': 'Internal Error'}},
            operation_name='SendMessage'
        )

        with self.assertRaises(ClientError):
            send_response_to_sqs(self.mock_sqs_client, "ticket123", "12345", "Happy message")


if __name__ == '__main__':
    unittest.main()
