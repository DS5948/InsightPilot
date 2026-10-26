
import os

from dotenv import load_dotenv
from groq import Groq

from rag import retrieve_documents

load_dotenv()

MODEL_NAME = "openai/gpt-oss-120b"

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY is missing from .env")

client = Groq(api_key=api_key)


def build_search_queries(question: str) -> list[str]:
    """Create focused search queries based on the user's question."""

    question_lower = question.lower()

    # Always start with the user's original question.
    queries = [question]

    # Expand searches for sales and revenue questions.
    sales_keywords = [
        "sales", "revenue", "profit", "decline",
        "decrease", "drop", "fall", "performance",
    ]

    if any(word in question_lower for word in sales_keywords):
        queries.append(
            "monthly sales revenue trends and product performance"
        )

    # Search for pricing pressure when relevant.
    pricing_keywords = [
        "why", "reason", "cause", "explanation",
        "decline", "decrease", "drop", "fall", "pricing",
        "price", "competitor",
    ]

    if any(word in question_lower for word in pricing_keywords):
        queries.append(
            "competitor pricing, customer price comparisons, "
            "and market competition"
        )

    # Search operational reports when looking for explanations.
    operations_keywords = [
        "why", "reason", "cause", "explanation",
        "delay", "delivery", "inventory", "operations",
        "decline", "decrease", "drop", "fall",
    ]

    if any(word in question_lower for word in operations_keywords):
        queries.append(
            "inventory replenishment problems, delivery delays, "
            "and operational issues affecting sales"
        )

    # Search customer feedback when it may explain a trend.
    feedback_keywords = [
        "customer", "feedback", "satisfaction",
        "reason", "cause", "explanation", "why",
    ]

    if any(word in question_lower for word in feedback_keywords):
        queries.append(
            "customer feedback, buying decisions, "
            "and issues reported by customers"
        )

    # Remove duplicate query strings while preserving their order.
    return list(dict.fromkeys(queries))


def retrieve_relevant_evidence(question: str) -> list[dict]:
    """Retrieve and combine relevant chunks from multiple searches."""

    search_queries = build_search_queries(question)

    all_results = []
    seen_chunks = set()

    for query in search_queries:
        results = retrieve_documents(query, top_k=3)

        for result in results:
            # Identify each chunk by its source file and chunk index.
            key = (
                result["source"],
                result["chunk_index"],
            )

            if key not in seen_chunks:
                seen_chunks.add(key)
                all_results.append(result)

    return all_results


def ask_documents(question: str) -> str:
    """Answer a question using evidence from business reports."""

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    retrieved = retrieve_relevant_evidence(question)

    if not retrieved:
        return "No relevant documents are available."

    context_parts = []

    for index, result in enumerate(retrieved, start=1):
        context_parts.append(
            f"Passage {index}\n"
            f"Source: {result['source']}\n"
            f"Content:\n{result['text']}"
        )

    context = "\n\n".join(context_parts)

    messages = [
        {
            "role": "system",
            "content": (
                "You are InsightPilot, a business intelligence assistant. "
                "Answer using only the supplied business report passages. "
                "Do not invent facts, numbers, events, or explanations. "

                "Separate your answer into these categories when relevant: "
                "1. Documented facts: explicitly stated in the reports. "
                "2. Possible explanations: factors the reports explicitly "
                "connect to the issue being investigated. "
                "3. Unconfirmed factors: observations that may be relevant "
                "but are not directly connected to the issue by the reports. "

                "Do not present an observation as a possible cause merely "
                "because it appears in the retrieved passages. "
                "Do not claim causation unless the reports explicitly "
                "establish it. "
                "If the evidence does not establish a connection, say so. "
                "If reports conflict, explain the conflict without "
                "resolving it yourself. "
                "Mention source filenames for important findings. "
                "The reports contain synthetic test data."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Retrieved business report passages:\n\n{context}\n\n"
                f"Question: {question}"
            ),
        },
    ]

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0,
        max_completion_tokens=4096,
    )

    answer = response.choices[0].message.content

    if not answer or not answer.strip():
        raise RuntimeError("The model returned an empty answer.")

    return answer


if __name__ == "__main__":
    question = input("Ask a question about the reports: ")
    print("\nInsightPilot:")
    print(ask_documents(question))
