"""Tontine MCP — educational content and investment type definitions."""

INVESTMENT_TYPE_DESCRIPTIONS = {
    "XAU5Y": {
        "label": "Gold Extra",
        "risk": "Aggressive",
        "description": (
            "Uses the past 5-year gold CAGR as the basis for distributions. "
            "Higher near-term payouts, more responsive to recent gold price movements. "
            "Greater variability: if real future CAGR falls short of the recent 5-year run, "
            "late-life payouts may be lower than projected."
        ),
    },
    "XAU10Y": {
        "label": "Gold Standard",
        "risk": "Balanced (default)",
        "description": (
            "Uses the past 10-year gold CAGR. Balanced approach between near-term income "
            "and long-term stability. Moderate variability — a sensible middle ground "
            "for most members."
        ),
    },
    "XAU20Y": {
        "label": "Gold Reserve",
        "risk": "Conservative",
        "description": (
            "Uses the past 20-year gold CAGR (most conservative). Lower initial distributions "
            "but more gradual and stable adjustment over time. If actual CAGR exceeds the "
            "20-year historical average, late-life payouts grow larger."
        ),
    },
    "BTC": {
        "label": "Bitcoin",
        "risk": "Very High Risk / Very High Potential",
        "description": (
            "Full Bitcoin allocation. Very high risk, very high potential return. "
            "For members with strong conviction in Bitcoin's long-term appreciation "
            "and a high risk tolerance."
        ),
    },
    "BOL": {
        "label": "Bold",
        "risk": "High Risk / Blended",
        "description": (
            "Blended portfolio of 65% gold and 35% Bitcoin — balancing gold's "
            "long-term stability with Bitcoin's upside potential."
        ),
    },
}

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

TOOLS_METADATA = [
    {
        "name": "get_tontine_info",
        "description": (
            "Get background information about Tontine Trust: what it is, how it compares to annuities, "
            "how mortality credits work, the available investment/distribution profiles, and how "
            "member assets are protected."
        ),
        "params": "topic: overview | vs_annuity | mortality_credits | distribution_profiles | trust_security | all",
    },
    {
        "name": "calculate_tontine_payout",
        "description": (
            "Calculate lifetime income projections using the Tontinator API. Returns monthly payout "
            "amounts for a tontine vs an annuity at key age milestones (+0, +5, +10, +15, +20 years "
            "from payout start). Includes a 'key insight' note on payout growth and annuity comparison."
        ),
        "params": "current_age_years, country (ISO 3166-1 alpha-3), sex, onetime_amount, payout_age_years, investment_type",
    },
    {
        "name": "compare_tontine_scenarios",
        "description": (
            "Compare 2–4 tontine scenarios side-by-side. Useful for 'retire at 70 vs 80', "
            "'$300k vs $500k', or comparing investment types. Runs all scenarios in parallel."
        ),
        "params": "scenarios[]: array of calculation requests, each with a label",
    },
    {
        "name": "get_investment_types",
        "description": (
            "List all available investment allocation types with descriptions. "
            "Call this when the user asks about investment options before recommending one."
        ),
        "params": "(none)",
    },
]
