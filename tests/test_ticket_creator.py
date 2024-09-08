import json
import os
import unittest
from unittest.mock import MagicMock

from botocore.exceptions import ClientError

from ticket_creator import lambda_handler


class TestTicketCreator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mock_lambda_client = MagicMock()
        cls.mock_db_client = MagicMock()
        cls.valid_event = {"body": json.dumps({"user_id": "test_user_id"})}

    def setUp(self):
        os.environ["DB_CLUSTER_ARN"] = "arn:aws:rds:us-east-1:1234:cluster:test-cluster"
        os.environ["SECRET_ARN"] = "arn:aws:secretsmanager:us-east-1:1234:secret:test-secret"
        os.environ["DB_NAME"] = "db_name"
        os.environ["ML_PROCESS_LAMBDA_ARN"] = "arn:aws:lambda:us-east-1:1234:cluster:test-cluster"

    def test_lambda_handler_success(self):
        self.mock_db_client.execute_statement.return_value = {"records": ["userExists"]}
        self.mock_lambda_client.invoke().return_value = {}

        response = lambda_handler(self.valid_event, None, self.mock_db_client, self.mock_lambda_client)

        self.assertEqual(response["statusCode"], 200)
        self.assertIn("ticket_id", json.loads(response["body"]))

    def test_lambda_handler_missing_user_id(self):
        event = {"body": json.dumps({})}

        response = lambda_handler(event, None, self.mock_db_client, self.mock_lambda_client)

        self.assertEqual(response["statusCode"], 400)
        self.assertIn("User ID is required", json.loads(response["body"])["message"])

    def test_failure_when_user_id_doesnt_exists(self):
        mock_db_client = MagicMock()
        mock_db_client.execute_statement.return_value = {"records": []}

        response = lambda_handler(self.valid_event, None, mock_db_client, self.mock_lambda_client)

        self.assertEqual(response["statusCode"], 404)

    def test_invoke_ml_process_failure(self):
        self.mock_db_client.execute_statement.return_value = {"records": ["userExists"]}
        mock_lambda_client = MagicMock()
        mock_lambda_client.invoke.side_effect = ClientError(
            error_response={'Error': {'Code': '500', 'Message': 'Internal Error'}},
            operation_name='Invoke'
        )

        response = lambda_handler(self.valid_event, None, self.mock_db_client, mock_lambda_client)

        self.assertEqual(response["statusCode"], 500)
        self.assertIn("Internal server error", json.loads(response["body"])["message"])

    def test_db_failure(self):
        mock_db_client = MagicMock()
        mock_db_client.execute_statement.side_effect = ClientError(
            error_response={'Error': {'Code': '500', 'Message': 'Internal Error'}},
            operation_name='ExecuteStatement'
        )

        response = lambda_handler(self.valid_event, None, mock_db_client, self.mock_lambda_client)

        self.assertEqual(response["statusCode"], 500)
        self.assertIn("Internal server error", json.loads(response["body"])["message"])


if __name__ == '__main__':
    unittest.main()
