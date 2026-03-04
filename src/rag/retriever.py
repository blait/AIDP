import boto3
from src.utils.config import AWS_REGION, S3_VECTORS_BUCKET_NAME, VECTOR_INDEXES
from src.utils.bedrock_client import get_embedding


def retrieve(query: str, index_type: str = "voc", top_k: int = 5) -> list[dict]:
    """지정된 인덱스에서 쿼리와 유사한 문서 청크 검색

    Args:
        query: 검색 쿼리
        index_type: "voc" 또는 "content"
        top_k: 반환할 결과 수
    """
    client = boto3.client("s3vectors", region_name=AWS_REGION)
    index_name = VECTOR_INDEXES.get(index_type)
    if not index_name:
        raise ValueError(f"Unknown index_type: {index_type}. Use: {list(VECTOR_INDEXES.keys())}")

    query_embedding = get_embedding(query)

    response = client.query_vectors(
        vectorBucketName=S3_VECTORS_BUCKET_NAME,
        indexName=index_name,
        queryVector={"float32": query_embedding},
        topK=top_k,
        returnMetadata=True,
    )

    results = []
    for item in response.get("vectors", []):
        metadata = item.get("metadata", {})
        results.append({
            "text": metadata.get("text", ""),
            "source": metadata.get("source", ""),
        })

    return results


def format_context(results: list[dict]) -> str:
    """검색 결과를 LLM 컨텍스트 형식으로 변환"""
    parts = []
    for i, r in enumerate(results, 1):
        parts.append(f"[문서 {i} - 출처: {r['source']}]\n{r['text']}")
    return "\n\n".join(parts)
