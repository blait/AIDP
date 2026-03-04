# NAIDP 구축 가이드

초기 상태에서 NAIDP를 구축하고 실행하기 위한 단계별 가이드입니다.

---

## 사전 요구사항

- Python 3.11+
- AWS CLI 설정 완료 (`aws configure`)
- AWS 계정에 다음 서비스 접근 권한:
  - Amazon Bedrock (Claude Sonnet 4.6, Titan Embeddings v2)
  - Amazon S3 / S3 Vectors
  - Amazon Athena

---

## Step 1: 프로젝트 클론 및 환경 설정

```bash
git clone https://github.com/blait/AIDP.git
cd AIDP

# 가상환경 생성 및 활성화
python3 -m venv .venv
source .venv/bin/activate

# 패키지 설치
pip install -r requirements.txt

# 추가 문서 형식 지원 패키지
pip install python-pptx python-docx openpyxl

# 환경 변수 설정
cp .env.example .env
```

`.env` 파일을 열어 필요 시 값을 수정합니다:

```
AWS_REGION=ap-northeast-2
BEDROCK_REGION=us-east-1
S3_BUCKET_NAME=naidp-documents
S3_VECTORS_BUCKET_NAME=naidp-vectors
S3_VECTORS_INDEX_NAME=naidp-index
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-6
BEDROCK_EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0
ATHENA_DATABASE=naidp
ATHENA_OUTPUT_LOCATION=s3://<your-bucket>/athena-results/
```

---

## Step 2: AWS 자격증명 확인

```bash
aws sts get-caller-identity
```

Bedrock 모델 접근 가능 여부 확인:

```bash
aws bedrock list-foundation-models --region us-east-1 \
  --query "modelSummaries[?contains(modelId,'claude-sonnet-4-6')]" \
  --output table
```

---

## Step 3: S3 Vectors 설정 (RAG)

### 3.1 벡터 버킷 및 인덱스 생성

```bash
python3 -c "
from src.rag.vector_store import setup_vector_store
setup_vector_store()
"
```

이 명령은 다음을 생성합니다:
- S3 Vectors 버킷: `naidp-vectors`
- 벡터 인덱스: `naidp-index` (float32, 1024 dim, cosine)

### 3.2 문서 인덱싱

`bedrock-sample/` 폴더에 분석할 문서를 배치합니다:

```
bedrock-sample/
├── 1.콘텐츠기획서/    # PPTX 파일
├── 2.업데이트내역/    # XLSX 파일
├── 3.KPI/            # CSV 파일
└── 4.VOC보고서/      # PDF/DOCX/TXT 파일
    ├── 상세본/
    └── 요약본/
```

인덱싱 실행:

```bash
python3 -m src.main ingest
```

출력 예시:
```
Loading: 260218_kpi.csv → 60 chunks
Loading: 성검.pptx → 2 chunks
Loading: _DK모바일_리본 커뮤니티 주간 동향.pdf → 11 chunks
...
총 148개 청크 로드 완료
Uploaded 148 vectors
```

---

## Step 4: Athena 설정 (Text-to-SQL)

### 4.1 S3 데이터 버킷 생성 및 CSV 업로드

```bash
# 버킷 생성 (이름은 고유해야 함)
aws s3 mb s3://<your-data-bucket> --region ap-northeast-2

# KPI CSV 업로드
aws s3 cp bedrock-sample/3.KPI/260218_kpi.csv s3://<your-data-bucket>/kpi/

# 거래 데이터 CSV 업로드 (있는 경우)
aws s3 cp "your-transaction-data.csv" s3://<your-data-bucket>/transaction/
```

### 4.2 Athena 데이터베이스 생성

AWS CLI 또는 Athena 콘솔에서:

```sql
CREATE DATABASE IF NOT EXISTS naidp;
```

CLI로 실행:

```bash
aws athena start-query-execution \
  --query-string "CREATE DATABASE IF NOT EXISTS naidp" \
  --result-configuration OutputLocation=s3://<your-data-bucket>/athena-results/ \
  --region ap-northeast-2
```

### 4.3 KPI 테이블 생성

```sql
CREATE EXTERNAL TABLE IF NOT EXISTS naidp.kpi (
  log_date string,
  dau bigint,
  nu bigint,
  pu bigint,
  npu bigint,
  pur double,
  daily_sales double,
  daily_arppu double,
  daily_arpdau double
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 's3://<your-data-bucket>/kpi/'
TBLPROPERTIES ('skip.header.line.count'='1');
```

