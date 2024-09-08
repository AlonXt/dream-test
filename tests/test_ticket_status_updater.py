import json
import os
import unittest
from unittest.mock import MagicMock

from botocore.exceptions import ClientError

from lambdas.ticket_status_updater import lambda_handler


class TestTicketStatusUpdater(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.valid_event = {
            "Records": [
                {"body": json.dumps(
                    {"user_id": "1234",
                     "ticket_id": "0000",
                     "response": "happy message"}
                )}
            ]
        }

    def setUp(self):
        os.environ["DB_CLUSTER_ARN"] = "arn:aws:rds:us-east-1:123456789012:cluster:test-cluster"
        os.environ["SECRET_ARN"] = "arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret"
        os.environ["DB_NAME"] = "dream"

    def test_lambda_handler_success(self):
        mock_db_client = MagicMock()
        mock_db_client.execute_statement.return_value = {}

        response = lambda_handler(self.valid_event, None, db_client=mock_db_client)

        self.assertEqual(response["statusCode"], 200)
        successfully_handled_ticket_id = json.loads(response["body"])["body"]["tickets_handled_successfully"]
        self.assertEqual(successfully_handled_ticket_id, ["0000"])

    def test_no_failure_when_db_query_failed(self):
        mock_db_client = MagicMock()
        mock_db_client.execute_statement.side_effect = ClientError(
            error_response={'Error': {'Code': '500', 'Message': 'Internal Error'}},
            operation_name='ExecuteStatement'
        )

        with self.assertRaises(Exception):
            lambda_handler(self.valid_event, None, db_client=mock_db_client)


if __name__ == '__main__':
    unittest.main()
