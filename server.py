#!/usr/bin/env python3
"""Tontine MCP Server — wraps api.mytontine.com for LLM tool use."""

import argparse
import asyncio
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

API_BASE = "https://api.mytontine.com"
TONTINATOR_ENDPOINT = f"{API_BASE}/v2/payout_forecast/tontinator"

# ---------------------------------------------------------------------------
# Educational resources
# ---------------------------------------------------------------------------

RESOURCES = {
    "tontine://what-is-a-tontine": {
        "name": "What is a Tontine?",
        "description": "Introduction to Tontine Trust: what it is, how it works, who it is for, key benefits and caveats",
        "mimeType": "text/markdown",
        "content": """\
# What is a Tontine Trust?

**Tontine Trust** (tontine.com / mytontine.com) is a modern fintech platform that revives a centuries-old
concept — the tontine — using secure individual trust structures and digital administration.
It was founded by entrepreneur Dean McClelland and is an Irish-registered company featured in
Forbes, Bitcoin Magazine, MoneySense, and the Retirement Income Journal.

## The core idea

When you join a Tontine Trust, you contribute savings into your own **individual irrevocable trust**.
That trust is then enrolled in a **Tontine Class** — a pool of members of similar age and sex (max 10,000
per class). Every month, you receive lifetime income from your trust.

When a class member dies, they no longer need their monthly income. Their remaining balance is
redistributed proportionally to all surviving members — increasing everyone else's monthly payout.
This redistribution is called a **mortality credit**, and it is the reason tontine payouts naturally
*rise over time* as the pool ages.

The longer you live, the more you receive. You cannot outlive your money.

## Three stages of membership

1. **Form your trust online** — takes about 15 minutes. Choose your contribution, investment type,
   and the age at which you want payouts to begin.
2. **The Tontine begins** — your trust joins its age/sex-matched class. Every month you receive
   income; every month survivors inherit mortality credits from those who have passed.
3. **The Über Tontine** — when the average age of the class reaches 100, it transitions into an
   extended support structure for the very long-lived.

## Key advantages

- **Lifetime income**: monthly payments for as long as you live.
- **Rising payouts**: mortality credits increase your income over time — the opposite of a fixed annuity.
- **Low flat fee**: 1% per year, no setup costs, no hidden charges, no commissions.
- **Individual trusts**: your savings are legally separate from Tontine Trust's own assets — you are
  not exposed to the company's balance sheet.
- **No contribution ceiling**: unlike annuities (typically capped at $200,000), you can contribute
  as much as you want. A larger balance means larger mortality credits when classmates pass away.
- **People with lifetime incomes are happier and live up to 20% longer** than those who fear running
  out of money. Tontine Trust's mission is to eliminate that fear.
- **Rollover-friendly**: TontineIRA® accepts rollovers from 401(k), 403(b), traditional IRA, SEP IRA,
  457(b) Government plans, Qualified plans, and Simple IRAs.

## When a Tontine Trust is NOT suitable

Honesty matters. A Tontine Trust is not the right fit if:
- You are in poor health with a significantly reduced life expectancy.
- You may need emergency access to a lump sum — the trust is irrevocable and cannot be surrendered.
- You require a fixed monthly amount regardless of market conditions.

## Trust options available

- **Solo Tontine Trust Fund** — individual lifetime income.
- **Joint Tontine Trust Fund** — spousal income (income continues to surviving spouse).
- **Family Tontine Trust Fund** — multi-generational: specified monthly income to children or grandchildren,
  protecting inheritance from wasteful spending and potentially reducing inheritance taxes.
- **TontineIRA®** — tax-advantaged structure for US retirement savings.

## Modern tontines vs. the old banned policies

Tontine *insurance* policies were banned in the US in the early 20th century due to widespread insurer
abuses uncovered by the Armstrong Commission. Tontine *trusts* are entirely different: they are
non-insurance financial vehicles, transparent, fiduciary-governed, and operate under modern trust law —
not insurance regulation. They represent a legitimate, regulated reinvention of the concept.
""",
    },
    "tontine://tontine-vs-annuity": {
        "name": "Tontine vs Annuity",
        "description": "Side-by-side comparison of Tontine Trust and traditional annuities — trade-offs, numbers, and when each makes sense",
        "mimeType": "text/markdown",
        "content": """\
# Tontine vs Annuity

Both tontines and annuities provide lifetime income. But they work very differently,
and for the right person the difference in lifetime income can be dramatic.

## Side-by-side comparison

| Feature | Tontine Trust | Traditional Annuity |
|---|---|---|
| Monthly payout trend | **Grows over time** (mortality credits) | Fixed or marginally adjusted |
| Payout driver | Investment returns + mortality credits from deceased members | Insurance company pricing |
| Death benefit | None — balance stays in the pool for survivors | Often yes (at added premium cost) |
| Counterparty risk | Pool of members + trust structure | Insurance company solvency |
| Longevity bonus | **Yes — the longer you live, the more you receive** | No |
| Contribution limit | **Unlimited** | Typically capped at ~$200,000 |
| Annual fee | **1% flat, no hidden charges** | Often 2–3%+ with commissions |
| Inflation protection | Partial (via gold/BTC investment growth) | Very limited |
| Setup | Online in ~15 minutes | Often weeks of paperwork |
| Best for | Longevity protection, maximising lifetime income | Predictability, legacy planning |

## The key trade-off

An annuity gives you **certainty**: you know exactly what you'll receive every month, forever.
A tontine gives you **upside**: the longer you live, the more you earn — powered by the mortality
credits of classmates who have passed away.

For someone who lives into their late 80s or 90s, a tontine typically pays dramatically more in
total lifetime income than an equivalent annuity. For someone who passes away early, an annuity
with a death benefit would have been more favourable.

Roughly **25%+ of today's retirees live into their 90s or beyond**. Life expectancies are averages,
not limits — 50% of people will live longer than the average. Tontines are specifically designed
for this half of the population.

## The annuity ceiling problem

Annuities in the US are typically capped at around $200,000. With Tontine Trust, there is no limit.
This makes tontines particularly attractive for people with substantial retirement savings who want
maximum longevity protection on their full portfolio.

## Real numbers

Use the `calculate_tontine_payout` tool to get precise monthly figures for your specific situation.
The Tontinator shows tontine and annuity amounts side-by-side at key age milestones (payout start,
+5 years, +10, +15, +20), so you can see exactly how the income gap evolves as you age.
""",
    },
    "tontine://mortality-credits": {
        "name": "How Mortality Credits Work",
        "description": "How the tontine mechanism causes payouts to grow — mortality credits, the nightly adjustment system, and why payouts increase with age",
        "mimeType": "text/markdown",
        "content": """\
# How Mortality Credits Work

Mortality credits are the engine that makes tontine payouts grow over time.
Understanding them is key to understanding why tontines outperform annuities for long-lived members.

## The basic mechanic

When a Tontine Class member dies, they no longer need their monthly income.
Their remaining trust balance is redistributed proportionally to all surviving members.
This redistribution is called a **mortality credit**.

The older the class, the higher the natural mortality rate — and therefore the larger
the monthly mortality credits flowing to survivors. This is not a windfall or a gamble;
it is a mathematically predictable sharing of longevity risk.

## Nightly micro-adjustments

Tontine Trust's platform performs **nightly micro-adjustments** of each member's payments,
based on actual death rates and actual investment performance. This is what the FAQs describe
as "the hallmark of the safest pension funds in the world." Payouts adjust continuously to
reflect reality, not fixed actuarial assumptions made decades ago.

## The payout formula (simplified)

Monthly payout ≈ member balance × (mortality_force + monthly_investment_return)

- **mortality_force**: the probability of dying this month given age, sex, and country.
  This increases every year as you age — which is why payouts grow.
- **monthly_investment_return**: returns from the underlying trust assets (gold, Bitcoin, etc.)

## Why payouts compound upward

As you age, three forces combine:
1. **Mortality force increases** — more classmates pass each month, sending larger credits to survivors.
2. **Your balance has grown** — years of investment returns have compounded your trust value.
3. **Fewer survivors share the credits** — your proportional share of incoming mortality credits grows.

These three effects stack. A tontine payout at age 85 can easily be 2–3× what it was at age 75,
while an annuity payment stays flat.

## Sustainability

Unlike a defined-benefit pension or insurance annuity, a Tontine Trust cannot become insolvent.
Payouts are always a function of what is actually in the pool — they adjust to match reality.
"You can be sure that the money will never run out" because the mechanism is self-correcting:
if members live longer than expected, payouts adjust downward; if investment returns are strong,
they adjust upward.

## Inflation-adjusted view

The Tontinator shows both nominal and inflation-adjusted payouts side-by-side, so you can
evaluate not just the headline number but the real purchasing power of your income 10 or 20 years
from now. This matters because even modest inflation (2–3%) erodes fixed income significantly over
a 20-year retirement.
""",
    },
    "tontine://distribution-profiles": {
        "name": "Flexible Distribution Profiles",
        "description": "The three investment/distribution profiles available on Tontine Trust: Gold Extra, Gold Standard, Gold Reserve — trade-offs and how to choose",
        "mimeType": "text/markdown",
        "content": """\
# Flexible Distribution Profiles

Tontine Trust offers three distribution profiles, each using a different historical window
for the gold CAGR (compound annual growth rate) to set payout levels. The choice affects
how aggressively or conservatively your monthly income is distributed during your lifetime.

## The three profiles

### Gold Extra (XAU5Y) — Aggressive
Uses the **past 5 years** of gold CAGR as the basis for distributions.
- Higher near-term payouts — you receive more income earlier.
- More responsive to recent gold price movements.
- Greater variability: if real future gold CAGR falls short of the recent 5-year run,
  late-life payouts may be lower than projected.
- Best for: members who want maximum income now and are comfortable with some variability.

### Gold Standard (XAU10Y) — Balanced *(default)*
Uses the **past 10 years** of gold CAGR.
- Balanced approach between near-term income and long-term stability.
- Moderate variability — not as front-loaded as Gold Extra, not as conservative as Gold Reserve.
- Best for: most members who want a reasonable income without extreme swings in either direction.

### Gold Reserve (XAU20Y) — Conservative
Uses the **past 20 years** of gold CAGR (the most conservative assumption).
- Lower initial distributions, but more gradual and stable adjustment over time.
- If actual gold CAGR exceeds the 20-year historical average, late-life payouts grow larger.
- Best for: members who prioritise stability and are willing to accept lower early payouts
  in exchange for more predictable long-term income.

## Additional options

- **Bitcoin (BTC)**: Very high risk, very high potential return. For members with a strong
  conviction in Bitcoin's long-term appreciation and a high risk tolerance.
- **Bold (BOL)**: A blended portfolio of 65% gold and 35% Bitcoin — balancing gold's
  stability with Bitcoin's upside potential.

## Important notes

- Distribution profiles represent **non-binding preferences**; final distributions are
  determined by the Trustee in accordance with the Trust Agreement.
- Distributions are **not guaranteed in amount or duration** — they are subject to
  actual asset performance and member mortality.
- Historical CAGR data is provided for educational purposes only and does not constitute
  a forecast or guarantee of future performance.
- The investment type affects only the **accumulation phase** (before payouts start).
  The tontine mortality credit mechanism operates the same way regardless of which
  profile you choose.

## How to choose

Ask yourself: do I want more money earlier, or do I want more stability?
- If you are starting payouts soon and want maximum income now: **Gold Extra**
- If you want a sensible middle ground: **Gold Standard** (the default)
- If you are conservative and value predictability over maximising early income: **Gold Reserve**
- If you have a high risk appetite and believe in Bitcoin: **Bold** or **BTC**

Use the `calculate_tontine_payout` tool to compare actual projected numbers across profiles
for your specific age, country, and contribution amount.
""",
    },
    "tontine://trust-property-and-security": {
        "name": "Trust Property & Security",
        "description": "How Tontine Trust holds and protects member assets — legal structure, custody, and what 'trust property' means in practice",
        "mimeType": "text/markdown",
        "content": """\
# Trust Property & Security

One of the most important features of Tontine Trust is the legal structure that protects
your assets. Unlike a bank account or an insurance policy, your money is not on the
company's balance sheet.

## Your money is in your own trust

When you contribute to Tontine Trust, your assets are deposited into an **individual irrevocable
trust** — a separate legal entity that only you can benefit from during your lifetime.
This creates a clean **legal separation between Trust Property and the personal assets of
the member**, as well as between your trust and Tontine Trust's corporate assets.

If Tontine Trust as a company ever faced financial difficulty, your trust assets would not
be at risk — they are not the company's to lose.

## What "beneficial interest" means

You hold a **beneficial interest** in the trust assets, not direct legal title.
The Trustee holds legal title and administers the trust according to the Trust Agreement
and applicable law. This is standard trust law — it's how all trust structures work,
and it provides important protections and continuity.

## Eligible assets

Trust Property may consist of:
- **Precious metals**: Gold, Silver, Copper (held in allocated/reserved physical form)
- **Digital assets**: Bitcoin (where legally permitted)
- **Blended options**: e.g. the Bold (BOL) profile (65% gold + 35% Bitcoin)

These asset types were deliberately chosen for their **long-term value storage
characteristics**: scarcity, durability, and non-sovereign value. They are not income-
generating instruments — they are stores of value that back your lifetime income stream.

## Custody

Assets may be held directly by the Trustee or through regulated third-party custodians.
Tontine Trust uses:
- **BitGo** — a leading institutional digital asset custodian securing over $100 billion
  in assets for more than 1,500 institutions worldwide.
- **Borderless** — for international payments infrastructure.

Regardless of which custodian holds the assets, **Trust Property remains held and administered
under the Trust Agreement at all times**. The custody structure does not change your rights.

## The irrevocable nature — what it means

The trust is **irrevocable**: once established, it cannot be terminated or surrendered for a
lump sum. This is by design — allowing early exits would reduce the mortality credits flowing
to other surviving members, undermining the fairness of the system.

If you ever need liquidity, the option is to **begin monthly payouts early** (subject to
tax implications for TontineIRA® holders under age 59.5). This is why Tontine Trust is
best suited for long-term savings you do not expect to need as a lump sum.

## The Trustee's role

The Trustee acts in a **fiduciary and administrative capacity only**. They do not provide
financial advice or make investment recommendations. Their role is to administer the trust
faithfully according to the Trust Agreement and applicable law — putting member interests first.
""",
    },
}

