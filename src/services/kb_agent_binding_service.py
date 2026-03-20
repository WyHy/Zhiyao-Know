from __future__ import annotations

from sqlalchemy import text

from src.storage.postgres.manager import pg_manager


class KBAgentBindingService:
    """知识库与智能体绑定服务"""

    def __init__(self):
        pg_manager.initialize()

    async def bind_agents(self, kb_id: str, agent_ids: list[str], replace: bool = False) -> int:
        async with pg_manager.get_async_session_context() as session:
            if replace:
                await session.execute(text("DELETE FROM kb_agent_bindings WHERE kb_id = :kb_id"), {"kb_id": kb_id})

            count = 0
            for agent_id in agent_ids:
                if not agent_id:
                    continue
                await session.execute(
                    text(
                        """
                        INSERT INTO kb_agent_bindings (kb_id, agent_id)
                        VALUES (:kb_id, :agent_id)
                        ON CONFLICT (kb_id, agent_id) DO NOTHING
                        """
                    ),
                    {"kb_id": kb_id, "agent_id": agent_id},
                )
                count += 1
            return count

    async def unbind_agent(self, kb_id: str, agent_id: str) -> None:
        async with pg_manager.get_async_session_context() as session:
            await session.execute(
                text("DELETE FROM kb_agent_bindings WHERE kb_id = :kb_id AND agent_id = :agent_id"),
                {"kb_id": kb_id, "agent_id": agent_id},
            )

    async def list_agents_for_kb(self, kb_id: str) -> list[str]:
        async with pg_manager.get_async_session_context() as session:
            result = await session.execute(
                text("SELECT agent_id FROM kb_agent_bindings WHERE kb_id = :kb_id ORDER BY agent_id"),
                {"kb_id": kb_id},
            )
            return [row[0] for row in result.fetchall()]

    async def list_agent_only_kb_names_for_agent(self, agent_id: str) -> list[str]:
        async with pg_manager.get_async_session_context() as session:
            result = await session.execute(
                text(
                    """
                    SELECT kb.name
                    FROM knowledge_bases kb
                    JOIN kb_agent_bindings bind ON bind.kb_id = kb.db_id
                    WHERE bind.agent_id = :agent_id AND kb.visibility = 'agent_only'
                    ORDER BY kb.name
                    """
                ),
                {"agent_id": agent_id},
            )
            return [row[0] for row in result.fetchall() if row[0]]

    async def is_agent_bound_to_kb(self, agent_id: str, kb_id: str) -> bool:
        async with pg_manager.get_async_session_context() as session:
            result = await session.execute(
                text(
                    """
                    SELECT 1
                    FROM kb_agent_bindings
                    WHERE kb_id = :kb_id AND agent_id = :agent_id
                    LIMIT 1
                    """
                ),
                {"kb_id": kb_id, "agent_id": agent_id},
            )
            return result.fetchone() is not None
