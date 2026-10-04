"""Deterministic UI illustration, explicitly NOT model inference."""
from services.mock_data import SCENARIO_FACTORS, SCENARIO_DEMAND_BASE


def delivery_scenario(baseline, original_shipping, shipping):
    return min(.99, max(.01, baseline + SCENARIO_FACTORS[shipping] - SCENARIO_FACTORS[original_shipping]))


def demand_scenario(multiplier):
    return round(SCENARIO_DEMAND_BASE * multiplier)

