"""Tontine API client — builds request payloads for and calls the Tontinator API."""

import httpx

TONTINATOR_ENDPOINT = "https://api.mytontine.com/v2/payout_forecast/tontinator"


def build_payload(
    current_age_years: int,
    current_age_months: int,
    country: str,
    sex: str | None,
    onetime_amount: float | None,
    monthly_amount: float | None,
    payout_age_years: int,
    payout_age_months: int,
    asset_type: str,
) -> dict:
    """Build a single Tontinator API request payload from user-supplied parameters."""
    payload: dict = {
        "demographic_data_country_of_residence": country.upper(),
        "demographic_data_current_age": {
            "year": current_age_years,
            "month": current_age_months or 0,
        },
        "contributions": {
            "payout_age": {
                "year": payout_age_years,
                "month": payout_age_months or 0,
            },
        },
        "contribution_allocations": asset_type,
        "write_draft_plan": False,
    }
    if sex:
        payload["demographic_data_sex"] = sex
    if onetime_amount:
        payload["contributions"]["onetime_amount"] = int(onetime_amount)
    if monthly_amount:
        payload["contributions"]["monthly_amount"] = int(monthly_amount)
    return payload


async def call_tontinator(payload: dict, client: httpx.AsyncClient) -> dict | str:
    """POST a payload to the Tontinator API.

    Returns the results dict on success, or an error string on failure.
    The API wraps each result in a list, so we unwrap the first (and only) item.
    """
    try:
        resp = await client.post(TONTINATOR_ENDPOINT, json=[payload], timeout=30.0)
    except httpx.RequestError as e:
        return f"Network error contacting Tontinator API: {e}"

    if resp.status_code != 200:
        try:
            body = resp.json()
            msg = body.get("message", resp.text)
        except Exception:
            msg = resp.text
        return f"API error {resp.status_code}: {msg}"

    data = resp.json()
    if not data or not isinstance(data, list):
        return "Unexpected API response format."

    first_result = data[0]
    if "results" not in first_result:
        return f"API returned no results. Raw: {first_result}"

    return first_result["results"]
