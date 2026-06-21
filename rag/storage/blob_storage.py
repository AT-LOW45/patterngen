import os
import boto3
from pathlib import Path
from dotenv import load_dotenv
from exception.document_not_found_error import DocumentNotFoundError

load_dotenv(Path(__file__).parent.parent / ".env")

client = boto3.client(
    "s3",
    endpoint_url=os.getenv("BLOB_ENDPOINT"),
    aws_access_key_id=os.getenv("BLOB_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("BLOB_SECRET_KEY"),
    region_name="us-east-1",
)

BUCKET = os.getenv("BLOB_BUCKET", "patterngen-docs")


def upload_to_blob(content: str, source: str) -> None:
    client.put_object(
        Bucket=BUCKET,
        Key=source,
        Body=content.encode("utf-8"),
        ContentType="text/markdown",
    )


def get_from_blob(source: str) -> str:
    try:
        response = client.get_object(Bucket=BUCKET, Key=source)
        return response["Body"].read().decode("utf-8")
    except:
        raise DocumentNotFoundError("no document found")


def delete_from_blob(source: str) -> None:
    client.delete_object(Bucket=BUCKET, Key=f"{source}")
