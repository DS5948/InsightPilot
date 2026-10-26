
import os
import json
from concurrent.futures import ThreadPoolExecutor
from typing import Literal, TypedDict

from dotenv import load_dotenv
from groq import Groq
from langgraph.graph import StateGraph, START, END

from llm import ask_insightpilot
from rag_llm import ask_documents


# Load environment variables and initialize Groq.
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY is missing from .env")

MODEL_NAME = "openai/gpt-oss-120b"
client = Groq(api_key=api_key)


class InsightPilotState(TypedDict):
    question: str
    answer: str
    route: str


def classify_question(state: InsightPilotState) -> dict:
    """Use an LLM to classify a question by its information needs."""

    question = state["question"].strip()

    if not question:
        return {"route": "general"}

    
    system_prompt = """
You are the question router for InsightPilot.

Classify the user's message into exactly one route:

1. analytics:
   The answer requires analyzing the currently uploaded dataset,
   regardless of its subject or column names.
   This includes counting, filtering, grouping, sorting,
   aggregations, comparisons, trends, and calculations.

2. documents:
   The answer requires information from uploaded documents,
   reports, company strategy, priorities, policies, or plans.

3. both:
   The answer requires information from both the active dataset
   and uploaded documents.

4. general:
   Greetings, small talk, general knowledge questions, or questions
   unrelated to the active dataset and uploaded documents.

Rules:
- Classify according to the user's intent.
- The active dataset may contain employee, sales, financial,
  operational, or other types of data.
- Questions about employees, departments, attrition, overtime,
  salaries, and office locations must use analytics when they
  refer to the uploaded dataset.
- Questions asking for counts, percentages, rankings, or
  comparisons from the active dataset use analytics.
- Questions about company policies or strategy use documents
  when they require information from those documents.
- Use both when the answer requires the dataset and documents.
- Do not answer the question. Only classify it.

Return a valid JSON object with exactly one field named "route".
The value must be analytics, documents, both, or general.
"""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            temperature=0,
            max_completion_tokens=256,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content

        if not content:
            raise ValueError("The router returned an empty response.")

        result = json.loads(content)
        route = result.get("route")

        if route not in {"analytics", "documents", "both", "general"}:
            raise ValueError(f"Invalid route returned by router: {route}")

        return {"route": route}

    except Exception as exc:
        raise RuntimeError(
            f"Question classification failed: {type(exc).__name__}: {exc}"
        ) from exc


def analytics_node(state: InsightPilotState) -> dict:
    """Answer using approved sales analytics tools."""

    answer = ask_insightpilot(state["question"])
    return {"answer": answer}


def documents_node(state: InsightPilotState) -> dict:
    """Answer using retrieved business report passages."""

    answer = ask_documents(state["question"])
    return {"answer": answer}


def general_node(state: InsightPilotState) -> dict:
    """Respond to greetings and questions outside InsightPilot's scope."""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are InsightPilot, a business intelligence assistant. "
                    "Respond naturally to greetings and brief small talk. "
                    "For questions unrelated to sales analytics or uploaded "
                    "business documents, politely explain your capabilities "
                    "and suggest a relevant business question. "
                    "Do not invent findings from the user's data or documents."
                ),
            },
            {"role": "user", "content": state["question"]},
        ],
        temperature=0,
        max_completion_tokens=300,
    )

    answer = response.choices[0].message.content

    if not answer or not answer.strip():
        raise RuntimeError(
            "The general-response model returned an empty answer."
        )

    return {"answer": answer.strip()}


def synthesize_answer(
    question: str,
    analytics_answer: str,
    documents_answer: str,
) -> str:
    """Combine analytics and report findings into one answer."""

    messages = [
        {
            "role": "system",
            "content": (
                "You are InsightPilot, a business intelligence assistant. "
                "Combine the supplied analytics results and business report "
                "findings into one clear, concise answer. Preserve numerical "
                "facts from the analytics results. Use reports only for "
                "explanations supported by their contents. Do not invent "
                "facts, numbers, or causes. Clearly distinguish verified "
                "results from possible explanations. State when a cause "
                "is not confirmed. Mention relevant source filenames. "
                "Do not claim that reports are unavailable when report "
                "findings have been supplied. Avoid repeating information."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Question:\n{question}\n\n"
                f"Analytics findings:\n{analytics_answer}\n\n"
                f"Business report findings:\n{documents_answer}"
            ),
        },
    ]

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0,
        max_completion_tokens=2048,
    )

    answer = response.choices[0].message.content

    if not answer or not answer.strip():
        raise RuntimeError("The synthesis model returned an empty answer.")

    return answer.strip()


def combined_node(state: InsightPilotState) -> dict:
    """Run analytics and document retrieval concurrently, then synthesize."""

    question = state["question"]

    with ThreadPoolExecutor(max_workers=2) as executor:
        analytics_future = executor.submit(ask_insightpilot, question)
        documents_future = executor.submit(ask_documents, question)

        analytics_answer = analytics_future.result()
        documents_answer = documents_future.result()

    answer = synthesize_answer(
        question=question,
        analytics_answer=analytics_answer,
        documents_answer=documents_answer,
    )

    return {"answer": answer}


def choose_route(
    state: InsightPilotState,
) -> Literal["analytics", "documents", "both", "general"]:
    return state["route"]


# Build the LangGraph workflow.
builder = StateGraph(InsightPilotState)

builder.add_node("classify", classify_question)
builder.add_node("analytics", analytics_node)
builder.add_node("documents", documents_node)
builder.add_node("both", combined_node)
builder.add_node("general", general_node)

builder.add_edge(START, "classify")

builder.add_conditional_edges(
    "classify",
    choose_route,
    {
        "analytics": "analytics",
        "documents": "documents",
        "both": "both",
        "general": "general",
    },
)

builder.add_edge("analytics", END)
builder.add_edge("documents", END)
builder.add_edge("both", END)
builder.add_edge("general", END)

graph = builder.compile()


if __name__ == "__main__":
    while True:
        question = input(
            "\nAsk InsightPilot a business question "
            "(or type 'exit' to quit): "
        ).strip()

        if question.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        if not question:
            print("Please enter a question.")
            continue

        try:
            result = graph.invoke(
                {
                    "question": question,
                    "answer": "",
                    "route": "",
                }
            )

            print(f"\nSelected route: {result['route']}")
            print("\nInsightPilot:")
            print(result["answer"])

        except Exception as error:
            print(f"\nError: {type(error).__name__}: {error}")
