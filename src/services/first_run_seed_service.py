from __future__ import annotations

import csv
import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from src import config
from src.knowledge import knowledge_base
from src.knowledge.base import FileStatus
from src.knowledge.manager import KB_VISIBILITY_AGENT_ONLY
from src.repositories.knowledge_base_repository import KnowledgeBaseRepository
from src.services.kb_agent_binding_service import KBAgentBindingService
from src.storage.postgres.manager import pg_manager
from src.utils import logger


@dataclass
class SeedResult:
    kb_id: str
    kb_name: str
    agent_id: str
    imported: bool
    message: str
    dataset_path: str | None = None


class FirstRunSeedService:
    """首次初始化后自动种子数据服务（幂等）"""

    KB_NAME = "惠州营销部问答隐藏知识库"
    KB_DESC = "系统初始化自动导入，仅绑定 huizhou_power_qa 使用。"
    AGENT_ID = "HuizhouPowerQAAgent"
    DATASET_CSV = "hz_power_marketing_qa_dataset_20260320.csv"
    DATASET_JSONL = "hz_power_marketing_qa_dataset_20260320.jsonl"

    @classmethod
    async def seed_hidden_huizhou_kb(cls, operator_id: int | str, department_id: int | None) -> SeedResult:
        if not pg_manager._initialized:
            pg_manager.initialize()
        await knowledge_base.initialize()

        kb_id = await cls._ensure_hidden_kb(department_id=department_id)
        await KBAgentBindingService().bind_agents(kb_id=kb_id, agent_ids=[cls.AGENT_ID], replace=False)

        dataset_path = cls._resolve_dataset_csv_path()
        if dataset_path is None:
            msg = (
                f"未找到数据集文件（{cls.DATASET_CSV} / {cls.DATASET_JSONL}），"
                "已创建并绑定隐藏知识库，待你补充数据文件后可重新执行导入。"
            )
            logger.warning(msg)
            return SeedResult(
                kb_id=kb_id,
                kb_name=cls.KB_NAME,
                agent_id=cls.AGENT_ID,
                imported=False,
                message=msg,
                dataset_path=None,
            )

        imported, msg = await cls._ensure_dataset_indexed(
            kb_id=kb_id, dataset_path=dataset_path, operator_id=str(operator_id)
        )
        return SeedResult(
            kb_id=kb_id,
            kb_name=cls.KB_NAME,
            agent_id=cls.AGENT_ID,
            imported=imported,
            message=msg,
            dataset_path=str(dataset_path),
        )

    @classmethod
    async def _ensure_hidden_kb(cls, department_id: int | None) -> str:
        repo = KnowledgeBaseRepository()
        rows = await repo.get_all()
        for row in rows:
            if (row.name or "").strip() == cls.KB_NAME:
                return row.db_id

        embed_model_name = config.embed_model
        embed_info = config.embed_model_names.get(embed_model_name)
        if embed_info is None:
            # 理论上不会发生，做最小兜底
            first_key = next(iter(config.embed_model_names.keys()))
            embed_info = config.embed_model_names[first_key]

        share_config = {
            "is_shared": False,
            "accessible_departments": [department_id] if department_id else [],
        }

        created = await knowledge_base.create_database(
            database_name=cls.KB_NAME,
            description=cls.KB_DESC,
            kb_type="lightrag",
            embed_info=embed_info.model_dump() if hasattr(embed_info, "model_dump") else dict(embed_info),
            share_config=share_config,
            visibility=KB_VISIBILITY_AGENT_ONLY,
            auto_generate_questions=False,
        )
        return created["db_id"]

    @classmethod
    def _resolve_dataset_csv_path(cls) -> Path | None:
        save_dir = Path(config.save_dir)
        save_csv = save_dir / "qa_datasets" / cls.DATASET_CSV
        save_jsonl = save_dir / "qa_datasets" / cls.DATASET_JSONL

        repo_data_csv = Path.cwd() / "data" / "qa_datasets" / cls.DATASET_CSV
        repo_data_jsonl = Path.cwd() / "data" / "qa_datasets" / cls.DATASET_JSONL

        if save_csv.exists():
            return save_csv

        if repo_data_csv.exists():
            save_csv.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(repo_data_csv, save_csv)
            return save_csv

        if save_jsonl.exists():
            cls._jsonl_to_csv(save_jsonl, save_csv)
            return save_csv

        if repo_data_jsonl.exists():
            save_csv.parent.mkdir(parents=True, exist_ok=True)
            cls._jsonl_to_csv(repo_data_jsonl, save_csv)
            return save_csv

        return None

    @staticmethod
    def _jsonl_to_csv(jsonl_path: Path, csv_path: Path) -> None:
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with jsonl_path.open("r", encoding="utf-8") as fin, csv_path.open(
            "w", encoding="utf-8-sig", newline=""
        ) as fout:
            writer = csv.DictWriter(fout, fieldnames=["query", "gold_answer"])
            writer.writeheader()
            for line in fin:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                query = (obj.get("query") or "").strip()
                answer = (obj.get("gold_answer") or "").strip()
                if not query or not answer:
                    continue
                writer.writerow({"query": query, "gold_answer": answer})

    @classmethod
    async def _ensure_dataset_indexed(cls, kb_id: str, dataset_path: Path, operator_id: str) -> tuple[bool, str]:
        kb_instance = await knowledge_base._get_kb_for_database(kb_id)  # noqa: SLF001
        await kb_instance._load_metadata()  # noqa: SLF001

        db_info = await knowledge_base.get_database_info(kb_id)
        files = db_info.get("files") or {}

        target_file_id = None
        target_status = None
        target_filename = dataset_path.name
        for file_id, file_info in files.items():
            filename = file_info.get("filename", "")
            path = file_info.get("path", "")
            if filename == target_filename or str(path).endswith(target_filename):
                target_file_id = file_id
                target_status = file_info.get("status")
                break

        if target_file_id is None:
            file_meta = await knowledge_base.add_file_record(
                kb_id,
                str(dataset_path),
                params={"content_type": "file", "chunk_size": 1200, "chunk_overlap": 100},
                operator_id=operator_id,
            )
            target_file_id = file_meta["file_id"]
            target_status = file_meta.get("status")

        if target_status in {FileStatus.INDEXED, FileStatus.DONE}:
            return False, "数据集已存在且已入库，跳过重复导入。"

        if target_status in {FileStatus.UPLOADED, FileStatus.ERROR_PARSING, FileStatus.FAILED}:
            await knowledge_base.parse_file(kb_id, target_file_id, operator_id=operator_id)
            target_status = FileStatus.PARSED

        if target_status in {FileStatus.PARSED, FileStatus.ERROR_INDEXING, FileStatus.UPLOADED}:
            await knowledge_base.index_file(kb_id, target_file_id, operator_id=operator_id)

        return True, "隐藏知识库数据导入并入库完成。"
