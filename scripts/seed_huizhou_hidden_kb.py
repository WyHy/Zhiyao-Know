import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.first_run_seed_service import FirstRunSeedService


async def main():
    # 手动执行时默认用系统管理员ID=1、默认部门ID=1
    result = await FirstRunSeedService.seed_hidden_huizhou_kb(operator_id=1, department_id=1)
    print(
        {
            "kb_id": result.kb_id,
            "kb_name": result.kb_name,
            "agent_id": result.agent_id,
            "imported": result.imported,
            "dataset_path": result.dataset_path,
            "message": result.message,
        }
    )


if __name__ == "__main__":
    asyncio.run(main())
