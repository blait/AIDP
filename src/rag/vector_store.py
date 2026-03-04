import boto3
from src.utils.config import AWS_REGION, S3_VECTORS_BUCKET_NAME, VECTOR_INDEXES, EMBEDDING_DIMENSION
from src.utils.bedrock_client import get_embedding


def get_s3vectors_client():
    return boto3.client("s3vectors", region_name=AWS_REGION)


def setup_vector_store():
    """S3 Vectors 버킷 및 인덱스별 생성"""
    client = get_s3vectors_client()

    try:
        client.create_vector_bucket(vectorBucketName=S3_VECTORS_BUCKET_NAME)
        print(f"Vector bucket created: {S3_VECTORS_BUCKET_NAME}")
    except client.exceptions.ConflictException:
        print(f"Vector bucket already exists: {S3_VECTORS_BUCKET_NAME}")

    for label, index_name in VECTOR_INDEXES.items():
        try:
            client.create_index(
                vectorBucketName=S3_VECTORS_BUCKET_NAME,
                indexName=index_name,
                dataType="float32",
                dimension=EMBEDDING_DIMENSION,
                distanceMetric="cosine",
                metadataConfiguration={
                    "nonFilterableMetadataKeys": ["text", "source", "file_path", "chunk_index"]
                },
            )
            print(f"Vector index created: {index_name} ({label})")
        except client.exceptions.ConflictException:
            print(f"Vector index already exists: {index_name} ({label})")


def upsert_documents(chunks: list[dict], index_name: str):
    """문서 청크를 임베딩하여 지정된 인덱스에 저장"""
    client = get_s3vectors_client()
    vectors = []

    for chunk in chunks:
        embedding = get_embedding(chunk["text"])
        vectors.append({
            "key": chunk["id"],
            "data": {"float32": embedding},
            "metadata": {
                "text": chunk["text"],
                **chunk["metadata"],
            },
        })

        if len(vectors) >= 500:
            client.put_vectors(
                vectorBucketName=S3_VECTORS_BUCKET_NAME,
                indexName=index_name,
                vectors=vectors,
            )
            print(f"Uploaded {len(vectors)} vectors → {index_name}")
            vectors = []

    if vectors:
        client.put_vectors(
            vectorBucketName=S3_VECTORS_BUCKET_NAME,
            indexName=index_name,
            vectors=vectors,
        )
        print(f"Uploaded {len(vectors)} vectors → {index_name}")