INVESTMENT_TYPE_DESCRIPTIONS = {
    "XAU5Y": "Tontine Trust Gold Extra — gold investment using the past 5-year gold CAGR. More aggressive payout distribution early on, but if real gold CAGR falls short, late-life payouts may be lower.",
    "XAU10Y": "Tontine Trust Gold Standard — gold investment using the past 10-year gold CAGR. Balanced payout distribution assuming normal growth.",
    "XAU20Y": "Tontine Trust Gold Reserved — gold investment using the past 20-year gold CAGR (conservative). Lower initial distributions, but if actual CAGR exceeds expectations, late-life payouts grow larger.",
    "BTC": "Bitcoin — very high risk, very high potential return.",
    "BOL": "Bold — portfolio allocated 65% gold and 35% Bitcoin (balanced between gold stability and BTC upside).",
}

app = Server("tontine-mcp")


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

@app.list_resources()
async def list_resources() -> list[types.Resource]:
    return [
        types.Resource(
            uri=uri,
            name=meta["name"],
            description=meta["description"],
            mimeType=meta["mimeType"],
        )
        for uri, meta in RESOURCES.items()
    ]


@app.read_resource()
async def read_resource(uri: types.AnyUrl) -> str:
    key = str(uri)
    if key not in RESOURCES:
        raise ValueError(f"Unknown resource: {uri}")
    return RESOURCES[key]["content"]


