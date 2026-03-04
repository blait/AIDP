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

    print("=== 문서 인덱싱 시작 ===")
    setup_vector_store()
    chunks = load_documents_from_dir("data/raw")
    if not chunks:
        print("data/raw 폴더에 PDF 파일이 없습니다.")
        return
    upsert_documents(chunks)
    print(f"=== 인덱싱 완료: {len(chunks)}개 청크 ===")


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
