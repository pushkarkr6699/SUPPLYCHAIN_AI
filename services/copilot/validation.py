ALLOWED_ROUTES = {
    "overview", "delivery", "demand", "geography", "changes", "orders",
    "explainability", "reports", "scenarios",
}


def validate_question(question):
    if not isinstance(question, str) or not question.strip() or len(question) > 1000:
        raise ValueError("Question must contain 1–1000 characters.")
    return question.strip()


def validate_route(route):
    if route not in ALLOWED_ROUTES:
        raise ValueError("Copilot navigation target is not allowlisted.")
    return route


def validate_filter(df, column, values):
    if column not in df.columns or column in {"Order", "Risk Probability", "Actual Late"}:
        raise ValueError("This filter is not supported by the Copilot action.")
    allowed = set(df[column].dropna().unique().tolist())
    values = list(values)
    if any(value not in allowed for value in values):
        raise ValueError("Filter value is outside the current data context.")
    return column, values
