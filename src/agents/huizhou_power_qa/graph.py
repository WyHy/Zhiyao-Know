from langchain.agents import create_agent
from langchain.agents.middleware import ModelRetryMiddleware

from src.agents.common import BaseAgent, load_chat_model
from src.agents.common.middlewares import RuntimeConfigMiddleware, inject_attachment_context
from src.services.mcp_service import get_tools_from_all_servers


class HuizhouPowerQAAgent(BaseAgent):
    name = "惠州电力整改问答助手"
    description = "基于惠州电力整改方案 QA 知识库进行问答的专用智能体。"
    capabilities = ["file_upload"]

    async def get_graph(self, **kwargs):
        context = self.context_schema()
        all_mcp_tools = await get_tools_from_all_servers()

        graph = create_agent(
            model=load_chat_model(context.model),
            system_prompt=context.system_prompt,
            middleware=[
                inject_attachment_context,
                RuntimeConfigMiddleware(extra_tools=all_mcp_tools),
                ModelRetryMiddleware(),
            ],
            checkpointer=await self._get_checkpointer(),
        )

        return graph

