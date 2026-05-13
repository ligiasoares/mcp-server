"""Tontine MCP — loads educational content and asset type definitions from content.json."""

import json
import pathlib

_content_path = pathlib.Path(__file__).parent / "content.json"
_content = json.loads(_content_path.read_text(encoding="utf-8"))

RESOURCES: dict = _content["resources"]
ASSET_TYPE_DESCRIPTIONS: dict = _content["asset_types"]

# TOOLS_METADATA is used exclusively by views.py to render the dashboard HTML.
# It is NOT the source of truth for the MCP protocol — that lives in server.py (list_tools).
# Keep descriptions here roughly in sync with server.py, but they don't need to be identical.
TOOLS_METADATA = [
    {
        "name": "get_tontine_info",
        "description": (
            "Get background information about Tontine Trust: what it is, how it compares to annuities, "
            "how mortality credits work, the available asset/distribution profiles, and how "
            "member assets are protected."
        ),
        "params": "topic: <resource-slug> | all  (slugs are derived from content.json resource keys)",
    },
    {
        "name": "calculate_tontine_payout",
        "description": (
            "Calculate illustrative lifetime income projections using the Tontinator API. Returns projected "
            "monthly payout amounts for a tontine vs an annuity at key age milestones (+0, +5, +10, +15, +20 years "
            "from payout start). Results are approximate — present as indicative ranges, not guarantees."
        ),
        "params": (
            "current_age_years, country (ISO 3166-1 alpha-3), sex, "
            "onetime_amount, monthly_amount (optional), payout_age_years, asset_type"
        ),
    },
    {
        "name": "compare_tontine_scenarios",
        "description": (
            "Compare 2–4 tontine scenarios side-by-side. Useful for 'retire at 70 vs 80', "
            "'$300k vs $500k', or comparing asset types. Runs all scenarios in parallel. "
            "Results are approximate projections."
        ),
        "params": "scenarios[]: array of calculation requests, each with a label",
    },
    {
        "name": "get_asset_types",
        "description": (
            "List all available asset allocation types with descriptions. "
            "Call this when the user asks about asset options before recommending one."
        ),
        "params": "(none)",
    },
]
