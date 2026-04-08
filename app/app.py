import os
import uuid
from datetime import datetime, timezone

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from flask import Flask, request
from flask_restful import Api, Resource

AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
TABLE_NAME = os.getenv("DYNAMODB_TABLE", "feedback-table")

config = Config(
    connect_timeout=1,
    read_timeout=1,
    retries={"mode": "standard", "total_max_attempts": 3},
)

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION, config=config)
table = dynamodb.Table(TABLE_NAME)

app = Flask(__name__)
api = Api(app)

class Health(Resource):
    def get(self):
        return {"status": "ok", "service": "feedback-api"}, 200

class FeedbackList(Resource):
    def post(self):
        data = request.get_json(force=True)
        required_fields = ["name", "email", "message"]
        missing = [field for field in required_fields if not data.get(field)]
        if missing:
            return {"error": f"Missing fields: {', '.join(missing)}"}, 400

        item = {
            "feedback_id": str(uuid.uuid4()),
            "name": data["name"].strip(),
            "email": data["email"].strip(),
            "message": data["message"].strip(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            table.put_item(Item=item)
            return {"message": "Feedback submitted", "item": item}, 201
        except ClientError as err:
            return {
                "error": "Failed to store feedback",
                "code": err.response.get("Error", {}).get("Code", "Unknown"),
            }, 500

class FeedbackItem(Resource):
    def get(self, feedback_id):
        try:
            response = table.get_item(Key={"feedback_id": feedback_id})
            item = response.get("Item")
            if not item:
                return {"error": "Feedback not found"}, 404
            return item, 200
        except ClientError as err:
            return {
                "error": "Failed to fetch feedback",
                "code": err.response.get("Error", {}).get("Code", "Unknown"),
            }, 500

api.add_resource(Health, "/health")
api.add_resource(FeedbackList, "/feedback")
api.add_resource(FeedbackItem, "/feedback/<string:feedback_id>")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)