# ---------------------------------------------------------------------------
# Tools declaration
# ---------------------------------------------------------------------------

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_tontine_info",
            description=(
                "Get background information about Tontine Trust: what it is, how it compares to annuities, "
                "how mortality credits work, the available investment/distribution profiles, and how "
                "member assets are protected. Call this when the user asks general questions like "
                "'what is a tontine?', 'how does it work?', 'is it safe?', 'is it better than an annuity?', "
                "or 'what investment options are there?'. "
                "Also lists available educational resources for deeper reading."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "enum": ["overview", "vs_annuity", "mortality_credits", "distribution_profiles", "trust_security", "all"],
                        "description": (
                            "Which topic to retrieve: "
                            "'overview' = what is Tontine Trust and how it works, "
                            "'vs_annuity' = tontine vs annuity comparison, "
                            "'mortality_credits' = how payouts grow over time, "
                            "'distribution_profiles' = the investment profiles (Gold Extra/Standard/Reserve, BTC, Bold), "
                            "'trust_security' = how assets are held and protected, "
                            "'all' = everything at once."
                        ),
                        "default": "overview",
                    }
                },
            },
        ),
        types.Tool(
            name="calculate_tontine_payout",
            description=(
                "Calculate lifetime income projections using the Tontinator. "
                "Returns monthly payout amounts for a tontine structure vs an annuity, "
                "at key age milestones. "
                "The tontine payout grows over time due to mortality credits — "
                "when pool members die, their balance is redistributed to survivors, "
                "increasing everyone's payout. Use this to give users real numbers "
                "instead of generic estimates. "
                "If the user is unfamiliar with tontines, call get_tontine_info first."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "current_age_years": {
                        "type": "integer",
                        "description": "Current age in whole years (e.g. 65)",
                    },
                    "current_age_months": {
                        "type": "integer",
                        "description": "Additional months on top of years (0-11, default 0)",
                        "default": 0,
                    },
                    "country": {
                        "type": "string",
                        "description": "Country of residence as ISO 3166-1 alpha-3 code (e.g. USA, GBR, BRA, CAN)",
                    },
                    "sex": {
                        "type": "string",
                        "enum": ["Male", "Female"],
                        "description": "Biological sex — used for actuarial mortality calculations",
                    },
                    "onetime_amount": {
                        "type": "number",
                        "description": "One-time lump sum contribution (e.g. 500000 for $500,000)",
                    },
                    "monthly_amount": {
                        "type": "number",
                        "description": "Recurring monthly contribution amount (optional, can combine with onetime_amount)",
                    },
                    "payout_age_years": {
                        "type": "integer",
                        "description": "Age at which monthly payouts begin (e.g. 70, 75, 84)",
                    },
                    "payout_age_months": {
                        "type": "integer",
                        "description": "Additional months for payout start age (default 0)",
                        "default": 0,
                    },
                    "investment_type": {
                        "type": "string",
                        "enum": ["XAU5Y", "XAU10Y", "XAU20Y", "BTC", "BOL"],
                        "description": (
                            "Investment allocation strategy: "
                            "XAU5Y=Gold Extra (aggressive), XAU10Y=Gold Standard (balanced), "
                            "XAU20Y=Gold Reserved (conservative), BTC=Bitcoin, BOL=Bold (65% gold + 35% BTC). "
                            "Affects how contributions grow before payout starts."
                        ),
                        "default": "XAU10Y",
                    },
                },
                "required": ["current_age_years", "country", "payout_age_years", "onetime_amount"],
            },
        ),
        types.Tool(
            name="compare_tontine_scenarios",
            description=(
                "Compare two or more tontine scenarios side-by-side. "
                "Useful for questions like 'what if I retire at 70 vs 80?' or "
                "'what if I invest $300k vs $500k?' or comparing investment types. "
                "Each scenario is a separate calculation request."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "scenarios": {
                        "type": "array",
                        "description": "List of scenarios to compare (2-4 recommended)",
                        "items": {
                            "type": "object",
                            "properties": {
                                "label": {
                                    "type": "string",
                                    "description": "Human-readable label for this scenario (e.g. 'Retire at 70', 'Option A')",
                                },
                                "current_age_years": {"type": "integer"},
                                "current_age_months": {"type": "integer", "default": 0},
                                "country": {"type": "string"},
                                "sex": {"type": "string", "enum": ["Male", "Female"]},
                                "onetime_amount": {"type": "number"},
                                "monthly_amount": {"type": "number"},
                                "payout_age_years": {"type": "integer"},
                                "payout_age_months": {"type": "integer", "default": 0},
                                "investment_type": {
                                    "type": "string",
                                    "enum": ["XAU5Y", "XAU10Y", "XAU20Y", "BTC", "BOL"],
                                    "default": "BOL",
                                },
                            },
                            "required": ["current_age_years", "country", "payout_age_years", "onetime_amount"],
                        },
                        "minItems": 2,
                        "maxItems": 4,
                    }
                },
                "required": ["scenarios"],
            },
        ),
        types.Tool(
            name="get_investment_types",
            description="List available investment allocation types with descriptions. Call this if the user asks about investment options or before recommending an investment type.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def build_payload(
    current_age_years: int,
    current_age_months: int,
    country: str,
    sex: str | None,
    onetime_amount: float | None,
    monthly_amount: float | None,
    payout_age_years: int,
    payout_age_months: int,
    investment_type: str,
) -> dict:
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
        "contribution_allocations": investment_type or "XAU10Y",
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
    """Returns parsed result dict or an error string."""
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

    item = data[0]
    if "results" not in item:
        return f"API returned no results. Raw: {item}"

    return item["results"]


