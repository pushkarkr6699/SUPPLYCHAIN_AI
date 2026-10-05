import re


def unsafe_request(question):
    """Refuse executable, file-access and mutation requests before intent routing."""
    return bool(re.search(r"\b(execute|delete|overwrite|subprocess|eval|exec)\b|os\.(system|remove)|\.env\b|\b(shell|python)\s+(command|code)|\brun\s+(?:this\s+)?(?:python|shell|command)|\b(?:change|modify|set)\b.{0,40}\b(?:model|threshold|source code)\b", str(question), re.IGNORECASE))


def classify(question, mode="Explore"):
    """Map plain language to a small allowlist; unknown requests fail closed."""
    query = str(question).casefold()
    if len(query) > 1000 or mode == "Simulate" or unsafe_request(query):
        return "unsupported"
    if "compare" in query and any(name in query for name in ("europe", "latam")):
        return "compare"
    if any(word in query for word in ("increasing", "increase", "acceleration", "accelerating")) and any(word in query for word in ("demand", "product")):
        return "demand_growth"
    if any(word in query for word in ("market", "markets", "region", "regions")) and any(word in query for word in ("risk", "highest", "investigate")):
        return "region_risk" if "region" in query else "market_risk"
    if "explain" in query or "why" in query:
        return "explain"
    if "changed" in query or "change" in query or "recently" in query:
        return "change"
    if any(word in query for word in ("demand", "forecast", "product")):
        return "demand"
    if any(word in query for word in ("risk", "order", "market", "region")):
        return "risk"
    return "unsupported"
