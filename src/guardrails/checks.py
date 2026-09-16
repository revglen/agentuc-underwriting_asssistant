"""
Sanity checks run on LLM-generated tool output before it's returned to a
caller. These catch results that are individually well-typed (pass Pydantic
field constraints) but violate a domain invariant the schema alone can't
express - a rating that doesn't match its score, an approved amount that
exceeds what was requested, a declined decision with no reasons given.
"""
from __future__ import annotations

from errors.exceptions import ValidationError

_RATING_BANDS = [
    (750, 850, "excellent"),
    (670, 749, "good"),
    (580, 669, "fair"),
    (300, 579, "poor"),
]


def _band_for_score(score: int) -> str:
    for low, high, band in _RATING_BANDS:
        if low <= score <= high:
            return band
    return "poor"


def check_credit_score(score: int, rating: str) -> None:
    if not (300 <= score <= 850):
        raise ValidationError(f"LLM produced an out-of-range credit score: {score}")
    expected = _band_for_score(score)
    if rating.lower() != expected:
        raise ValidationError(
            f"LLM produced an inconsistent rating {rating!r} for score {score} (expected {expected!r})"
        )


def check_bank_statement(avg_monthly_income: float, avg_monthly_expenses: float) -> None:
    if avg_monthly_income <= 0:
        raise ValidationError(f"LLM produced a non-positive avg_monthly_income: {avg_monthly_income}")
    if avg_monthly_expenses < 0:
        raise ValidationError(f"LLM produced a negative avg_monthly_expenses: {avg_monthly_expenses}")


def check_transaction_summary(category_breakdown: dict, total_outflow: float, tolerance: float = 0.05) -> None:
    breakdown_sum = sum(category_breakdown.values())
    if breakdown_sum <= 0:
        raise ValidationError("LLM produced an empty or zero category_breakdown")
    if abs(breakdown_sum - total_outflow) > max(tolerance * total_outflow, 1.0):
        raise ValidationError(
            f"LLM's total_outflow ({total_outflow}) doesn't match its own "
            f"category_breakdown sum ({breakdown_sum})"
        )


def check_policy_decision(
    decision: str, reasons: list[str], max_approved_amount: float, requested_amount: float
) -> None:
    if decision not in ("approved", "declined"):
        raise ValidationError(f"LLM produced an invalid decision: {decision!r} (must be 'approved' or 'declined')")
    if decision == "declined" and not reasons:
        raise ValidationError("LLM declined the application but gave no reasons")
    if decision == "approved" and max_approved_amount <= 0:
        raise ValidationError("LLM approved the application but max_approved_amount is 0")
    if max_approved_amount > requested_amount:
        raise ValidationError(
            f"LLM approved more than requested: max_approved_amount={max_approved_amount} "
            f"> requested_amount={requested_amount}"
        )
    if decision == "declined" and max_approved_amount != 0:
        raise ValidationError(f"LLM declined but max_approved_amount is nonzero: {max_approved_amount}")
