
from langchain_core.tools import tool

from app.logger import logger


@tool
def search_refund_policy(query: str) -> dict:
    """Search the company's official refund policy.

    Use this tool when a customer asks about refund eligibility, refund
    timelines, cancellations, or refund conditions.

    IMPORTANT: This is currently a placeholder. The refund-policy document
    retrieval system has not been implemented. Never infer or invent
    company-specific refund rules from general knowledge.
    """
    query = query.strip()

    if not query:
        logger.warning("Refund policy search called with an empty query")
        return {
            "found": False,
            "message": "Please provide a refund-policy question.",
        }

    logger.info("Refund policy search requested; document retrieval is not implemented")

    return {
        "found": False,
        "implemented": False,
        "query": query,
        "message": (
            "The official refund policy cannot currently be searched. "
            "Do not assume refund eligibility or promise a refund. "
            "Offer to create a support ticket or request human review."
        ),
    }


REFUND_POLICY_TOOLS = [search_refund_policy]
