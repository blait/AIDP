# NAIDP 시스템 아키텍처 문서

## 1. 프로젝트 개요

NAIDP(게임 인사이트 분석 플랫폼)는 게임 기업의 VOC, KPI, 콘텐츠 기획서, 업데이트 내역, 거래 데이터를 종합 분석하여 인사이트 리포트를 자동 생성하는 AI 멀티 에이전트 시스템입니다.

---

## 2. 전체 아키텍처

```
┌──────────────────────────────────────────────────────────────────┐
│                        Data Sources                              │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐   │
│  │VOC 보고서│  │콘텐츠    │  │업데이트  │  │KPI CSV         │   │
│  │(PDF/DOCX │  │기획서    │  │내역      │  │(직접 로드)     │   │
│  │/TXT)     │  │(PPTX)    │  │(XLSX)    │  │                │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───────┬────────┘   │
│       └──────────────┼─────────────┘                │            │
│                      ▼                              │            │
│            ┌──────────────────┐                     │            │
│            │ Document Loader  │                     │            │
│            │ (PDF/DOCX/PPTX/  │                     │            │
│            │  XLSX/CSV/TXT)   │                     │            │
│            └────────┬─────────┘                     │            │
│                     ▼                               │            │
│            ┌──────────────────┐                     │            │
│            │ Titan Embeddings │                     │            │
│            │ (1024 dim)       │                     │            │
│            └────────┬─────────┘                     │            │
│                     ▼                               │            │
│            ┌──────────────────┐                     │            │
│            │ Amazon S3 Vectors│                     │            │
│            │ (naidp-vectors/  │                     │            │
│            │  naidp-index)    │                     │            │
│            └────────┬─────────┘                     │            │
│                     │                               │            │
└─────────────────────┼───────────────────────────────┼────────────┘
                      │                               │
                      ▼                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                  LangGraph Multi-Agent System                    │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐         │
│  │ VOC Agent   │  │ KPI Agent   │  │ Content Agent    │         │
│  │ (RAG 검색)  │  │ (CSV 직접)  │  │ (RAG 검색)      │         │
│  │ → JSON 출력 │  │ → JSON 출력 │  │ → JSON 출력     │         │
│  └──────┬──────┘  └──────┬──────┘  └────────┬────────┘         │
│         └────────────────┼──────────────────┘                   │
│                          ▼                                       │
│                 ┌─────────────────┐                              │
│                 │ Report Agent    │                              │
│                 │ (종합 → JSON)   │                              │
│                 └─────────────────┘                              │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐       │
│  │ Athena Agent (Text-to-SQL)                           │       │
│  │ 자연어 → SQL 생성 → 검증 → 실행 → 결과 검증 → 인사이트│       │
│  │ (자동 재시도 최대 5회)                                │       │
│  └──────────────────────────────────────────────────────┘       │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐       │
│  │ Chatbot (추가 질문)                                   │       │
│  │ 분석 결과 컨텍스트 + RAG 검색 → Claude 응답           │       │
│  └──────────────────────────────────────────────────────┘       │
└──────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│                   Streamlit Dashboard                            │
│                                                                  │
│  [📊 KPI 대시보드] [📢 VOC] [📝 콘텐츠] [📋 종합] [🔍 Athena]  │
│                                                                  │
│  사이드바: 분석 실행 버튼                                         │
│  하단 고정: 💬 챗봇                                              │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. 에이전트 상세

### 3.1 VOC Agent (`src/agents/voc_agent.py`)

| 항목 | 내용 |
|------|------|
| 데이터 소스 | Amazon S3 Vectors (RAG 시맨틱 검색, `naidp-voc-index`, top_k=5) |
| 입력 | 사용자 쿼리 |
| 처리 | RAG에서 VOC 전용 인덱스 검색 → Claude에게 분석 요청 |
| 출력 (JSON) | 감정 분포(긍정/중립/부정), 이슈 TOP5(제목/심각도/카테고리/조회수), 핵심 키워드, 요약, 위험도, 권고사항 |
| 시각화 | 감정 바차트, 이슈 카드(심각도 배지), 키워드 태그 |

### 3.2 KPI Agent (`src/agents/kpi_agent.py`)

| 항목 | 내용 |
|------|------|
| 데이터 소스 | Athena Agent를 통해 `naidp.kpi` 테이블 조회 |
| 입력 | 사용자 쿼리 |
| 처리 | Athena Agent에게 KPI 데이터 조회 요청 → 결과 수신 → Claude에게 분석 요청 |
| 출력 (JSON) | 지표 하이라이트(트렌드/심각도), 이상 징후, 위험 요소, 요약, 권고사항 |
| 시각화 | 트렌드 아이콘 카드, 경고 배너 |
| 참고 | Athena Agent의 SQL 생성→검증→실행→재시도 로직을 그대로 활용 |

### 3.3 Content Agent (`src/agents/content_agent.py`)

| 항목 | 내용 |
|------|------|
| 데이터 소스 | Amazon S3 Vectors (RAG 시맨틱 검색, `naidp-content-index`, top_k=5) |
| 입력 | 사용자 쿼리 |
| 처리 | RAG에서 콘텐츠 전용 인덱스 검색 → Claude에게 분석 요청 |
| 출력 (JSON) | 업데이트 현황(상태/카테고리), 콘텐츠 건강도(품질점수/빈도/만족도), Gap 분석(기획 vs 실제), 권고사항 |
| 시각화 | 프로그레스바, 상태 카드, Gap 테이블 |

### 3.4 Report Agent (`src/agents/report_agent.py`)

| 항목 | 내용 |
|------|------|
| 데이터 소스 | VOC/KPI/Content Agent의 JSON 결과 |
| 입력 | 3개 에이전트 분석 결과 종합 |
| 처리 | 교차 분석 및 종합 인사이트 도출 |
| 출력 (JSON) | Executive Summary(한줄진단/위험도/점수), 스코어카드(영역별), 교차 인사이트, 액션 아이템(우선순위/담당/기한), 리스크 시나리오 |
| 시각화 | 스코어카드 프로그레스바, 액션 아이템 테이블, 리스크 배지 |

### 3.5 Athena Agent (`src/agents/athena_agent.py`)

| 항목 | 내용 |
|------|------|
| 데이터 소스 | Amazon Athena (S3 기반 테이블) |
| 입력 | 자연어 질문 |
| 처리 흐름 | SQL 생성 → EXPLAIN 검증 → 실행 → 결과 검증 → 인사이트 생성 (실패 시 자동 재시도, 최대 5회) |
| 출력 | 생성된 SQL, 쿼리 결과 (DataFrame), AI 인사이트 |
| 시각화 | 결과 테이블, 자동 라인 차트 (날짜+숫자 컬럼 감지 시) |
| 참조 리포 | [langgraph-tts-redshift](https://github.com/blait/langgraph-tts-redshift) 패턴 기반 |

### 3.6 Chatbot (`src/utils/chatbot.py`)

| 항목 | 내용 |
|------|------|
| 데이터 소스 | 분석 결과 (session_state) + S3 Vectors (VOC 인덱스 top_k=2 + Content 인덱스 top_k=2) |
| 입력 | 사용자 추가 질문 + 대화 히스토리 (최근 3턴) |
| 처리 | 분석 결과 컨텍스트 + RAG 검색 결과를 system prompt에 포함 → Claude 응답 |
| 위치 | 대시보드 하단 고정 (모든 탭에서 접근 가능) |

---

## 4. 에이전트 실행 흐름

### 4.1 인사이트 분석 (메인 워크플로우)

```
[분석 시작 버튼]
       │
       ▼
  VOC Agent ──→ KPI Agent ──→ Content Agent ──→ Report Agent
  (RAG 검색)    (Athena Agent  (RAG 검색)        (결과 종합)
                 경유 조회)
  ↓              ↓              ↓                 ↓
  JSON           JSON           JSON              JSON
       │              │              │                │
       └──────────────┴──────────────┴────────────────┘
                              │
                              ▼
                    Streamlit 시각화 렌더링
