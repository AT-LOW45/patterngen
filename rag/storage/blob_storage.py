import os
import boto3
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

client = boto3.client(
    "s3",
    endpoint_url=os.getenv("BLOB_ENDPOINT"),
    aws_access_key_id=os.getenv("BLOB_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("BLOB_SECRET_KEY"),
    region_name="us-east-1",
)

BUCKET = os.getenv("BLOB_BUCKET", "patterngen-docs")

def upload_document(content: str, source: str) -> None:
    client.put_object(
        Bucket=BUCKET,
        Key=f"{source}.md",
        Body=content.encode("utf-8"),
        ContentType="text/markdown",
    )

def get_document(source: str) -> str:
    response = client.get_object(Bucket=BUCKET, Key=f"{source}.md")
    return response["Body"].read().decode("utf-8")

def delete_document(source: str) -> None:
    client.delete_object(Bucket=BUCKET, Key=f"{source}.md")