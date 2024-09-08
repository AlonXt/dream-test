import json
import os
import unittest
from unittest.mock import MagicMock

from botocore.exceptions import ClientError

from lambdas.user_creator import lambda_handler


class TestUserCreator(unittest.TestCase):

    def setUp(self):
        os.environ["DB_CLUSTER_ARN"] = "arn:aws:rds:us-east-1:123456789012:cluster:test-cluster"
        os.environ["SECRET_ARN"] = "arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret"
        os.environ["DB_NAME"] = "dream"

    def test_lambda_handler_success(self):
        mock_db_client = MagicMock()
        mock_db_client.execute_statement.return_value = {}

        response = lambda_handler(None, None, db_client=mock_db_client)

        self.assertEqual(response["statusCode"], 200)
        self.assertIn("user_id", json.loads(response["body"]))

    def test_no_failure_when_db_query_failed(self):
        mock_db_client = MagicMock()
        mock_db_client.execute_statement.side_effect = ClientError(
            error_response={'Error': {'Code': '500', 'Message': 'Internal Error'}},
            operation_name='ExecuteStatement'
        )

        response = lambda_handler(None, None, db_client=mock_db_client)

        self.assertEqual(response["statusCode"], 500)
        self.assertIn("Internal server error", json.loads(response["body"])["message"])


if __name__ == '__main__':
    unittest.main()