```

### 4.2 Athena Text-to-SQL

```
[자연어 질문 입력]
       │
       ▼
  ┌─→ SQL 생성 (Claude + 스키마 정보)
  │        │
  │        ▼
  │   SQL 검증 (EXPLAIN)
  │        │
  │   실패 ←┤→ 성공
  │   ↓     │
  │   재시도 ▼
  │   SQL 실행 (Athena)
  │        │
  │   실패 ←┤→ 성공
  │   ↓     │
  │   재시도 ▼
  │   결과 검증 (Claude)
  │        │
  │   실패 ←┤→ 성공
  │   ↓     │
  └───┘    ▼
      인사이트 생성 (Claude)
           │
           ▼
      테이블 + 차트 + 인사이트 표시
```

---

## 5. 데이터 소스 매핑

### 5.1 RAG (S3 Vectors)

| 인덱스 | 원본 파일 | 형식 | 청크 수 | 사용 에이전트 |
|--------|-----------|------|---------|-------------|
| `naidp-voc-index` | VOC 보고서 상세본 (PDF/DOCX/TXT) | 텍스트 | ~22 | VOC Agent, Chatbot |
| `naidp-voc-index` | VOC 보고서 요약본 (PDF/DOCX/TXT) | 텍스트 | ~14 | VOC Agent, Chatbot |
| `naidp-content-index` | 콘텐츠 기획서 (PPTX) | 텍스트 | ~2 | Content Agent, Chatbot |
| `naidp-content-index` | 업데이트 내역 (XLSX) | 텍스트 | ~50 | Content Agent, Chatbot |

- 벡터 버킷: `naidp-vectors`
- 인덱스 분리: VOC 문서 → `naidp-voc-index`, 기획서/패치노트 → `naidp-content-index`
- 임베딩: Amazon Titan Embeddings v2 (1024 dim, cosine)
- 청킹: 1000자, 200자 오버랩

### 5.2 KPI 대시보드 차트

- KPI 대시보드 탭의 차트는 `bedrock-sample/3.KPI/260218_kpi.csv`를 pandas로 직접 읽어서 렌더링
- KPI Agent의 AI 분석은 Athena Agent를 경유하여 `naidp.kpi` 테이블에서 조회

### 5.3 Athena 테이블

| 테이블 | S3 위치 | 컬럼 | 사용 에이전트 |
|--------|---------|------|-------------|
| `naidp.kpi` | `s3://naidp-data-986930576673/kpi/` | log_date, dau, nu, pu, npu, pur, daily_sales, daily_arppu, daily_arpdau | KPI Agent (Athena Agent 경유), Athena Agent |
| `naidp.transaction_map` | `s3://naidp-data-986930576673/transaction/` | sell_account, buy_account, sell_currency, market_type, cnt, total_price, first_date, last_date | Athena Agent |

