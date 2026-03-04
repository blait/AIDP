"""
NAIDP 메인 진입점
사용법:
  python -m src.main ingest          # 문서 인덱싱
  python -m src.main analyze "쿼리"  # 분석 실행
"""
import sys
from pathlib import Path


def ingest():
    from src.rag.document_loader import load_documents_from_dir
    from src.rag.vector_store import setup_vector_store, upsert_documents
    from src.utils.config import VECTOR_INDEXES

    print("=== 문서 인덱싱 시작 ===")
    setup_vector_store()

    # VOC 인덱스: VOC 보고서
    voc_chunks = load_documents_from_dir("bedrock-sample/4.VOC보고서")
    if voc_chunks:
        upsert_documents(voc_chunks, VECTOR_INDEXES["voc"])
        print(f"VOC 인덱스: {len(voc_chunks)}개 청크")

    # Content 인덱스: 기획서 + 업데이트 내역
    content_chunks = []
    content_chunks.extend(load_documents_from_dir("bedrock-sample/1.콘텐츠기획서"))
    content_chunks.extend(load_documents_from_dir("bedrock-sample/2.업데이트내역"))
    if content_chunks:
        upsert_documents(content_chunks, VECTOR_INDEXES["content"])
        print(f"Content 인덱스: {len(content_chunks)}개 청크")

    print(f"=== 인덱싱 완료 ===")


def analyze(query: str):
    from src.agents.supervisor import run_analysis

    print(f"=== 분석 시작: {query} ===")
    result = run_analysis(query)

    report = result.get("final_report", "")
    print("\n" + "=" * 60)
    print(report)
    print("=" * 60)

    # 리포트 저장
    output_path = Path("outputs/reports/report.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"\n리포트 저장: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]
    if command == "ingest":
        ingest()
    elif command == "analyze":
        query = sys.argv[2] if len(sys.argv) > 2 else "전체 게임 현황 분석"
        analyze(query)
    else:
        print(f"알 수 없는 명령어: {command}")
        print(__doc__)
