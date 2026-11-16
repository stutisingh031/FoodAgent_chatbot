
import ast
import json
from time import perf_counter
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from langchain.agents import create_agent
from langchain_core.callbacks import BaseCallbackHandler
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from app.config import settings
from app.logger import logger
from app.agent.instructions import get_support_agent_instructions
from app.agent.tools.order_tools import ORDER_TOOLS
from app.agent.tools.faq_tools import FAQ_TOOLS
from app.agent.tools.support_tools import SUPPORT_TOOLS
from app.agent.tools.refund_policy_tool import REFUND_POLICY_TOOLS


ALL_SUPPORT_TOOLS = (
    ORDER_TOOLS
    + FAQ_TOOLS
    + SUPPORT_TOOLS
    + REFUND_POLICY_TOOLS
)


@dataclass
class SupportAgentResponse:
    reply: str
    handoff_required: bool = False
    ticket_id: int | None = None


class ToolLifecycleLogger(BaseCallbackHandler):
    """Log tool starts, completions, and failures without logging tool data."""

    def __init__(self, customer_id: int):
        self.customer_id = customer_id
        self._started_at: dict[UUID, tuple[float, str]] = {}

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        tool_name = serialized.get("name", "unknown")
        self._started_at[run_id] = (perf_counter(), tool_name)
        logger.info(
            "TOOL_START tool=%s customer_id=%s run_id=%s",
            tool_name,
            self.customer_id,
            run_id,
        )

    def on_tool_end(self, output: Any, *, run_id: UUID, **kwargs: Any) -> None:
        elapsed_ms, tool_name = self._elapsed_ms(run_id)
        result = _tool_result_data(output)
        success = result.get("success")
        if success is None:
            success = "error" not in result
        logger.info(
            "TOOL_END tool=%s run_id=%s success=%s duration_ms=%s",
            tool_name,
            run_id,
            success if success is not None else "unknown",
            elapsed_ms,
        )

    def on_tool_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> None:
        elapsed_ms, tool_name = self._elapsed_ms(run_id)
        logger.error(
            "TOOL_ERROR tool=%s run_id=%s duration_ms=%s error_type=%s",
            tool_name,
            run_id,
            elapsed_ms,
            type(error).__name__,
        )

    def _elapsed_ms(self, run_id: UUID) -> tuple[int, str]:
        started = self._started_at.pop(run_id, None)
        if not started:
            return 0, "unknown"
        started_at, tool_name = started
        return round((perf_counter() - started_at) * 1000), tool_name


def _tool_result_data(content) -> dict:
    """Decode structured results returned by LangChain support tools."""

    if isinstance(content, dict):
        return content

    if isinstance(content, list):
        content = "\n".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict)
        )

    if isinstance(content, str):
        try:
            value = json.loads(content)
        except (TypeError, ValueError):
            try:
                value = ast.literal_eval(content)
            except (SyntaxError, ValueError):
                return {}
        return value if isinstance(value, dict) else {}

    return {}


def build_support_agent(customer_id: int):
    """Build the support agent for a customer request."""

    if customer_id <= 0:
        raise ValueError("customer_id must be positive.")

    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    model = ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0,
    )

    instructions = get_support_agent_instructions()
    instructions += (
        "\n\nTrusted application context: the authenticated customer ID "
        f"for this request is {customer_id}. Use this customer ID for "
        "customer-specific operations. Never access another customer's data."
    )

    agent = create_agent(
        model=model,
        tools=ALL_SUPPORT_TOOLS,
        system_prompt=instructions,
    )

    logger.info("Support agent initialized for customer_id=%s", customer_id)
    return agent


def chat_with_support_agent(
    message: str,
    customer_id: int,
    history: list[dict[str, str]] | None = None,
) -> SupportAgentResponse:
    """Run the agent with the current message and optional conversation history."""

    if not message or not message.strip():
        raise ValueError("Message cannot be empty.")

    if customer_id <= 0:
        raise ValueError("customer_id must be positive.")

    logger.info("Processing support message for customer_id=%s", customer_id)

    agent = build_support_agent(customer_id)

    messages = []

    # Convert stored history into LangChain's structured message format.
    for item in history or []:
        role = item.get("role")
        content = item.get("message", "")

        if not content.strip():
            continue

        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))

    # Append the current message exactly once.
    messages.append(HumanMessage(content=message.strip()))

    try:
        result = agent.invoke(
            {"messages": messages},
            config={"callbacks": [ToolLifecycleLogger(customer_id)]},
        )
        agent_messages = result.get("messages", [])
        handoff_required = False
        ticket_id = None

        for response in agent_messages:
            if isinstance(response, ToolMessage):
                tool_name = response.name or "unknown"
                tool_result = _tool_result_data(response.content)
                if (
                    tool_name in {"request_human_handoff", "create_support_ticket"}
                    and tool_result.get("success") is True
                ):
                    handoff_required = True
                    ticket_id = tool_result.get("ticket_id")

        for response in reversed(agent_messages):
            if isinstance(response, AIMessage):
                content = response.content

                if isinstance(content, str) and content.strip():
                    logger.info(
                        "Support response generated for customer_id=%s",
                        customer_id,
                    )
                    return SupportAgentResponse(
                        reply=content,
                        handoff_required=handoff_required,
                        ticket_id=ticket_id,
                    )

                if isinstance(content, list):
                    text_parts = [
                        block["text"]
                        for block in content
                        if isinstance(block, dict)
                        and isinstance(block.get("text"), str)
                    ]

                    if text_parts:
                        return SupportAgentResponse(
                            reply="\n".join(text_parts),
                            handoff_required=handoff_required,
                            ticket_id=ticket_id,
                        )

        logger.warning(
            "Agent returned no usable response for customer_id=%s",
            customer_id,
        )
        return SupportAgentResponse(
            reply="I'm sorry, I couldn't generate a response. Please try again."
        )

    except Exception:
        logger.exception(
            "Support agent failed for customer_id=%s",
            customer_id,
        )
        raise