---

## 6. AWS 리소스

| 서비스 | 리소스 | 리전 | 용도 |
|--------|--------|------|------|
| Bedrock | Claude Sonnet 4.6 (`us.anthropic.claude-sonnet-4-6`) | us-east-1 | LLM 추론 |
| Bedrock | Titan Embeddings v2 | us-east-1 | 벡터 임베딩 |
| S3 Vectors | `naidp-vectors` / `naidp-voc-index`, `naidp-content-index` | ap-northeast-2 | RAG 벡터 저장/검색 (인덱스 분리) |
| S3 | `naidp-data-986930576673` | ap-northeast-2 | Athena 데이터 + 쿼리 결과 |
| Athena | Database `naidp` | ap-northeast-2 | Text-to-SQL 쿼리 |

---

## 7. 기술 스택

| 구분 | 기술 |
|------|------|
| 언어 | Python 3.11+ |
| LLM | Amazon Bedrock - Claude Sonnet 4.6 |
| 임베딩 | Amazon Bedrock - Titan Embeddings v2 |
| 벡터 스토어 | Amazon S3 Vectors |
| 에이전트 프레임워크 | LangGraph |
| 대시보드 | Streamlit |
| 데이터 웨어하우스 | Amazon Athena |
| AWS SDK | boto3 |

---

## 8. 프로젝트 구조

```
NAIDP/
├── src/
│   ├── agents/
│   │   ├── __init__.py          # AgentState 정의
│   │   ├── supervisor.py        # LangGraph 워크플로우 (순차 실행)
│   │   ├── voc_agent.py         # VOC 분석 (RAG → JSON)
│   │   ├── kpi_agent.py         # KPI 분석 (CSV → JSON)
│   │   ├── content_agent.py     # 콘텐츠 분석 (RAG → JSON)
│   │   ├── report_agent.py      # 종합 리포트 (JSON → JSON)
│   │   └── athena_agent.py      # Text-to-SQL (LangGraph)
│   ├── rag/
│   │   ├── document_loader.py   # PDF/DOCX/PPTX/XLSX/CSV/TXT 로더
│   │   ├── vector_store.py      # S3 Vectors 생성/업로드
│   │   └── retriever.py         # S3 Vectors 검색
│   └── utils/
│       ├── bedrock_client.py    # Claude + Titan 클라이언트
│       ├── athena_client.py     # Athena 쿼리 실행/검증
│       ├── chatbot.py           # 챗봇 (컨텍스트 + RAG)
│       ├── config.py            # 환경 설정
│       └── progress.py          # 진행 상황 콜백
├── dashboard/
│   └── app.py                   # Streamlit 대시보드
├── bedrock-sample/              # 샘플 데이터
├── aidlc-docs/                  # AI-DLC 문서
├── requirements.txt
└── .env.example
```
