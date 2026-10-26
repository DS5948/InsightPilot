
from llm import ask_insightpilot

questions = [
    "What are our total revenue, total profit, and number of sales records?",
    "Which region generates the most revenue?",
    "Which product generates the most revenue?",
    "Show our monthly revenue trend.",
]

for question in questions:
    print("\n" + "=" * 60)
    print("Question:", question)
    print("\nInsightPilot:")

    try:
        print(ask_insightpilot(question))
    except Exception as error:
        print(f"Test failed: {type(error).__name__}: {error}")
        raise
