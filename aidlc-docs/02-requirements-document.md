# NAIDP 요구사항 문서

**프로젝트명**: NAIDP (게임 인사이트 분석 플랫폼)  
**작성일**: 2026-03-04  
**단계**: 🔵 INCEPTION PHASE

---

## 1. 프로젝트 개요

게임 기업의 VOC, KPI 데이터, 콘텐츠 기획서, 업데이트 내역을 종합 분석하여 인사이트 리포트를 자동 생성하는 AI 기반 멀티 에이전트 시스템.

### 핵심 가치
- 실시간 모니터링 및 주기적 인사이트 제공
- 다양한 데이터 소스 통합 분석
- AI 기반 자동화된 인사이트 도출
- 의사결정자를 위한 명확한 리포트

---

## 2. 기능 요구사항

### 2.1 데이터 수집 및 처리
- PDF 형식의 VOC 리포트 수집
- 콘텐츠 기획서 수집
- 업데이트/패치 노트 수집
- KPI 데이터 수집 (형식 미정)
- 일 단위 배치 처리

### 2.2 RAG 시스템
- S3 기반 문서 저장
- FAISS 벡터 인덱스
- 하이브리드 검색 (키워드 + 시맨틱)
- 문서 타입: 기획서, VOC 리포트, 패치 노트

### 2.3 멀티 에이전트 시스템
**계층적 구조 (Supervisor + Sub-agents)**

1. **Supervisor Agent**: 전체 워크플로우 조율
2. **VOC Analysis Agent**: 감정 분석, 트렌드, 주요 이슈 추출
3. **KPI Analysis Agent**: 지표 분석, 이상 탐지, 예측
4. **Content Planning Agent**: 기능 분석, 추천사항 도출
5. **Report Synthesis Agent**: 인사이트 통합, 최종 리포트 생성

### 2.4 출력 형식
- PDF 리포트
- 인터랙티브 웹 대시보드

---

## 3. 기술 스택

### 3.1 AI/ML
- **LLM**: Amazon Bedrock - Claude Sonnet 4.6
- **Embeddings**: Amazon Bedrock - Titan Embeddings
- **Framework**: LangGraph (멀티 에이전트 오케스트레이션)

### 3.2 데이터 저장 및 검색
- **문서 저장**: Amazon S3
- **벡터 스토어**: Amazon S3 Vectors (네이티브 벡터 저장/검색, 별도 벡터 DB 불필요)
- **메타데이터**: S3 Vectors 내장 메타데이터

### 3.3 개발 환경
- **언어**: Python 3.11+
- **주요 라이브러리**:
  - langgraph
  - langchain-aws
  - boto3 (AWS SDK, S3 Vectors 포함)
  - pypdf
  - streamlit (웹 대시보드)
  - reportlab (PDF 생성)

---

## 4. 시스템 아키텍처

```
┌─────────────────────────────────────────────────┐
│              Data Sources (S3)                  │
│  VOC Reports | 기획서 | 패치노트 | KPI Data    │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│           Document Processing                   │
│  PDF Parser → Chunking → Embedding              │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│         RAG System (FAISS + S3)                 │
│  Vector Index | Metadata | Hybrid Search        │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│         Supervisor Agent (LangGraph)            │
│              Task Routing                       │
└───┬─────────┬──────────┬──────────┬─────────────┘
    │         │          │          │
    ▼         ▼          ▼          ▼
┌───────┐ ┌──────┐ ┌─────────┐ ┌──────────┐
│  VOC  │ │ KPI  │ │ Content │ │  Report  │
│ Agent │ │Agent │ │  Agent  │ │ Synthesis│
└───┬───┘ └──┬───┘ └────┬────┘ └────┬─────┘
    │        │          │           │
    └────────┴──────────┴───────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│              Output Generation                  │
│         PDF Report | Web Dashboard              │
└─────────────────────────────────────────────────┘
```

---

## 5. MVP 범위 (오늘 중 완성)

### Phase 1: 기본 인프라 (1-2시간)
- [ ] 프로젝트 구조 생성
- [ ] AWS Bedrock 연결 설정
- [ ] S3 + FAISS RAG 기본 구현
- [ ] 샘플 문서 로딩

### Phase 2: 에이전트 구현 (2-3시간)
- [ ] LangGraph 기본 구조
- [ ] Supervisor Agent
- [ ] VOC Analysis Agent (단순 버전)
- [ ] Report Synthesis Agent (단순 버전)

### Phase 3: 출력 생성 (1-2시간)
- [ ] 텍스트 리포트 생성
- [ ] 간단한 Streamlit 대시보드

### Phase 4: 통합 테스트 (1시간)
- [ ] End-to-end 테스트
- [ ] 샘플 리포트 생성

---

## 6. 제약사항 및 가정

### 제약사항
- 로컬 개발 환경만 지원
- 보안/인증 미구현
- KPI 데이터 형식 미정 (추후 정의)
- 실시간 스트리밍 미지원

### 가정
- VOC 리포트는 PDF 형식
- 월 1-10GB 데이터 처리
- 단일 사용자 환경
- AWS 자격증명 설정 완료

---

## 7. 향후 확장 계획

- KPI Agent 고도화
- Content Planning Agent 고도화
- OpenSearch 마이그레이션 (확장성)
- 실시간 모니터링 기능
- 역할 기반 접근 제어
- 프로덕션 배포 (ECS/Lambda)
