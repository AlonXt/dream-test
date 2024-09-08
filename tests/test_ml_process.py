import json
import os
import unittest
from unittest.mock import MagicMock

from botocore.exceptions import ClientError

from ml_process import lambda_handler


class TestMLProcess(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mock_sqs_client = MagicMock()
        cls.valid_event = {"body": json.dumps({"user_id": "test_user_id", "ticket_id": "test_ticket_id"})}

    def setUp(self):
        os.environ["SQS_QUEUE_URL"] = "https://sqs.us-east-1.amazonaws.com/123456789012/test-queue"

    def test_lambda_handler_success(self):
        self.mock_sqs_client.send_message.return_value = {}

        response = lambda_handler(self.valid_event, None, self.mock_sqs_client, 2)

        self.assertEqual(response["statusCode"], 200)
        self.assertIn("ticket_id", json.loads(response["body"]))
        self.assertIn("response", json.loads(response["body"]))

    def test_lambda_handler_missing_user_id(self):
        event = {"body": json.dumps({"ticket_id": "test_ticket_id"})}

        response = lambda_handler(event, None, self.mock_sqs_client, 2)

        self.assertEqual(response["statusCode"], 400)
        self.assertIn("User ID is required", json.loads(response["body"])["message"])

    def test_lambda_handler_missing_ticket_id(self):
        event = {"body": json.dumps({"user_id": "test_user_id"})}

        response = lambda_handler(event, None, self.mock_sqs_client, 2)

        self.assertEqual(response["statusCode"], 400)
        self.assertIn("Ticket ID is required", json.loads(response["body"])["message"])

    def test_failure_sending_sqs_message(self):
        mock_sqs_client = MagicMock()
        mock_sqs_client.send_message.side_effect = ClientError(
            error_response={'Error': {'Code': '500', 'Message': 'Internal Error'}},
            operation_name='SendMessage'
        )

        response = lambda_handler(self.valid_event, None, mock_sqs_client, 2)

        self.assertEqual(response["statusCode"], 500)
        self.assertIn("Internal server error", json.loads(response["body"])["message"])


if __name__ == '__main__':
    unittest.main()
