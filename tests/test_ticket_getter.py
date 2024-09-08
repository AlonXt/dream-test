import json
import os
import unittest
from unittest.mock import MagicMock

from ticket_getter import lambda_handler


class TestTicketGetter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mock_db_client = MagicMock()
        cls.mock_sqs_client = MagicMock()
        cls.valid_event = {
            "queryStringParameters": {
                "ticket_id": "12345"
            }
        }
        cls.record_with_resp = [[{'stringValue': '2024-09-08T15:58:35.361954'}, {'stringValue': 'Happy message'},
                                 {'stringValue': '2024-09-08T15:58:57.253804'}]]
        cls.record_with_timeout_resp = [[{'stringValue': '2024-09-08T13:58:35.361954'}, {'stringValue': 'Sad message'},
                                         {'stringValue': '2024-09-08T19:58:57.253804'}]]
        cls.record_without_resp = [
            [{'stringValue': '2024-09-08T15:58:35.361954'}, {'isNull': "true"}, {'isNull': "true"}]]

    def setUp(self):
        os.environ["DB_CLUSTER_ARN"] = "arn:aws:rds:us-east-1:123456789012:cluster:test-cluster"
        os.environ["SECRET_ARN"] = "arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret"
        os.environ["DB_NAME"] = "dream"
        os.environ["SQS_QUEUE_URL"] = "https://sqs.us-east-1.amazonaws.com/123456789012/test-queue"

    def test_lambda_handler_success(self):
        self.mock_return_values_from_db(self.record_with_resp)

        response = lambda_handler(self.valid_event, None, sqs_client=self.mock_sqs_client,
                                  db_client=self.mock_db_client)

        self.assertEqual(response["statusCode"], 200)
        ticket_response = json.loads(response["body"])["ticket_response"]
        self.assertEqual("Happy message", ticket_response)

    def test_missing_ticket_record(self):
        self.mock_return_values_from_db([])

        response = lambda_handler(self.valid_event, None, sqs_client=self.mock_sqs_client,
                                  db_client=self.mock_db_client)

        self.assertEqual(response["statusCode"], 404)
        self.assertIn("Ticket not found", json.loads(response["body"])["message"])

    def test_missing_ticket_response(self):
        self.mock_return_values_from_db(self.record_without_resp)

        response = lambda_handler(self.valid_event, None, sqs_client=self.mock_sqs_client,
                                  db_client=self.mock_db_client)

        self.assertEqual(response["statusCode"], 202)
        self.assertIn("Ticket response has not completed yet", json.loads(response["body"])["message"])

    def test_processing_time_not_ok(self):
        self.mock_return_values_from_db(self.record_with_timeout_resp)

        response = lambda_handler(self.valid_event, None, sqs_client=self.mock_sqs_client,
                                  db_client=self.mock_db_client)

        self.assertEqual(response["statusCode"], 408)
        self.assertEqual("Ticket processing request timeout", json.loads(response["body"])["message"])

    def mock_return_values_from_db(self, records: list[list]):
        self.mock_db_client.execute_statement.return_value = {"records": records}


if __name__ == '__main__':
    unittest.main()