# ---------------------------------------------------------------------------
# Response formatting
# ---------------------------------------------------------------------------

def extract_milestones(payouts: list[dict], payout_age_years: int) -> list[dict]:
    """Pick one entry per year at +0, +5, +10, +15, +20 from payout start."""
    targets = {payout_age_years + offset for offset in [0, 5, 10, 15, 20]}
    seen: set[int] = set()
    milestones = []
    for p in payouts:
        yr = p["age"]["years"]
        mo = p["age"]["months"]
        if yr in targets and mo == 0 and yr not in seen:
            milestones.append(p)
            seen.add(yr)
    return milestones


def fmt_currency(amount: float | None, currency: str = "USD") -> str:
    if amount is None:
        return "N/A"
    symbol = {"USD": "$", "GBP": "£", "EUR": "€", "BRL": "R$"}.get(currency, currency + " ")
    return f"{symbol}{amount:,.0f}"


def format_single_result(results: dict, investment_type: str, label: str = "") -> str:
    payouts: list[dict] = results.get("payouts", [])
    currency: str = results.get("currency", "USD")
    total_contributions: float = results.get("_total_contributions", 0)
    annual_inflation: float = results.get("annual_inflation_rate", 0.03)

    if not payouts:
        return "No payout data returned."

    payout_age_years = payouts[0]["age"]["years"]
    milestones = extract_milestones(payouts, payout_age_years)

    header = f"{'=' * 56}\n"
    if label:
        header += f"Scenario: {label}\n"
    header += (
        f"Investment type : {investment_type} — {INVESTMENT_TYPE_DESCRIPTIONS.get(investment_type, '')}\n"
        f"Total invested  : {fmt_currency(total_contributions, currency)}\n"
        f"Inflation rate  : {annual_inflation * 100:.1f}% per year\n"
        f"Payouts start at age {payout_age_years}\n"
        f"{'=' * 56}\n"
    )

    col_age = "Age"
    col_tontine = "Tontine/mo"
    col_tontine_adj = "(inflation adj.)"
    col_annuity = "Annuity/mo"

    table_header = f"\n{'Age':<5}  {'Tontine/mo':>12}  {'Infl.adj':>12}  {'Annuity/mo':>12}\n"
    table_header += f"{'-'*5}  {'-'*12}  {'-'*12}  {'-'*12}\n"

    rows = []
    for p in milestones:
        age_yr = p["age"]["years"]
        tontine_amt = p["tontine"].get("amount")
        tontine_adj = p["tontine"].get("amount_inflation_adjusted")
        annuity_amt = p["annuity"].get("amount")
        rows.append(
            f"{age_yr:<5}  {fmt_currency(tontine_amt, currency):>12}  "
            f"{fmt_currency(tontine_adj, currency):>12}  "
            f"{fmt_currency(annuity_amt, currency):>12}"
        )

    # Key insight note
    first = milestones[0] if milestones else None
    last = milestones[-1] if len(milestones) > 1 else None
    note = ""
    if first and last:
        t_first = first["tontine"].get("amount", 0) or 0
        t_last = last["tontine"].get("amount", 0) or 0
        a_first = first["annuity"].get("amount", 0) or 0
        if t_last > t_first and t_first > 0:
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
                f"At payout start, tontine pays {fmt_currency(abs(diff), currency)}/mo "
                f"{direction} than the annuity equivalent.\n"
            )

    return header + table_header + "\n".join(rows) + "\n" + note


