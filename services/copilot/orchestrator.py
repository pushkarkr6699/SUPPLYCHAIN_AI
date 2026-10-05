from services.copilot.intent import classify, unsafe_request
from services.copilot.context import snapshot
from services.copilot.response import build
from services.copilot.validation import validate_question


def respond(question, df, mode="Explore", selected_order=None, filters=None):
    question = validate_question(question)
    intent = classify(question, mode)
    result = build(intent, df, selected_order)
    if unsafe_request(question):
        result.update(title="Request outside the analytics boundary", narrative="I can analyze approved dataset values. I cannot execute code or commands, access secret files, delete data, or modify models and thresholds.")
    result["evidence_context"] = snapshot(df, filters)
    if mode == "Simulate":
        result["route"] = "scenarios"
    elif mode == "Report" and intent != "unsupported":
        result["route"] = "reports"
    return result
