"""Statistics calculated from persisted provider data, with explicit coverage."""

def safe_div(numerator, denominator):
    return round(numerator / denominator, 3) if denominator else None
