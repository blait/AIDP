import json
import boto3
from src.utils.config import BEDROCK_REGION, BEDROCK_MODEL_ID, BEDROCK_EMBEDDING_MODEL_ID


def get_bedrock_client():
    from botocore.config import Config
    return boto3.client(
        "bedrock-runtime",
        region_name=BEDROCK_REGION,
        config=Config(read_timeout=300, connect_timeout=10),
    )


def invoke_llm(messages: list, system: str = "") -> str:
    client = get_bedrock_client()
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "messages": messages,
    }
    if system:
        body["system"] = system

    response = client.invoke_model(modelId=BEDROCK_MODEL_ID, body=json.dumps(body))
    result = json.loads(response["body"].read())
    return result["content"][0]["text"]


def get_embedding(text: str) -> list[float]:
    client = get_bedrock_client()
    body = {"inputText": text, "dimensions": 1024, "normalize": True}
    response = client.invoke_model(
        modelId=BEDROCK_EMBEDDING_MODEL_ID, body=json.dumps(body)
    )
    result = json.loads(response["body"].read())
    return result["embedding"]
