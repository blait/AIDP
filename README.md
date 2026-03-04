# NAIDP - 게임 인사이트 분석 플랫폼

## 설치

```bash
pip install -r requirements.txt
```

## 환경 설정

```bash
cp .env.example .env
# .env 파일에서 AWS 설정 확인
```

AWS 자격증명은 `~/.aws/credentials` 또는 환경변수로 설정하세요.

## 사용법

### 1. 문서 인덱싱

`data/raw/` 폴더에 PDF 파일을 넣고 실행:

```bash
python -m src.main ingest
```

### 2. 분석 실행

```bash
python -m src.main analyze "이번 달 주요 이슈와 KPI 현황 분석"
```

### 3. 웹 대시보드

```bash
streamlit run dashboard/app.py
```

## 아키텍처

```
VOC Agent ─┐
KPI Agent ──┼─→ Report Agent → 최종 리포트
Content Agent ─┘
```

- **LLM**: Claude Sonnet 4.6 (Amazon Bedrock, jp 리전)
- **Embeddings**: Amazon Titan Embeddings v2
- **벡터 스토어**: Amazon S3 Vectors
- **프레임워크**: LangGraph
