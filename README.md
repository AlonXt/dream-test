# Senior Platform Engineer Exercise

## System Playground

#### You can try this up and running production system!
- First create a user_id by making a POST request to:
  - https://aye10lq35l.execute-api.us-east-1.amazonaws.com/user
- Then create a ticket by making another POST request to:
  - Add this body- {"user_id": "YOUR-USER-ID"} 
  - https://aye10lq35l.execute-api.us-east-1.amazonaws.com/ticket
- Now you can check on your ticket status by making this GET request:
  - https://aye10lq35l.execute-api.us-east-1.amazonaws.com/ticket?ticket_id=<YOUR_TICKET_ID>

## Setup Instructions

**Prerequisites:**

- AWS account
- Disclaimer: the cloud_formation.yaml is not production ready, but gives a sense of the design
  - You can paste and view it in the ["Application Composer"](https://aws.amazon.com/application-composer/) on AWS console

**Step 1:** Create a new Aurora PostgreSQL cluster in the AWS Console

- Enable DATA API for your database!
- Use the "Query Editor" on AWS console to connect to the DB and create these tables:

```
CREATE TABLE IF NOT EXISTS users (
user_id VARCHAR(255) PRIMARY KEY,
time_created VARCHAR(255) NOT NULL);

CREATE TABLE IF NOT EXISTS tickets (
ticket_id VARCHAR(255) PRIMARY KEY, 
user_id VARCHAR(255) REFERENCES users(user_id), 
time_created VARCHAR(255) NOT NULL, 
time_finished VARCHAR(255), 
response TEXT);
```

**Step 2:** Create two new Standard Queues in the AWS SQS Console

- one for Responses and one for Errors

**Step 3:** Create Lambda Functions for each component in the lambdas directory.

- Runtime: Python 3.12
- Attach correct IAM roles that allows access to RDS and SQS for each lambda
- Set the required environment variables for each lambda
- Give the ticket_creator lambda permissions to invoke the ml_process, and the vice-versa
- Configure the ticket_status_updater lambda to be triggered by the "Response" SQS when receiving a message
- Timeout: Increase to 10 seconds for all lambdas (for "ml_process" make it 7 minutes!)

**Step 4:** Create an API Gateway for an HTTP API

- Create a POST endpoint and link it to the ticket_creator
- Create a GET endpoint and link it to the ticket_getter
- Create a POST endpoint and link it to the user_creator

**Step 5:** Test the setup

- Make a POST request to the API Gateway endpoint to create "user_id" and save it
- Make another POST request to /ticket endpoint to create a ticket_id
- Try to GET from /ticket endpoint with the ticket_id and see what you get 
- Check if the request is stored in the RDS database

## Enjoy!