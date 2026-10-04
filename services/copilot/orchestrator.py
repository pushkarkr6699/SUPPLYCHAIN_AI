from services.copilot.intent import classify
from services.copilot.context import snapshot
from services.copilot.response import build
from services.copilot.validation import validate_question


def respond(question, df, mode="Explore", selected_order=None, filters=None):
    question = validate_question(question)
    intent = classify(question, mode)
    result = build(intent, df, selected_order)
    result["evidence_context"] = snapshot(df, filters)
    if mode == "Simulate":
        result["route"] = "scenarios"
    elif mode == "Report" and intent != "unsupported":
        result["route"] = "reports"
    return result
