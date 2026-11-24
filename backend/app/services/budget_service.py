from decimal import Decimal, ROUND_HALF_UP

NEAR_LIMIT_RATIO = Decimal("0.8")  # 80% of the budget or more -> near_limit


def _d(value) -> Decimal:
    # str() first so 0.1 stays 0.1 instead of 0.1000000000000000055...
    return Decimal(str(value))


def _money(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def compute_budget(budget_total: float, activities: list[dict]) -> dict:
    """
    Single source of truth for the Trip Budget progress bar.
    Pure function (no DB, no I/O) so it is trivial to test.
    Uses Decimal so currency sums do not drift (0.1 + 0.2 != 0.3 in float).
    """
    budget = _d(budget_total)
    estimated = sum((_d(a["estimated_cost"]) for a in activities), Decimal(0))

    with_actual = [a for a in activities if a.get("actual_cost") is not None]
    actual = sum((_d(a["actual_cost"]) for a in with_actual), Decimal(0))
    variance = sum(
        (_d(a["actual_cost"]) - _d(a["estimated_cost"]) for a in with_actual),
        Decimal(0),
    )

    if budget <= 0:
        percent = Decimal(0)
        status = "no_budget"
    else:
        percent = (estimated / budget * 100).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        if estimated > budget:
            status = "over_budget"
        elif estimated >= budget * NEAR_LIMIT_RATIO:
            status = "near_limit"
        else:
            status = "on_track"

    return {
        "budget_total": _money(budget),
        "total_estimated": _money(estimated),
        "total_actual": _money(actual),
        "actual_variance": _money(variance),
        "remaining": _money(budget - estimated),
        "percent_used": float(percent),
        "status": status,
    }