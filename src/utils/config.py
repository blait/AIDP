import os
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")
BEDROCK_REGION = os.getenv("BEDROCK_REGION", "us-east-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "naidp-documents")
S3_VECTORS_BUCKET_NAME = os.getenv("S3_VECTORS_BUCKET_NAME", "naidp-vectors")
S3_VECTORS_INDEX_NAME = os.getenv("S3_VECTORS_INDEX_NAME", "naidp-index")

# 인덱스별 분류
VECTOR_INDEXES = {
    "voc": "naidp-voc-index",
    "content": "naidp-content-index",
}
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-6")
BEDROCK_EMBEDDING_MODEL_ID = os.getenv("BEDROCK_EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0")
EMBEDDING_DIMENSION = 1024

ATHENA_DATABASE = os.getenv("ATHENA_DATABASE", "naidp")
ATHENA_OUTPUT_LOCATION = os.getenv("ATHENA_OUTPUT_LOCATION", "s3://naidp-data-986930576673/athena-results/")
