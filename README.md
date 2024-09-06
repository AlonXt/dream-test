# dream assignment- Senior Platform Engineer Exercise
## Setup Instructions
**Prerequisites:** 
- AWS account

**Step 1:** Create a new Aurora PostgreSQL cluster in the AWS Console
- Enable DATA API for your database! 
- Ensure that your cluster has a database called "dream" 
- Create table called "requests" with the following schema:
```
CREATE TABLE requests (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    ticket_id VARCHAR(255) NOT NULL
);
```

**Step 2:** Create a new Standard Queue in the AWS Console

**Step 3:** Create a Lambda Function
- Runtime: Python 3.12
- Timeout: Increase to 30 seconds
- Attach an IAM role that allows access to RDS and SQS
- Set the following environment variables:
  - DB_CLUSTER_ARN: Your DB cluster ARN
  - SECRET_ARN: Your RDS secret ARN
  - SQS_QUEUE_URL: Your SQS queue url


**Step 4:** Create an API Gateway for an HTTP API
- Create a GET method and link it to the Lambda function

**Step 5:** Test the setup
- Make a GET request to the API Gateway endpoint with "user_id" query param and expect a "ticket_id"
- Check if the request is stored in the RDS database and if the message is sent to the SQS queue

