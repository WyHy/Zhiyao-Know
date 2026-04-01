#!/usr/bin/env python3
"""
查询知识库文件任务状态（宿主机执行）

输出：
- 处理中数量
- 等待处理数量
- 失败数量
- 已完成数量
- 总文件数量
- 各状态分布明细

用法示例：
  python3 scripts/check_kb_file_task_status.py
  python3 scripts/check_kb_file_task_status.py --compose-file docker-compose.l20.qwen35.vllm.yml
  python3 scripts/check_kb_file_task_status.py --db-id kb_xxx
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def run_psql_query(compose_file: str, sql: str, user: str, db_name: str) -> str:
    cmd = [
        "docker",
        "compose",
        "-f",
        compose_file,
        "exec",
        "-T",
        "postgres",
        "psql",
        "-U",
        user,
        "-d",
        db_name,
        "-t",
        "-A",
        "-F",
        "|",
        "-c",
        sql,
    ]
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(
            f"psql 查询失败 (exit={proc.returncode})\n"
            f"cmd: {' '.join(cmd)}\n"
            f"stdout: {proc.stdout}\n"
            f"stderr: {proc.stderr}"
        )
    return (proc.stdout or "").strip()


def normalize_status(raw: str) -> str:
    return (raw or "unknown").strip().lower()


def main() -> int:
    parser = argparse.ArgumentParser(description="查询知识库文件任务状态统计")
    parser.add_argument(
        "--compose-file",
        default="docker-compose.yaml",
        help="docker compose 配置文件路径（默认: docker-compose.yaml）",
    )
    parser.add_argument(
        "--db-id",
        default="",
        help="可选：只查询指定知识库 db_id",
    )
    args = parser.parse_args()

    db_id = args.db_id.strip()
    if db_id and not re.match(r"^[A-Za-z0-9_-]+$", db_id):
        print(f"非法 db_id: {db_id}")
        return 2

    pg_user = os.getenv("POSTGRES_USER", "postgres")
    pg_db = os.getenv("POSTGRES_DB", "yuxi_know")

    where_clause = "WHERE COALESCE(is_folder, false) = false"
    if db_id:
        where_clause += f" AND db_id = '{db_id}'"

    sql = f"""
SELECT COALESCE(status, 'unknown') AS status, COUNT(*) AS cnt
FROM knowledge_files
{where_clause}
GROUP BY COALESCE(status, 'unknown')
ORDER BY cnt DESC, status ASC;
""".strip()

    try:
        out = run_psql_query(args.compose_file, sql, pg_user, pg_db)
    except Exception as exc:  # noqa: BLE001
        print(f"执行失败: {exc}")
        return 1

    status_counts: dict[str, int] = defaultdict(int)
    if out:
        for line in out.splitlines():
            if not line.strip():
                continue
            parts = line.split("|")
            if len(parts) != 2:
                continue
            status = normalize_status(parts[0])
            try:
                cnt = int(parts[1])
            except ValueError:
                continue
            status_counts[status] += cnt

    processing_statuses = {"processing", "parsing", "indexing"}
    waiting_statuses = {"uploaded", "waiting", "parsed"}
    failed_statuses = {"failed", "error_parsing", "error_indexing"}
    completed_statuses = {"indexed", "done"}

    processing = sum(status_counts[s] for s in processing_statuses)
    waiting = sum(status_counts[s] for s in waiting_statuses)
    failed = sum(status_counts[s] for s in failed_statuses)
    completed = sum(status_counts[s] for s in completed_statuses)
    total = sum(status_counts.values())
    other = total - processing - waiting - failed - completed

    scope = f"db_id={db_id}" if db_id else "全库"
    print("\n" + "=" * 64)
    print(f"知识库文件任务状态统计 ({scope})")
    print("=" * 64)
    print(f"处理中   : {processing}")
    print(f"等待处理 : {waiting}")
    print(f"失败     : {failed}")
    print(f"已完成   : {completed}")
    print(f"其他状态 : {other}")
    print(f"总数     : {total}")

    print("\n状态明细:")
    if not status_counts:
        print("  (无数据)")
    else:
        for status, cnt in sorted(status_counts.items(), key=lambda x: (-x[1], x[0])):
            print(f"  - {status:16s} {cnt}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

