import time
import boto3
import pandas as pd
from src.utils.config import AWS_REGION, ATHENA_DATABASE, ATHENA_OUTPUT_LOCATION


def get_athena_client():
    return boto3.client("athena", region_name=AWS_REGION)


def get_table_schema() -> str:
    client = get_athena_client()
    query = f"""
    SELECT table_name, column_name, data_type
    FROM information_schema.columns
    WHERE table_schema = '{ATHENA_DATABASE}'
    ORDER BY table_name, ordinal_position
    """
    df = execute_query(query)
    if df is None or df.empty:
        return "스키마 정보를 가져올 수 없습니다."

    lines = []
    current_table = ""
    for _, row in df.iterrows():
        if row["table_name"] != current_table:
            current_table = row["table_name"]
            lines.append(f"\n테이블: {ATHENA_DATABASE}.{current_table}")
        lines.append(f"  - {row['column_name']} ({row['data_type']})")
    return "\n".join(lines)


def execute_query(sql: str, timeout: int = 60) -> pd.DataFrame | None:
    client = get_athena_client()
    response = client.start_query_execution(
        QueryString=sql,
        QueryExecutionContext={"Database": ATHENA_DATABASE},
        ResultConfiguration={"OutputLocation": ATHENA_OUTPUT_LOCATION},
    )
    query_id = response["QueryExecutionId"]

    for _ in range(timeout):
        status = client.get_query_execution(QueryExecutionId=query_id)
        state = status["QueryExecution"]["Status"]["State"]
        if state == "SUCCEEDED":
            break
        if state in ("FAILED", "CANCELLED"):
            reason = status["QueryExecution"]["Status"].get("StateChangeReason", "")
            raise Exception(f"Athena 쿼리 실패: {reason}")
        time.sleep(1)
    else:
        raise Exception("Athena 쿼리 타임아웃")

    results = client.get_query_results(QueryExecutionId=query_id)
    rows = results["ResultSet"]["Rows"]
    if len(rows) <= 1:
        return pd.DataFrame()

    headers = [col["VarCharValue"] for col in rows[0]["Data"]]
    data = []
    for row in rows[1:]:
        data.append([col.get("VarCharValue", "") for col in row["Data"]])
    return pd.DataFrame(data, columns=headers)


def validate_query(sql: str) -> tuple[bool, str]:
    try:
        execute_query(f"EXPLAIN {sql}")
        return True, "SQL이 유효합니다."
    except Exception as e:
        return False, str(e)
