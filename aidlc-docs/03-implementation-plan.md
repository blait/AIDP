# NAIDP 구현 계획

**작성일**: 2026-03-04  
**목표**: 오늘 중 프로토타입 완성

---

## 프로젝트 구조

```
NAIDP/
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── supervisor.py
│   │   ├── voc_agent.py
│   │   ├── kpi_agent.py
│   │   ├── content_agent.py
│   │   └── report_agent.py
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── document_loader.py
│   │   ├── vector_store.py    # S3 Vectors 연동
│   │   └── retriever.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── bedrock_client.py
│   │   └── config.py
│   └── main.py
├── data/
│   └── raw/          # 원본 문서 (PDF 등)
├── outputs/
│   └── reports/      # 생성된 리포트
├── dashboard/
│   └── app.py        # Streamlit 대시보드
├── requirements.txt
├── .env.example
└── README.md
```

---

## 구현 단계

### Step 1: 프로젝트 초기화
```bash
# 디렉토리 구조 생성
# requirements.txt 작성
# .env 설정
```

**핵심 패키지**:
- langgraph
- langchain-aws
- boto3 (S3 Vectors 포함)
- pypdf
- streamlit
- python-dotenv

---

### Step 2: AWS Bedrock 연결

**파일**: `src/utils/bedrock_client.py`

- Claude Sonnet 4.6 연결
- Titan Embeddings 연결
- 재시도 로직

---

### Step 3: RAG 시스템 구현

**파일**: `src/rag/`

1. **document_loader.py**: PDF 파싱, 청킹
2. **vector_store.py**: S3 Vectors 버킷/인덱스 생성, 벡터 업로드
3. **retriever.py**: S3 Vectors 시맨틱 검색

---

### Step 4: 에이전트 구현

**LangGraph 구조**:

```python
# Supervisor가 작업 분배
# 각 에이전트는 독립적으로 실행
# 결과를 Report Agent가 종합
```

**최소 구현**:
- Supervisor: 작업 라우팅
- VOC Agent: 감정 분석, 주요 이슈 추출
- Report Agent: 최종 리포트 생성

---

### Step 5: 출력 생성

1. **텍스트 리포트**: Markdown → PDF
2. **Streamlit 대시보드**: 간단한 UI

---

## 구현 우선순위

### 🔴 Critical (오늘 필수)
1. Bedrock 연결
2. 기본 RAG (FAISS)
3. Supervisor + VOC Agent
4. 텍스트 리포트 생성

### 🟡 Important (시간 있으면)
1. KPI Agent
2. Content Agent
3. Streamlit 대시보드

### 🟢 Nice to Have (다음에)
1. PDF 리포트 생성
2. 고급 검색 기능
3. 에러 핸들링

---

## 다음 액션

바로 구현을 시작하시겠습니까?

**옵션**:
1. "구현 시작" - 전체 코드 생성
2. "단계별 진행" - 하나씩 확인하며 진행
3. "수정 필요" - 계획 조정
