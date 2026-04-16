#!/usr/bin/env python3
"""
生成可信检索日报（Grounded + Route + Alerts）。

用法:
  python3 scripts/report_trust_metrics.py
  python3 scripts/report_trust_metrics.py --days 1
  python3 scripts/report_trust_metrics.py --output /tmp/trust_report.md
"""

import argparse
import asyncio
import os
from datetime import datetime

import httpx

API_BASE_URL = os.getenv("YUXI_API_BASE_URL", "http://localhost:5050")
USERNAME = os.getenv("YUXI_TEST_USERNAME") or os.getenv("YUXI_SUPER_ADMIN_NAME") or "admin"
PASSWORD = os.getenv("YUXI_TEST_PASSWORD") or os.getenv("YUXI_SUPER_ADMIN_PASSWORD") or "Admin@123456"
HTTP_TIMEOUT = float(os.getenv("YUXI_HTTP_TIMEOUT", "60"))


async def get_token(client: httpx.AsyncClient, base_url: str, username: str, password: str) -> str:
    resp = await client.post(
        f"{base_url}/api/auth/token",
        data={"username": username, "password": password},
    )
    resp.raise_for_status()
    token = (resp.json() or {}).get("access_token")
    if not token:
        raise RuntimeError("登录成功但未返回 access_token")
    return token


async def fetch_json(client: httpx.AsyncClient, url: str, token: str) -> dict:
    resp = await client.get(url, headers={"Authorization": f"Bearer {token}"})
    resp.raise_for_status()
    data = resp.json()
    return data if isinstance(data, dict) else {}


def _pct(value: float | int | None) -> str:
    if not isinstance(value, (int, float)):
        return "0.00%"
    return f"{float(value) * 100:.2f}%"


def build_markdown(days: int, grounded: dict, route: dict, alerts: dict, api_base_url: str) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    alert_items = alerts.get("alerts") or []
    top_kbs = route.get("top_hit_kbs") or []
    top_kbs_text = " / ".join([f"{item.get('name')}({item.get('count')})" for item in top_kbs[:5]]) or "-"

    lines = [
        "# 可信检索日报",
        "",
        f"- 生成时间: {now}",
        f"- API: {api_base_url}",
        f"- 统计窗口: 最近 {days} 天",
        "",
        "## Grounded 质量",
        f"- assistant_messages: {grounded.get('assistant_messages', 0)}",
        f"- grounded_marked_messages: {grounded.get('grounded_marked_messages', 0)}",
        f"- low_grounded_messages: {grounded.get('low_grounded_messages', 0)}",
        f"- low_grounded_rate: {_pct(grounded.get('low_grounded_rate'))}",
        f"- avg_support_ratio: {_pct(grounded.get('avg_support_ratio'))}",
        f"- grounded_retry_events: {grounded.get('grounded_retry_events', 0)}",
        "",
        "## Route 质量",
        f"- total_route_events: {route.get('total_route_events', 0)}",
        f"- ok_events: {route.get('ok_events', 0)}",
        f"- insufficient_events: {route.get('insufficient_events', 0)}",
        f"- avg_candidate_count: {route.get('avg_candidate_count', 0)}",
        f"- budget_truncated_events: {route.get('budget_truncated_events', 0)}",
        f"- budget_truncated_rate: {_pct(route.get('budget_truncated_rate'))}",
        f"- avg_budget_utilization: {_pct(route.get('avg_budget_utilization'))}",
        f"- avg_estimated_tokens: {route.get('avg_estimated_tokens', 0)}",
        f"- top_hit_kbs: {top_kbs_text}",
        "",
        "## 告警",
    ]

    if not alert_items:
        lines.append("- 当前无告警")
    else:
        for item in alert_items:
            lines.append(
                f"- [{item.get('level', 'info')}] {item.get('code', '-')}: "
                f"{item.get('message', '-')} (value={item.get('value')}, threshold={item.get('threshold')})"
            )

    lines.append("")
    return "\n".join(lines)


async def run(days: int, api_base_url: str, output: str | None, username: str, password: str) -> int:
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, trust_env=False) as client:
        token = await get_token(client, api_base_url, username, password)
        grounded, route, alerts = await asyncio.gather(
            fetch_json(client, f"{api_base_url}/api/dashboard/stats/grounded-quality?days={days}", token),
            fetch_json(client, f"{api_base_url}/api/dashboard/stats/route-quality?days={days}", token),
            fetch_json(client, f"{api_base_url}/api/dashboard/stats/trust-alerts?days={days}", token),
        )

    markdown = build_markdown(days, grounded, route, alerts, api_base_url)
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(markdown)
        print(f"✅ 报告已写入: {output}")
    else:
        print(markdown)
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成可信检索日报")
    parser.add_argument("--days", type=int, default=1, help="统计天数，默认1")
    parser.add_argument("--api-base-url", default=API_BASE_URL, help="API 地址，默认读取 YUXI_API_BASE_URL")
    parser.add_argument("--output", default=None, help="输出 Markdown 文件路径")
    parser.add_argument("--username", default=USERNAME, help="登录账号")
    parser.add_argument("--password", default=PASSWORD, help="登录密码")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    days = max(1, min(90, int(args.days)))
    try:
        return asyncio.run(run(days, args.api_base_url, args.output, args.username, args.password))
    except Exception as e:
        print(f"❌ 生成失败: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