def format_comparison(results_list: list[tuple[str, dict, str]]) -> str:
    """Format multiple scenarios side-by-side summary."""
    parts = []
    for label, results, investment_type in results_list:
        parts.append(format_single_result(results, investment_type, label=label))
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    async with httpx.AsyncClient() as client:

        if name == "get_tontine_info":
            topic = arguments.get("topic", "overview")
            topic_map = {
                "overview": "tontine://what-is-a-tontine",
                "vs_annuity": "tontine://tontine-vs-annuity",
                "mortality_credits": "tontine://mortality-credits",
                "distribution_profiles": "tontine://distribution-profiles",
                "trust_security": "tontine://trust-property-and-security",
            }
            if topic == "all":
                uris = list(topic_map.values())
            else:
                uris = [topic_map.get(topic, "tontine://what-is-a-tontine")]

            parts = [RESOURCES[uri]["content"] for uri in uris if uri in RESOURCES]
            parts.append(
                "\n---\n"
                "**Educational resources available** (readable via MCP resource protocol):\n"
                + "\n".join(
                    f"- `{uri}` — {RESOURCES[uri]['name']}"
                    for uri in RESOURCES
                )
                + "\n\nFor precise monthly income numbers, use the `calculate_tontine_payout` tool."
            )
            return [types.TextContent(type="text", text="\n\n".join(parts))]

        if name == "get_investment_types":
            lines = ["Available investment allocation types:\n"]
            for code, desc in INVESTMENT_TYPE_DESCRIPTIONS.items():
                lines.append(f"  {code}: {desc}")
            lines.append(
                "\nNote: investment type affects how contributions grow during the "
                "accumulation phase (before payouts start). It does not affect the "
                "tontine mechanism (mortality credits) itself."
            )
            return [types.TextContent(type="text", text="\n".join(lines))]

        if name == "calculate_tontine_payout":
            payload = build_payload(
                current_age_years=arguments["current_age_years"],
                current_age_months=arguments.get("current_age_months", 0),
                country=arguments["country"],
                sex=arguments.get("sex"),
                onetime_amount=arguments.get("onetime_amount"),
                monthly_amount=arguments.get("monthly_amount"),
                payout_age_years=arguments["payout_age_years"],
                payout_age_months=arguments.get("payout_age_months", 0),
                investment_type=arguments.get("investment_type", "XAU10Y"),
            )
            result = await call_tontinator(payload, client)
            if isinstance(result, str):
                return [types.TextContent(type="text", text=result)]

            text = format_single_result(
                result,
                investment_type=arguments.get("investment_type", "XAU10Y"),
            )
            return [types.TextContent(type="text", text=text)]

        if name == "compare_tontine_scenarios":
            scenarios = arguments["scenarios"]
            tasks = []
            for sc in scenarios:
                payload = build_payload(
                    current_age_years=sc["current_age_years"],
                    current_age_months=sc.get("current_age_months", 0),
                    country=sc["country"],
                    sex=sc.get("sex"),
                    onetime_amount=sc.get("onetime_amount"),
                    monthly_amount=sc.get("monthly_amount"),
                    payout_age_years=sc["payout_age_years"],
                    payout_age_months=sc.get("payout_age_months", 0),
                    investment_type=sc.get("investment_type", "BOL"),
                )
                tasks.append(call_tontinator(payload, client))

            raw_results = await asyncio.gather(*tasks)

            results_list = []
            for sc, raw in zip(scenarios, raw_results):
                label = sc.get("label", f"Age {sc['current_age_years']}, ${sc.get('onetime_amount', 0):,.0f}")
                inv = sc.get("investment_type", "BOL")
                if isinstance(raw, str):
                    results_list.append((label, {"error": raw}, inv))
                else:
                    results_list.append((label, raw, inv))

            text = format_comparison(results_list)
            return [types.TextContent(type="text", text=text)]

    return [types.TextContent(type="text", text=f"Unknown tool: {name}")]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def run_stdio():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def run_http(port: int):
    import uvicorn
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.routing import Route

    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request):
        async with sse.connect_sse(request.scope, request.receive, request._send) as (r, w):
            await app.run(r, w, app.create_initialization_options())

    async def handle_messages(request: Request):
        await sse.handle_post_message(request.scope, request.receive, request._send)

    starlette_app = Starlette(routes=[
        Route("/sse", endpoint=handle_sse),
        Route("/messages/", endpoint=handle_messages, methods=["POST"]),
    ])

    print(f"Tontine MCP server running on http://0.0.0.0:{port}")
    print(f"SSE endpoint: http://0.0.0.0:{port}/sse")
    uvicorn.run(starlette_app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tontine MCP Server")
    parser.add_argument("--http", action="store_true", help="Run as HTTP/SSE server (for claude.ai web)")
    parser.add_argument("--port", type=int, default=8000, help="Port for HTTP mode (default: 8000)")
    args = parser.parse_args()

    if args.http:
        run_http(args.port)
    else:
        asyncio.run(run_stdio())
