
from langchain_core.tools import tool

from app.logger import logger


# Starter FAQ data for development.
# These are general support instructions, not official refund policies.
FAQS = [
    {
        "question": "What should I do if my order is delayed?",
        "keywords": ["late delivery", "delayed", "delay", "taking too long"],
        "answer": (
            "You can check your order's latest status. If it is still delayed, "
            "I can help create a support ticket for further assistance."
        ),
        "category": "late_delivery",
    },
    {
        "question": "What should I do if an item is missing?",
        "keywords": ["missing item", "missing food", "item missing", "not received"],
        "answer": (
            "Please check your order details and identify the missing item. "
            "I can help create a support ticket for the issue."
        ),
        "category": "missing_item",
    },
    {
        "question": "What should I do if I received the wrong item?",
        "keywords": ["wrong item", "incorrect item", "wrong food", "incorrect order"],
        "answer": (
            "Please identify the item you received and the item you expected. "
            "I can help create a support ticket for further assistance."
        ),
        "category": "wrong_item",
    },
    {
        "question": "How can I get help with an order?",
        "keywords": ["contact support", "human support", "help", "speak to agent"],
        "answer": (
            "I can check your order, help identify the issue, or create a "
            "support ticket for follow-up by a human support representative."
        ),
        "category": "general_support",
    },
]


@tool
def search_support_faq(query: str) -> dict:
    """Search common food-delivery support FAQs.

    Use this tool for general questions about delayed deliveries, missing
    items, incorrect items, and contacting support. This starter FAQ does
    not define refund eligibility or authorize refunds.
    """
    query = query.strip()

    if not query:
        return {"error": "Please provide a question to search."}

    logger.info("FAQ search requested")

    try:
        query_words = set(query.lower().replace("?", "").split())
        matches = []

        for faq in FAQS:
            searchable_text = " ".join(
                [faq["question"], faq["answer"], faq["category"]]
                + faq["keywords"]
            ).lower()

            score = sum(
                1 for word in query_words
                if len(word) > 2 and word in searchable_text
            )

            if score > 0:
                matches.append((score, faq))

        matches.sort(key=lambda item: item[0], reverse=True)

        results = [
            {
                "question": faq["question"],
                "answer": faq["answer"],
                "category": faq["category"],
            }
            for _, faq in matches[:3]
        ]

        logger.info("FAQ search completed: result_count=%s", len(results))

        if not results:
            return {
                "results": [],
                "message": (
                    "No matching FAQ found. Consider checking the order "
                    "or creating a support ticket."
                ),
            }

        return {"results": results}

    except Exception:
        logger.exception("FAQ search failed")
        return {"error": "Unable to search FAQs right now."}


@tool
def get_issue_categories() -> dict:
    """List supported customer support issue categories.

    Use this tool when identifying or categorizing a customer's problem.
    """
    return {
        "categories": [
            {
                "id": "late_delivery",
                "description": "Order is delayed or taking too long.",
            },
            {
                "id": "missing_item",
                "description": "One or more ordered items are missing.",
            },
            {
                "id": "wrong_item",
                "description": "Customer received an incorrect item.",
            },
            {
                "id": "order_status",
                "description": "Customer needs an order status update.",
            },
            {
                "id": "quality_issue",
                "description": "Food quality or packaging concern.",
            },
            {
                "id": "cancellation",
                "description": "Customer wants help with order cancellation.",
            },
            {
                "id": "refund_query",
                "description": "Customer has a question about a refund.",
            },
            {
                "id": "general_support",
                "description": "Other support requests.",
            },
        ]
    }


FAQ_TOOLS = [
    search_support_faq,
    get_issue_categories,
]
