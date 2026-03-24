# NAIDP - 게임 인사이트 분석 플랫폼

게임 기업의 VOC, KPI, 콘텐츠 기획서, 업데이트 내역을 종합 분석하여 인사이트 리포트를 자동 생성하는 AI 멀티 에이전트 시스템.


<img width="542" height="431" alt="image" src="https://github.com/user-attachments/assets/4ef88aa8-47cc-4a44-bb38-9d96a188ac2a" />

## 아키텍처

```
┌─────────────────────────────────────────┐
│           Data Sources                  │
│  VOC 보고서 | 기획서 | 패치노트 | KPI  │
└──────────────────┬──────────────────────┘
                   ▼
┌──────────────────────────────────────────┐
│         RAG (Amazon S3 Vectors)          │
│   PDF/DOCX/PPTX/XLSX → 임베딩 → 검색    │
└──────────────────┬───────────────────────┘
                   ▼
┌──────────────────────────────────────────┐
│       LangGraph Multi-Agent System       │
│                                          │
│  ┌─────────┐ ┌─────────┐ ┌───────────┐  │
│  │VOC Agent│ │KPI Agent│ │Content    │  │
│  │(RAG)    │ │(CSV)    │ │Agent(RAG) │  │
│  └────┬────┘ └────┬────┘ └─────┬─────┘  │
│       └───────────┼────────────┘         │
│                   ▼                      │
│           ┌──────────────┐               │
│           │ Report Agent │               │
│           └──────────────┘               │
└──────────────────┬───────────────────────┘
                   ▼
┌──────────────────────────────────────────┐
│        Streamlit Dashboard               │
│  KPI 차트 | VOC 시각화 | 챗봇           │
└──────────────────────────────────────────┘
```

## 기술 스택

| 구분 | 기술 |
|------|------|
| LLM | Amazon Bedrock - Claude Sonnet 4.6 |
| Embeddings | Amazon Titan Embeddings v2 |
| 벡터 스토어 | Amazon S3 Vectors |
| 에이전트 프레임워크 | LangGraph |
| 대시보드 | Streamlit |
| 언어 | Python 3.11+ |

## 에이전트 구성

| 에이전트 | 데이터 소스 | 출력 |
|----------|-----------|------|
| VOC Agent | S3 Vectors (RAG) | 감정 분포, 이슈 TOP5, 키워드 (JSON) |
| KPI Agent | CSV 직접 로드 | 지표 하이라이트, 이상 징후, 위험 요소 (JSON) |
| Content Agent | S3 Vectors (RAG) | 업데이트 현황, 건강도, Gap 분석 (JSON) |
| Report Agent | 위 3개 결과 종합 | 스코어카드, 교차 인사이트, 액션 아이템 (JSON) |






## 설치

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## 사용법

### 1. 문서 인덱싱

`bedrock-sample/` 폴더에 데이터를 넣고:

```bash
python -m src.main ingest
```

### 2. CLI 분석

```bash
python -m src.main analyze "DK모바일 리본 게임의 주요 이슈 분석"
```

### 3. 대시보드

```bash
streamlit run dashboard/app.py
```

- **📊 KPI 대시보드**: DAU/매출/PU 트렌드 차트
- **📢 VOC 분석**: 감정 분포, 이슈 카드, 키워드
- **📝 콘텐츠 분석**: 건강도, Gap 테이블
- **📋 종합 리포트**: 스코어카드, 액션 아이템
- **💬 챗봇**: 분석 결과 기반 추가 질문 (하단 고정)

## 프로젝트 구조

```
NAIDP/
├── src/
│   ├── agents/          # LangGraph 에이전트
│   ├── rag/             # S3 Vectors RAG
│   └── utils/           # Bedrock 클라이언트, 설정
├── dashboard/app.py     # Streamlit 대시보드
├── bedrock-sample/      # 샘플 데이터
└── aidlc-docs/          # AI-DLC 문서
```
