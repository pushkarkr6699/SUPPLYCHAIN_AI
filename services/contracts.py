from typing import Any, Protocol
import pandas as pd


class AnalyticsService(Protocol):
    """Replace the provider, preserving these UI-facing contracts.

    Real implementations must enforce dataset grain, filters and provenance.
    Missing signals must return unavailable status, never synthetic fallbacks.
    """
    demo: bool
    def records(self, filters: dict | None = None) -> pd.DataFrame: ...
    def options(self) -> dict[str, list]: ...
    def evidence(self, records: pd.DataFrame, filters: dict) -> dict[str, Any]: ...
    def model_status(self) -> list[dict]: ...


class AuthService(Protocol):
    def sign_in(self, username: str) -> dict: ...

