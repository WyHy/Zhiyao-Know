#!/usr/bin/env python3
"""
单文件导入测试脚本（参考 batch_import_huizhou.py）

流程：
1. 登录
2. 确保测试知识库存在（不存在则创建）
3. 上传单个文件
4. 发起文档入库
5. 回查知识库文件列表，确认文件状态
"""

from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

import httpx

API_BASE_URL = os.getenv("YUXI_API_BASE_URL", "http://localhost:5050")
USERNAME = (
    os.getenv("YUXI_TEST_USERNAME")
    or os.getenv("YUXI_SUPER_ADMIN_NAME")
    or "admin"
)
PASSWORD = (
    os.getenv("YUXI_TEST_PASSWORD")
    or os.getenv("YUXI_SUPER_ADMIN_PASSWORD")
    or "sgcc@0716!Jz"
)
KB_NAME = os.getenv("YUXI_TEST_KB_NAME", "单文件导入测试库")
PRESET_TOKEN = os.getenv("YUXI_TEST_TOKEN")


class SingleFileImporter:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.token: str | None = None
        self.kb_id: str | None = None

    async def login(self) -> None:
        if PRESET_TOKEN:
            self.token = PRESET_TOKEN
            print("使用预设 token 登录")
            return
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{API_BASE_URL}/api/auth/token",
                data={"username": USERNAME, "password": PASSWORD},
            )
        if resp.status_code != 200:
            raise RuntimeError(f"登录失败: {resp.status_code} {resp.text}")
        self.token = resp.json()["access_token"]
        print(f"登录成功: user={USERNAME}")

    def _headers(self) -> dict[str, str]:
        assert self.token, "token not initialized"
        return {"Authorization": f"Bearer {self.token}"}

    async def ensure_kb(self) -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{API_BASE_URL}/api/knowledge/databases", headers=self._headers())
        if resp.status_code != 200:
            raise RuntimeError(f"查询知识库失败: {resp.status_code} {resp.text}")

        for db in resp.json().get("databases", []):
            if db.get("name") == KB_NAME:
                kb_id = db.get("db_id")
                print(f"复用已有知识库: {KB_NAME} ({kb_id})")
                return kb_id

        payload = {
            "database_name": KB_NAME,
            "description": "单文件导入测试自动创建",
            "embed_model_name": "siliconflow/BAAI/bge-m3",
            "kb_type": "milvus",
            "additional_params": {},
            "share_config": {"is_shared": True, "accessible_departments": []},
        }
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{API_BASE_URL}/api/knowledge/databases",
                headers=self._headers(),
                json=payload,
            )
        if resp.status_code != 200:
            raise RuntimeError(f"创建知识库失败: {resp.status_code} {resp.text}")
        kb_id = resp.json().get("db_id")
        print(f"创建知识库成功: {KB_NAME} ({kb_id})")
        return kb_id

    async def upload_file(self, kb_id: str) -> tuple[str, str] | None:
        filename = self.file_path.name
        async with httpx.AsyncClient(timeout=300) as client:
            with self.file_path.open("rb") as f:
                files = {"file": (filename, f)}
                resp = await client.post(
                    f"{API_BASE_URL}/api/knowledge/files/upload?db_id={kb_id}",
                    headers=self._headers(),
                    files=files,
                )
        if resp.status_code == 200:
            data = resp.json()
            minio_path = data.get("file_path") or data.get("minio_path")
            content_hash = data.get("content_hash")
            print(f"上传成功: {filename}")
            return minio_path, content_hash
        if resp.status_code == 409:
            print(f"文件已存在（跳过上传）: {filename}")
            return None
        raise RuntimeError(f"上传失败: {resp.status_code} {resp.text}")

    async def add_documents(self, kb_id: str, file_infos: list[tuple[str, str]]) -> str | None:
        if not file_infos:
            return None
        items = [x[0] for x in file_infos]
        content_hashes = {x[0]: x[1] for x in file_infos}
        payload = {"items": items, "params": {"auto_index": True, "content_hashes": content_hashes}}
        async with httpx.AsyncClient(timeout=600) as client:
            resp = await client.post(
                f"{API_BASE_URL}/api/knowledge/databases/{kb_id}/documents",
                headers=self._headers(),
                json=payload,
            )
        if resp.status_code != 200:
            raise RuntimeError(f"入库失败: {resp.status_code} {resp.text}")
        task_id = resp.json().get("task_id")
        print(f"入库任务已提交: task_id={task_id}")
        return task_id

    async def check_file_status(self, kb_id: str, filename: str) -> dict | None:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{API_BASE_URL}/api/knowledge/databases/{kb_id}",
                headers=self._headers(),
            )
        if resp.status_code != 200:
            raise RuntimeError(f"查询知识库详情失败: {resp.status_code} {resp.text}")
        files = (resp.json() or {}).get("files") or {}
        for _, info in files.items():
            if info.get("filename") == filename:
                return {
                    "filename": info.get("filename"),
                    "status": info.get("status"),
                    "file_id": info.get("file_id"),
                }
        return None

    async def run(self) -> None:
        if not self.file_path.exists() or not self.file_path.is_file():
            raise FileNotFoundError(f"测试文件不存在: {self.file_path}")

        print(f"开始单文件导入测试: {self.file_path}")
        await self.login()
        kb_id = await self.ensure_kb()
        self.kb_id = kb_id

        uploaded = await self.upload_file(kb_id)
        infos = [uploaded] if uploaded else []
        await self.add_documents(kb_id, infos)

        status = await self.check_file_status(kb_id, self.file_path.name)
        if status:
            print(f"回查状态: filename={status['filename']}, status={status['status']}, file_id={status['file_id']}")
        else:
            print("回查状态: 未找到该文件记录（可能仍在异步处理中）")

        print(f"测试完成: kb_id={kb_id}")


async def main() -> None:
    parser = argparse.ArgumentParser(description="单文件导入测试")
    parser.add_argument("--file", required=True, help="待导入文件绝对路径")
    args = parser.parse_args()
    await SingleFileImporter(args.file).run()


if __name__ == "__main__":
    asyncio.run(main())