### 4.4 Transaction 테이블 생성 (선택)

```sql
CREATE EXTERNAL TABLE IF NOT EXISTS naidp.transaction_map (
  sell_account string,
  buy_account string,
  sell_currency string,
  market_type string,
  cnt bigint,
  total_price bigint,
  first_date string,
  last_date string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES ('separatorChar'=',', 'quoteChar'='"')
STORED AS TEXTFILE
LOCATION 's3://<your-data-bucket>/transaction/'
TBLPROPERTIES ('skip.header.line.count'='1');
```

### 4.5 테이블 확인

```bash
aws athena start-query-execution \
  --query-string "SELECT * FROM naidp.kpi LIMIT 3" \
  --query-execution-context Database=naidp \
  --result-configuration OutputLocation=s3://<your-data-bucket>/athena-results/ \
  --region ap-northeast-2
```

---

## Step 5: 동작 확인

### 5.1 Bedrock 연결 테스트

```bash
python3 -c "
from src.utils.bedrock_client import invoke_llm
print(invoke_llm([{'role': 'user', 'content': '안녕'}]))
"
```

### 5.2 RAG 검색 테스트

```bash
python3 -c "
from src.rag.retriever import retrieve
docs = retrieve('VOC 고객 불만', top_k=2)
for d in docs:
    print(f'[{d[\"source\"]}] {d[\"text\"][:80]}...')
"
```

### 5.3 Athena 스키마 조회 테스트

```bash
python3 -c "
from src.utils.athena_client import get_table_schema
print(get_table_schema())
"
```

### 5.4 CLI 분석 실행

```bash
python3 -m src.main analyze "게임의 주요 VOC 이슈와 KPI 현황을 종합 분석해줘"
```

리포트가 `outputs/reports/report.md`에 저장됩니다.

---

## Step 6: 대시보드 실행

```bash
streamlit run dashboard/app.py
```

브라우저에서 `http://localhost:8501` 접속.

### 대시보드 탭 구성

| 탭 | 기능 | 데이터 소스 |
|----|------|-----------|
| 📊 KPI 대시보드 | DAU/매출/PU 차트, metric 카드 | CSV (pandas) |
| 📢 VOC 분석 | 감정 분포, 이슈 카드, 키워드 | AI 분석 결과 (JSON) |
| 📝 콘텐츠 분석 | 건강도, 업데이트 현황, Gap 테이블 | AI 분석 결과 (JSON) |
| 📋 종합 리포트 | 스코어카드, 액션 아이템, 리스크 | AI 분석 결과 (JSON) |
| 🔍 Athena 분석 | 자연어 → SQL → 결과 + 차트 | Athena |
| 💬 챗봇 (하단) | 추가 질문 응답 | 분석 결과 + RAG |

### 사용 순서

1. **사이드바** → `분석 시작` 클릭 (VOC/KPI/Content/Report 에이전트 순차 실행)
2. **각 탭** → 분석 결과 시각화 확인
3. **Athena 탭** → 자연어로 추가 쿼리
4. **하단 챗봇** → 분석 결과 기반 추가 질문

---

## 트러블슈팅

### Bedrock 타임아웃

Report Agent에서 타임아웃 발생 시, `src/utils/bedrock_client.py`의 `read_timeout` 값을 조정:

```python
Config(read_timeout=300)  # 기본 300초
```

### Athena 쿼리 결과 0행

- 날짜 필터가 데이터 범위를 벗어나는 경우 발생
- `athena_agent.py`의 프롬프트에 데이터 범위 힌트가 포함되어 있음
- 새 데이터 추가 시 프롬프트의 날짜 범위 업데이트 필요

### S3 Vectors 인덱스 생성 실패

`distanceMetric` 파라미터가 필요합니다. `vector_store.py`에 `distanceMetric="cosine"` 포함되어 있는지 확인.

---

## 데이터 추가/갱신

### 새 문서 추가 (RAG)

1. `bedrock-sample/` 하위에 파일 배치
2. `python3 -m src.main ingest` 재실행
3. 기존 인덱스에 추가됨 (중복 방지는 UUID 기반)

### 새 CSV 추가 (Athena)

1. S3에 업로드: `aws s3 cp new_data.csv s3://<bucket>/kpi/`
2. 기존 테이블에 자동 반영 (External Table이므로 S3 파일 추가만으로 충분)
3. 스키마가 다르면 새 테이블 생성 필요
