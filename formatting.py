"""Formats Tontinator API results into human-readable text for LLM consumption."""

from context_data import ASSET_TYPE_DESCRIPTIONS

# Age milestones shown in payout tables: payout start age, then +5, +10, +15, +20 years.
MILESTONE_OFFSETS = [0, 5, 10, 15, 20]


def extract_milestones(payouts: list[dict], payout_age_years: int) -> list[dict]:
    """Return one payout entry per milestone age, starting from payout_age_years."""
    targets = {payout_age_years + offset for offset in MILESTONE_OFFSETS}
    seen: set[int] = set()
    milestones = []
    for p in payouts:
        yr = p["age"]["years"]
        if yr in targets and p["age"]["months"] == 0 and yr not in seen:
            milestones.append(p)
            seen.add(yr)
    return milestones


def fmt_amount(amount: float | None) -> str:
    """Format a payout figure as a plain number with thousands separators.

    The Tontinator is currency-agnostic: 100,000 contributed is 100,000
    regardless of the user's local currency, so no symbol is added.
    """
    if amount is None:
        return "N/A"
    return f"{amount:,.0f}"


def format_single_result(results: dict, asset_type: str, label: str = "") -> str:
    """Format one Tontinator result into a labelled, readable text block for the LLM."""
    payouts: list[dict] = results.get("payouts", [])
    total_contributions: float = results.get("_total_contributions", 0)
    annual_inflation: float = results.get("annual_inflation_rate", 0.03)

    if not payouts:
        return "No payout data returned."

    payout_age_years = payouts[0]["age"]["years"]
    milestones = extract_milestones(payouts, payout_age_years)

    asset_meta = ASSET_TYPE_DESCRIPTIONS.get(asset_type, {})
    asset_label = asset_meta.get("label", asset_type) if isinstance(asset_meta, dict) else asset_type

    header = f"{'=' * 56}\n"
    header += (
        "NOTE: Figures are currency-agnostic (100,000 contributed is 100,000\n"
        "regardless of local currency) and are illustrative projections —\n"
        "present to the user as approximate ranges, not guaranteed amounts.\n"
        f"{'=' * 56}\n"
    )
    if label:
        header += f"Scenario: {label}\n"
    header += (
        f"Asset type       : {asset_type} — {asset_label}\n"
        f"Total contributed: {fmt_amount(total_contributions)}\n"
        f"Inflation rate   : {annual_inflation * 100:.1f}% per year\n"
        f"Payouts start at age {payout_age_years}\n"
        f"{'=' * 56}\n"
    )

    table_header = f"\n{'Age':<5}  {'Tontine/mo':>12}  {'Infl.adj':>12}  {'Annuity/mo':>12}\n"
    table_header += f"{'-'*5}  {'-'*12}  {'-'*12}  {'-'*12}\n"

    rows = []
    for p in milestones:
        age_yr = p["age"]["years"]
        tontine_amt = p["tontine"].get("amount")
        tontine_adj = p["tontine"].get("amount_inflation_adjusted")
        annuity_amt = p["annuity"].get("amount")
        rows.append(
            f"{age_yr:<5}  {fmt_amount(tontine_amt):>12}  "
            f"{fmt_amount(tontine_adj):>12}  "
            f"{fmt_amount(annuity_amt):>12}"
        )

    note = _build_insight_note(milestones)
    return header + table_header + "\n".join(rows) + "\n" + note


def format_comparison(results_list: list[tuple[str, dict, str]]) -> str:
    """Format multiple scenarios as separate result blocks joined together."""
    return "\n\n".join(
        format_single_result(results, asset_type, label=label)
        for label, results, asset_type in results_list
    )


def _build_insight_note(milestones: list[dict]) -> str:
    """Build the 'key insight' note comparing tontine growth and annuity at payout start."""
    if len(milestones) < 2:
        return ""

    first, last = milestones[0], milestones[-1]
    t_first = first["tontine"].get("amount", 0) or 0
    t_last = last["tontine"].get("amount", 0) or 0
    a_first = first["annuity"].get("amount", 0) or 0
    note = ""

    if t_last > t_first > 0:
        growth_pct = ((t_last / t_first) - 1) * 100
        note = (
            f"\nKey insight: Tontine payout grows {growth_pct:.0f}% from age "
            f"{first['age']['years']} to {last['age']['years']} due to mortality "
            f"credits — as pool members pass away, their balance is redistributed "
            f"to survivors, increasing everyone's monthly income.\n"
        )

    if a_first and t_first:
        diff = t_first - a_first
        direction = "higher" if diff > 0 else "lower"
        note += (
            f"At payout start, tontine pays {fmt_amount(abs(diff))}/mo "
            f"{direction} than the annuity equivalent.\n"
        )

    return note
