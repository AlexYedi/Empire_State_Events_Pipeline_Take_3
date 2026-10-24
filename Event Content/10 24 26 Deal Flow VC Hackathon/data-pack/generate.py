#!/usr/bin/env python3
"""Synthetic LP-reporting data pack for the Deal Flow VC Hackathon (2026-10-24).

EVERYTHING HERE IS FICTIONAL. Fund, GPs, LPs, companies and founders are invented;
email domains use the reserved `.example` TLD (RFC 2606). Any resemblance to a real
company or person is coincidental.

Deterministic and idempotent: stdlib only, fixed seed, no clock reads, no network.
Re-running deletes and rewrites every generated path, byte-for-byte identical.

    python3 generate.py

How spans work: update templates mark every value-bearing substring as
[[key|shown text]]. `render()` strips the markers and records the exact character
offsets of each shown text in the final file, so the answer key's spans are
correct by construction (and `eval/check_answer_key.py` re-asserts them).
Offsets are Python str indices (Unicode code points) into the UTF-8-decoded file.
"""

import csv
import datetime as dt
import json
import math
import os
import random
import re
import shutil
import textwrap

SEED = 20261024
ROOT = os.path.dirname(os.path.abspath(__file__))
GENERATED = ["fund", "updates", "answer_key", "schema", "eval/baseline_carry_forward.json", "README.md"]

NUMERIC_FIELDS = ["monthly_revenue", "arr", "monthly_burn", "cash", "runway_months", "headcount", "customers"]
TEXT_FIELDS = ["key_highlight", "key_risk"]
MONEY_FIELDS = {"monthly_revenue", "arr", "monthly_burn", "cash"}
FLAG_VOCAB = [
    "missing_update",        # no update received at all
    "no_numbers_reported",   # founder replied without metrics
    "low_runway",            # runway < 6 months
    "revenue_decline",       # monthly revenue down vs prior quarter
    "conflicting_figures",   # two different values for the same metric in one update
    "non_recurring_arr",     # "ARR" used for revenue that is not recurring
    "non_usd_currency",      # update reported in a currency other than USD
    "unit_inconsistency",    # mixed unit conventions (k / $K / thousands / m) in one update
]

# --------------------------------------------------------------------------- fund

FUND = {
    "name": "Halyard Ventures Fund I, L.P.",
    "fictional": True,
    "legal_form": "Delaware limited partnership",
    "general_partner_entity": "Halyard Ventures GP I, LLC",
    "management_company": "Halyard Ventures Management, LLC",
    "vintage_year": 2023,
    "first_close": "2023-02-15",
    "final_close": "2023-09-29",
    "total_commitments_usd": 40_000_000,
    "gp_commitment_usd": 400_000,
    "reporting_currency": "USD",
    "strategy": "Pre-seed and seed, US and EU, sector-agnostic with a B2B software tilt",
    "target_portfolio_size": 22,
    "term": "10 years from final close, plus two 1-year extensions",
    "investment_period_end": "2028-02-15",
    "management_fee": "2.0% per annum of total commitments during the investment period, charged quarterly in advance",
    "carried_interest": "20% over an 8% preferred return, European (whole-fund) waterfall",
    "general_partners": [
        {"name": "Theodora Halloway", "title": "Managing Partner", "email": "theodora@halyard.example"},
        {"name": "Marcus Penwright", "title": "General Partner", "email": "marcus@halyard.example"},
    ],
    "fund_administrator": "Brightledger Fund Services (fictional)",
    "auditor": "Corbel & Vane LLP (fictional)",
    "updates_inbox": "updates@halyard.example",
    "fx_assumption": {"pair": "EURUSD", "rate": 1.085, "as_of": "2026-09-30",
                      "note": "Fictional fixed rate for the demo. Use it only for USD roll-ups; extract EUR figures as EUR."},
}

LP_TYPES = ["Family Office", "Fund of Funds", "Endowment", "Foundation", "Individual", "Corporate", "Pension"]

# Portfolio. check/ownership/last_post define marks: mark = ownership x last post-money
# (or cost, or a discount, per method). All USD.
COMPANIES = [
    # id, name, slug, sector, stage, hq, founder, title, entry_date, check, own%, last_post, last_round_date, method
    ("C01", "Loomvale Systems", "loomvale", "Logistics software", "Seed", "New York, NY", "Mara Quillfeather", "CEO", "2023-05-18", 1_500_000, 7.5, 20_000_000, "2023-05-18", "Last round (post-money)"),
    ("C02", "Tidewright Labs", "tidewright", "Developer tools", "Seed", "Brooklyn, NY", "Jonah Tidewell", "CEO", "2023-03-09", 1_200_000, 6.0, 20_000_000, "2023-03-09", "Secondary transaction"),
    ("C03", "Ossmere Health", "ossmere", "Digital health", "Seed", "Boston, MA", "Priyanka Ossler", "CEO", "2023-08-22", 1_000_000, 5.0, 36_000_000, "2025-02-11", "Last round (post-money)"),
    ("C04", "Brackenfold", "brackenfold", "Climate analytics", "Pre-seed", "Denver, CO", "Wes Bracklund", "CEO", "2024-06-04", 600_000, 6.0, 10_000_000, "2024-06-04", "Cost"),
    ("C05", "Quarrytone AI", "quarrytone", "AI infrastructure", "Seed", "San Francisco, CA", "Ines Quarrow", "CEO", "2023-10-10", 1_250_000, 4.6, 52_000_000, "2025-09-30", "Last round (post-money)"),
    ("C06", "Murrelwick Robotics", "murrelwick", "Robotics", "Seed", "Pittsburgh, PA", "Teodor Murrelind", "CEO", "2024-01-23", 1_400_000, 5.2, 40_000_000, "2025-05-20", "Last round (post-money)"),
    ("C07", "Gantrell Dental Cloud", "gantrell", "Vertical SaaS (dental)", "Seed", "Austin, TX", "Dana Gantrell", "CEO", "2023-12-05", 1_100_000, 5.5, 30_000_000, "2025-01-14", "Last round (post-money)"),
    ("C08", "Corvellum Pay", "corvellum", "Fintech (B2B payments)", "Seed", "New York, NY", "Felix Corvellis", "CEO", "2024-02-27", 1_750_000, 6.0, 45_000_000, "2025-07-08", "Last round (post-money)"),
    ("C09", "Stillmote Studios", "stillmote", "Creator tools", "Pre-seed", "Los Angeles, CA", "June Stillmore", "CEO", "2024-03-19", 500_000, 5.0, 10_000_000, "2024-03-19", "Cost"),
    ("C10", "Vellstrom Data GmbH", "vellstrom", "Data infrastructure", "Seed", "Berlin, DE", "Katrin Vellstrom", "CEO", "2024-04-16", 1_000_000, 4.0, 30_000_000, "2025-03-03", "Last round (post-money)"),
    ("C11", "Kettleworn Commerce", "kettleworn", "E-commerce enablement", "Seed", "Chicago, IL", "Ravi Kettleby", "CEO", "2023-07-11", 900_000, 4.5, 24_000_000, "2024-11-12", "Last round (post-money)"),
    ("C12", "Halcyra Security", "halcyra", "Cybersecurity", "Seed", "New York, NY", "Odessa Halcyon", "CEO", "2023-06-20", 1_250_000, 5.0, 30_000_000, "2024-09-17", "Last round (post-money)"),
    ("C13", "Pebblequill Learning", "pebblequill", "Edtech", "Pre-seed", "Philadelphia, PA", "Bram Pebbleton", "CEO", "2023-11-02", 600_000, 6.0, 10_000_000, "2023-11-02", "Last round less 30% discount"),
    ("C14", "Wrenfield Cover", "wrenfield", "Insurtech", "Seed", "Hartford, CT", "Lena Wrenfield", "CEO", "2024-07-30", 1_000_000, 4.0, 32_000_000, "2025-04-22", "Last round (post-money)"),
    ("C15", "Dunmarsh Grid", "dunmarsh", "Energy software", "Seed", "Houston, TX", "Silas Dunmarsh", "CEO", "2024-03-12", 1_250_000, 5.0, 28_000_000, "2024-12-09", "Last round (post-money)"),
    ("C16", "Ashvane Legal", "ashvane", "Legal AI", "Seed", "New York, NY", "Noor Ashvane", "CEO", "2024-10-22", 1_000_000, 5.0, 26_000_000, "2025-06-17", "Last round (post-money)"),
    ("C17", "Velloway Mobility", "velloway", "Fleet software", "Pre-seed", "Detroit, MI", "Tomas Vellow", "CEO", "2024-08-06", 500_000, 5.0, 10_000_000, "2024-08-06", "Cost"),
    ("C18", "Thistlecrumb Foods", "thistlecrumb", "Consumer packaged goods", "Seed", "Portland, OR", "Hattie Thistlewood", "CEO", "2023-09-14", 1_000_000, 5.0, 22_000_000, "2024-05-28", "Last round (post-money)"),
    ("C19", "Marrowlight Bio", "marrowlight", "Biotech tools", "Pre-seed", "Cambridge, MA", "Elio Marrowby", "CEO", "2025-10-21", 750_000, 6.0, 12_500_000, "2025-10-21", "Cost"),
    ("C20", "Sorrel & Pike People", "sorrelpike", "HR software", "Seed", "Atlanta, GA", "Gemma Sorrel", "CEO", "2024-02-06", 1_000_000, 5.0, 24_000_000, "2025-01-29", "Last round (post-money)"),
    ("C21", "Lanternwick Agents", "lanternwick", "AI agents", "Pre-seed", "New York, NY", "Kit Lanternby", "CEO", "2026-01-13", 600_000, 5.0, 12_000_000, "2026-01-13", "Cost"),
    ("C22", "Cinderquay Games", "cinderquay", "Gaming", "Pre-seed", "Seattle, WA", "Rosalind Cinderby", "CEO", "2024-10-01", 500_000, 5.0, 10_000_000, "2024-10-01", "Cost"),
]
COLS = ["id", "name", "slug", "sector", "stage", "hq", "founder", "title", "entry_date", "check", "own", "last_post", "last_round_date", "method"]
CO = {row[0]: dict(zip(COLS, row)) for row in COMPANIES}

# Tidewright partial secondary in Q2 2026: 25% of the position sold.
SECONDARY = {"company": "C02", "date": "2026-05-28", "proceeds": 1_150_000, "cost_sold": 300_000, "own_after": 4.5, "mark": 3_450_000}

# Q3 2026 rounds the fund did not join (dilution + markup).
Q3_ROUNDS = {
    "C01": {"date": "2026-08-27", "size": 6_000_000, "post": 48_000_000},
    "C12": {"date": "2026-09-15", "size": 8_000_000, "post": 60_000_000},
}

# Operating metrics. (monthly_revenue, revenue_type, stated_arr, burn, cash, runway, headcount, customers, currency)
# stated_arr=None means ARR is derived as 12 x monthly_revenue for recurring revenue.
R, N, Z = "recurring", "non_recurring", "none"
Q2 = {
    "C01": (118_000, R, None, 165_000, 2_900_000, 18, 14, 41, "USD"),
    "C02": (96_400, R, None, 140_000, 3_100_000, 22, 12, 220, "USD"),
    "C03": (58_000, R, None, 190_000, 4_200_000, 22, 16, 9, "USD"),
    "C04": (14_500, R, None, 62_000, 1_450_000, 23, 5, 6, "USD"),
    "C05": (72_000, R, None, 210_000, 5_100_000, 24, 15, 18, "USD"),
    "C06": (35_000, N, None, 260_000, 3_800_000, 15, 21, 4, "USD"),
    "C07": (61_000, R, None, 55_000, 494_000, 9, 11, 87, "USD"),
    "C08": (168_000, R, None, 230_000, 4_600_000, 20, 22, 34, "USD"),
    "C09": (78_000, N, None, 45_000, 880_000, 20, 7, 11, "USD"),
    "C10": (31_200, R, None, 118_000, 2_780_000, 23, 13, 17, "EUR"),
    "C11": (83_000, R, None, 128_000, 2_040_000, 16, 10, 140, "USD"),
    "C12": (141_000, R, None, 260_000, 3_300_000, 13, 18, 26, "USD"),
    "C13": (22_400, R, None, 58_000, 1_120_000, 19, 6, 31, "USD"),
    "C14": (47_300, R, None, 175_000, 3_950_000, 22, 15, 2_140, "USD"),
    "C15": (39_000, R, None, 155_000, 4_400_000, 28, 13, 5, "USD"),
    "C16": (88_600, R, None, 150_000, 3_600_000, 24, 12, 37, "USD"),
    "C17": (18_200, R, None, 85_000, 1_300_000, 15, 8, 3, "USD"),
    "C18": (210_000, N, None, 120_000, 2_200_000, 18, 17, 410, "USD"),
    "C19": (0, Z, None, 95_000, 2_600_000, 27, 7, 0, "USD"),
    "C20": (64_800, R, None, 140_000, 2_900_000, 20, 14, 58, "USD"),
    "C21": (9_800, R, None, 70_000, 1_900_000, 27, 6, 4, "USD"),
    "C22": (31_000, N, None, 90_000, 1_500_000, 16, 9, 3_900, "USD"),
}
Q3 = {
    "C01": (141_500, R, 1_698_000, 172_000, 8_390_000, 48, 19, 52, "USD"),
    "C02": (112_900, R, None, 150_000, 2_665_000, 18, 13, 268, "USD"),
    "C03": (71_250, R, None, 205_000, 3_620_000, 18, 18, 11, "USD"),
    "C04": (19_800, R, None, 70_000, 1_240_000, 18, 6, 8, "USD"),
    "C05": None,  # replied "all good, will send numbers next week"
    "C06": None,  # no update at all
    "C07": (52_800, R, None, 68_000, 290_000, 4, 11, 74, "USD"),
    "C08": (192_400, R, None, 245_000, 3_900_000, 16, 25, 39, "USD"),
    "C09": (100_000, N, None, 52_000, 745_000, 14, 8, 14, "USD"),
    "C10": (38_500, R, None, 124_000, 2_412_000, 19, 14, 21, "EUR"),
    "C11": (91_700, R, None, 131_000, 1_650_000, 13, 11, 162, "USD"),
    "C12": (163_800, R, 1_970_000, 270_000, 10_480_000, 38, 23, 31, "USD"),
    "C13": (24_100, R, None, 60_000, 940_000, 15, 6, 33, "USD"),
    "C14": (55_900, R, None, 182_000, 3_400_000, 18, 16, 2_610, "USD"),
    "C15": (46_500, R, None, 160_000, 3_930_000, 24, 14, 6, "USD"),
    "C16": (109_300, R, None, 165_000, 3_130_000, 19, 14, 45, "USD"),
    "C17": (21_600, R, None, 88_000, 1_040_000, 12, 8, 4, "USD"),
    "C18": (236_000, N, None, 105_000, 1_885_000, 18, 17, 465, "USD"),
    "C19": (0, Z, None, 98_000, 2_310_000, 23, 8, 0, "USD"),
    "C20": (70_100, R, 841_000, 150_000, 2_450_000, 16, 15, 63, "USD"),
    "C21": (27_400, R, None, 95_000, 1_620_000, 17, 9, 11, "USD"),
    "C22": (44_500, N, None, 92_000, 1_220_000, 13, 10, 5_250, "USD"),
}
METRIC_KEYS = ["monthly_revenue", "revenue_type", "stated_arr", "monthly_burn", "cash", "runway_months", "headcount", "customers", "currency"]

CUSTOMER_LABEL = {
    "C01": "Paying customers (brokerages)", "C02": "Paying teams", "C03": "Clinic groups live", "C04": "Paying customers",
    "C05": "Paying customers", "C06": "Paid pilot customers", "C07": "Practices on platform", "C08": "Customers",
    "C09": "Brand clients", "C10": "Customers", "C11": "Merchants live", "C12": "Enterprise customers",
    "C13": "Schools", "C14": "Active policies", "C15": "Utility customers", "C16": "Law firms",
    "C17": "Fleet operators", "C18": "Retail doors", "C19": "Paying customers", "C20": "Customers",
    "C21": "Paying customers", "C22": "Paying users",
}

Q2_TEXT = {  # (highlight, risk) for the clean Q2 updates
    "C01": ("signed our first two enterprise brokerages on annual contracts", "sales cycle for enterprise brokerages is running 4-5 months"),
    "C02": ("crossed 200 paying teams on self-serve", "a well-funded competitor launched a free tier"),
    "C03": ("went live with our ninth clinic group", "payer reimbursement code for our remote-monitoring workflow is under review"),
    "C04": ("first municipal customer signed", "pilots take 6+ months to convert"),
    "C05": ("inference cost per request down 40% after the scheduler rewrite", "GPU capacity contracts renew in Q4 at higher prices"),
    "C06": ("fourth paid pilot started with a regional 3PL", "pilot-to-fleet conversion still unproven"),
    "C07": ("launched the imaging integration beta", "two mid-size practices gave churn notice"),
    "C08": ("processed our first month above $40M in payment volume", "sponsor bank renegotiation due in Q4"),
    "C09": ("booked our largest brand campaign to date", "revenue is lumpy and project-based"),
    "C10": ("signed our first DAX-listed customer pilot", "German enterprise procurement cycles are long"),
    "C11": ("launched the returns module", "two large merchants are evaluating in-house builds"),
    "C12": ("closed two enterprise logos in financial services", "SOC 2 Type II audit scheduled for Q3"),
    "C13": ("expanded to two new districts", "district budgets set in August could slip"),
    "C14": ("crossed 2,000 active policies", "reinsurance capacity renews in January"),
    "C15": ("fifth utility signed a 3-year contract", "utility procurement timelines are slow"),
    "C16": ("net revenue retention at 128%", "incumbent research vendors bundling drafting tools"),
    "C17": ("third fleet operator went live", "fleet electrification budgets are shifting"),
    "C18": ("entered a 120-store regional grocery chain", "promo spend is high in new doors"),
    "C19": ("assay hit target sensitivity on first design-partner samples", "lab hiring is slow"),
    "C20": ("launched payroll-sync integrations", "SMB churn ticked up to 2.1% monthly"),
    "C21": ("first four paying customers on the agent platform", "pricing model still being tested"),
    "C22": ("soft-launched in two test markets", "paid user acquisition costs are rising"),
}

# --------------------------------------------------------------------------- helpers

MARK = re.compile(r"\[\[([A-Za-z0-9_.@]+)\|(.*?)\]\]", re.S)


def render(src):
    """Strip [[key|text]] markers; return (text, {key: (start, end, quote)})."""
    out, spans, pos, n = [], {}, 0, 0
    for m in MARK.finditer(src):
        pre = src[pos:m.start()]
        out.append(pre)
        n += len(pre)
        key, quote = m.group(1), m.group(2)
        assert key not in spans, f"duplicate marker {key}"
        spans[key] = (n, n + len(quote), quote)
        out.append(quote)
        n += len(quote)
        pos = m.end()
    out.append(src[pos:])
    text = "".join(out)
    assert "[[" not in text and "]]" not in text, "unclosed marker"
    for start, end, quote in spans.values():
        assert text[start:end] == quote
    return text, spans


def doc(s):
    return textwrap.dedent(s).lstrip("\n")


def usd(v):
    return f"${v:,}"


def k(v, prefix="$", suffix="K"):
    """Exact thousands shorthand: 141500 -> $141.5K, 172000 -> $172K."""
    if v % 1000 == 0:
        return f"{prefix}{v // 1000}{suffix}"
    assert v % 100 == 0, v
    return f"{prefix}{v / 1000:.1f}{suffix}"


def mm(v, prefix="$", suffix="M"):
    """Exact millions shorthand with the fewest decimals that are lossless."""
    for d in (1, 2, 3):
        if v % (10 ** (6 - d)) == 0:
            return f"{prefix}{v / 1_000_000:.{d}f}{suffix}"
    raise AssertionError(v)


def eur_eu(v):
    """European formatting: 2412000 -> EUR 2.412.000 with a euro sign."""
    return "€" + f"{v:,}".replace(",", ".")


def eur_k_eu(v):
    """European decimal comma: 38500 -> euro 38,5k."""
    assert v % 100 == 0
    whole, frac = divmod(v, 1000)
    return f"€{whole},{frac // 100}k" if frac else f"€{whole}k"


def email_of(c):
    return c["founder"].split()[0].lower() + "@" + c["slug"] + ".example"


def header(c, date, subject):
    return (f"From: {c['founder']} <{email_of(c)}>\n"
            f"To: Halyard Ventures <updates@halyard.example>\n"
            f"Date: {date}\n"
            f"Subject: {subject}\n\n")


def metrics(table, cid):
    row = table[cid]
    return None if row is None else dict(zip(METRIC_KEYS, row))


# --------------------------------------------------------------------------- Q2 updates (clean)

def q2_update(cid, rng):
    c, m = CO[cid], metrics(Q2, cid)
    day = 6 + int(cid[1:]) % 12
    date = dt.date(2026, 7, day)
    hl, risk = Q2_TEXT[cid]
    eur = m["currency"] == "EUR"
    money = (lambda v: "€" + f"{v:,}") if eur else usd
    lines = []
    if m["revenue_type"] == Z:
        lines.append(f"- Revenue: [[monthly_revenue|{money(0)}]] (pre-revenue)")
    elif m["revenue_type"] == R:
        lines.append(f"- MRR (June): [[monthly_revenue|{money(m['monthly_revenue'])}]]")
        lines.append(f"- ARR: [[arr|{money(12 * m['monthly_revenue'])}]]")
    else:
        lines.append(f"- Revenue (June, non-recurring): [[monthly_revenue|{money(m['monthly_revenue'])}]]")
    lines += [
        f"- Monthly net burn: [[monthly_burn|{money(m['monthly_burn'])}]]",
        f"- Cash on hand (June 30): [[cash|{money(m['cash'])}]]",
        f"- Runway: [[runway_months|{m['runway_months']} months]]",
        f"- Headcount: [[headcount|{m['headcount']}]]",
        f"- {CUSTOMER_LABEL[cid]}: [[customers|{m['customers']:,}]]",
    ]
    greet = rng.choice(["Hi Halyard team,", "Hi Theodora and Marcus,", "Hello Halyard,"])
    cur_note = " All figures in EUR." if eur else ""
    src = (header(c, f"{['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][date.weekday()]}, {date.day:02d} Jul 2026 09:30:00 -0400", f"{c['name']} - Q2 2026 investor update")
           + f"{greet}\n\nHere is our Q2 2026 update. Key metrics as of June 30, 2026.{cur_note}\n\n"
           + "\n".join(lines)
           + f"\n\nHighlight: [[key_highlight|{hl}]].\nRisk we're watching: [[key_risk|{risk}]].\n\n"
           + f"Thanks,\n{c['founder'].split()[0]}\n")
    flags = [("non_usd_currency", "flag.non_usd_currency")] if eur else []
    if eur:
        src = src.replace("All figures in EUR.", "[[flag.non_usd_currency|All figures in EUR.]]")
    fname = f"{cid}_{c['slug']}_{date.isoformat()}.txt"
    return fname, src, flags, {"received_date": date.isoformat(), "channel": "email body", "status": "received"}


# --------------------------------------------------------------------------- Q3 updates (messy)
# Each returns (filename, marked source, flags[(flag, evidence_marker)], manifest extras, format label)

def q3_C01():  # (a) prose email, the clean demo company
    c, m = CO["C01"], metrics(Q3, "C01")
    src = header(c, "Tue, 06 Oct 2026 08:41:00 -0400", "Loomvale Q3 2026 investor update") + doc(f"""
        Hi all,

        Quick Q3 recap. Short version: best quarter we've had.

        We closed the seed extension in late August, [[key_highlight|$6M led by a new lead investor at a $48M post-money]], which takes cash on hand to [[cash|{mm(m['cash'])}]] at September 30. Net burn averaged [[monthly_burn|{k(m['monthly_burn'])}]] a month across the quarter, so runway is roughly [[runway_months|{m['runway_months']} months]] at current spend (we will step burn up as we hire).

        September MRR came in at [[monthly_revenue|{k(m['monthly_revenue'])}]], up from $118K in June, which puts ARR at [[arr|{mm(m['stated_arr'])}]]. We added 11 net new brokerages and now have [[customers|{m['customers']} paying customers]]. Team is [[headcount|{m['headcount']} people]] after five hires, mostly engineering.

        What keeps me up at night: [[key_risk|two of our top five customers renew in Q1 and one of them is being acquired]], so we are pushing to get multi-year paper signed before year end.

        Asks: intros to heads of operations at mid-market freight brokers (50-300 trucks).

        Thanks,
        Mara
        """)
    return "C01_loomvale_2026-10-06.txt", src, [], {"received_date": "2026-10-06", "channel": "email body"}, "(a) prose email"


def q3_C02():  # (b) tab-pasted table
    c, m = CO["C02"], metrics(Q3, "C02")
    src = header(c, "Fri, 09 Oct 2026 17:02:00 -0400", "Tidewright // Q3") + (
        "Hi all - Q3 metrics pasted straight from our sheet:\n\n"
        "Metric\tJul-26\tAug-26\tSep-26\n"
        f"MRR\t$101,200\t$106,750\t[[monthly_revenue|{usd(m['monthly_revenue'])}]]\n"
        f"Paying teams\t239\t251\t[[customers|{m['customers']}]]\n"
        f"Net burn\t$148,000\t$151,000\t[[monthly_burn|{usd(m['monthly_burn'])}]]\n"
        f"Ending cash\t$2,965,000\t$2,814,000\t[[cash|{usd(m['cash'])}]]\n"
        f"Headcount\t12\t13\t[[headcount|{m['headcount']}]]\n"
        f"Runway (mo)\t20\t19\t[[runway_months|{m['runway_months']}]]\n\n"
        "Two notes. Good: [[key_highlight|we launched the Enterprise tier and signed our first 3 enterprise contracts]]. "
        "Less good: [[key_risk|free-to-paid conversion slipped from 4.1% to 3.4% after the competitor's free tier]].\n\n"
        "Happy to walk through on a call.\nJonah\n")
    return "C02_tidewright_2026-10-09.txt", src, [], {"received_date": "2026-10-09", "channel": "email body"}, "(b) pasted table (tab-separated)"


def q3_C03():  # (c) deck export
    m = metrics(Q3, "C03")
    src = doc(f"""
        # Ossmere Health: Q3 2026 Investor Update
        _Exported from Google Slides, 14 slides. Speaker notes omitted._

        ## Slide 1: Title
        Ossmere Health. Remote monitoring for cardiology practices. Q3 2026.

        ## Slide 2: Agenda
        - Q3 at a glance
        - Product
        - Team
        - Financials
        - Risks and asks

        ## Slide 3: Q3 at a glance
        - Recurring revenue, September: [[monthly_revenue|{usd(m['monthly_revenue'])}]]
        - Clinic groups live: [[customers|{m['customers']}]] (+2 this quarter)
        - [[key_highlight|Signed a 40-clinic regional cardiology group, our largest contract to date]]

        ## Slide 5: Product
        - Shipped automated escalation for arrhythmia alerts
        - Median alert-to-clinician time down from 31 to 9 minutes

        ## Slide 7: Team
        - FTEs at quarter end: [[headcount|{m['headcount']}]]
        - Hired VP Clinical Operations

        ## Slide 11: Financials
        | | Q2 2026 | Q3 2026 |
        |---|---|---|
        | Monthly net burn | $190K | [[monthly_burn|{k(m['monthly_burn'])}]] |
        | Cash (end of quarter) | $4.20M | [[cash|{mm(m['cash'])}]] |
        | Runway | 22 mo | [[runway_months|{m['runway_months']} mo]] |

        ## Slide 13: Risks
        - [[key_risk|CMS proposed rule could cut the remote-monitoring reimbursement code by ~12% in 2027]]

        ## Slide 14: Asks
        - Intros to cardiology service-line leaders at health systems
        """)
    return "C03_ossmere_Q3-2026-deck-export.md", src, [], {"received_date": "2026-10-12", "channel": "email attachment (deck export)"}, "(c) deck export markdown"


def q3_C04():  # (d) bullet-only
    m = metrics(Q3, "C04")
    src = doc(f"""
        Brackenfold - Q3 '26 update

        - MRR [[monthly_revenue|{k(m['monthly_revenue'], prefix='')}]] (Jun: 14.5K)
        - [[customers|{m['customers']}]] paying customers (+2: a utility co-op and a muni)
        - net burn ~[[monthly_burn|{k(m['monthly_burn'], prefix='')}]]/mo
        - cash [[cash|{mm(m['cash'], prefix='')}]], runway ~[[runway_months|{m['runway_months']} mo]]
        - team [[headcount|{m['headcount']}]] (hired first AE)
        - win: [[key_highlight|first multi-year contract, 3 years with the co-op]]
        - watch: [[key_risk|two pilots stalled waiting on state grant disbursement]]
        - ask: intros to rural electric co-op GMs
        """)
    return "C04_brackenfold_2026-10-14.md", src, [], {"received_date": "2026-10-14", "channel": "email attachment"}, "(d) bullet-only update"


def q3_C05():  # (e) "all good, will send numbers next week"
    c = CO["C05"]
    src = header(c, "Sat, 17 Oct 2026 22:48:00 -0700", "Re: Halyard Q3 update request") + doc("""
        [[flag.no_numbers_reported|all good, will send numbers next week]]

        Sent from my phone

        > On Fri, Oct 16, 2026 at 10:02 AM, Halyard Ventures <updates@halyard.example> wrote:
        > Hi Ines, friendly reminder that Q3 updates were due October 16. A short
        > email with MRR, burn, cash, runway, headcount and customers is plenty.
        > Thanks! Theodora
        """)
    return "C05_quarrytone_2026-10-17.txt", src, [("no_numbers_reported", "flag.no_numbers_reported")], \
        {"received_date": "2026-10-17", "channel": "email reply"}, "(e) reply with no numbers"


def q3_C07():  # (g) quietly in trouble: upbeat prose, revenue down, runway in a footnote
    c, m = CO["C07"], metrics(Q3, "C07")
    src = header(c, "Thu, 15 Oct 2026 18:20:00 -0500", "Gantrell Q3 - foundation quarter, biggest pipeline yet") + doc(f"""
        Hi Halyard team,

        Q3 was a foundation-building quarter for us. We rebuilt onboarding end to end, shipped the imaging integration our largest DSO asked for, and the Q4 pipeline is the biggest it has ever been: [[key_highlight|three multi-location DSOs are in late-stage trials]].

        On the numbers, September MRR was [[monthly_revenue|{k(m['monthly_revenue'])}]] as [[flag.revenue_decline|we cleaned up some legacy accounts]], and we now serve [[customers|{m['customers']} practices]] after offboarding a handful of single-chair offices that were never a great fit. The team is steady at [[headcount|{m['headcount']}]]. We are investing in the DSO trials, so net burn ran about [[monthly_burn|{k(m['monthly_burn'])}/month]].

        Really excited about Q4. Would love 20 minutes with either of you in the next couple of weeks to talk through the DSO motion.

        Best,
        Dana

        --
        * Cash at 9/30: [[cash|{k(m['cash'])}]]; [[runway_months|~{m['runway_months']} months]] at current burn. [[key_risk|Exploring options incl. a bridge]].
        """)
    return "C07_gantrell_2026-10-15.txt", src, [("low_runway", "runway_months"), ("revenue_decline", "flag.revenue_decline")], \
        {"received_date": "2026-10-15", "channel": "email body"}, "(g) quietly in trouble (runway in footnote, revenue down)"


def q3_C08():  # (h) summary vs table conflict
    c, m = CO["C08"], metrics(Q3, "C08")
    src = header(c, "Wed, 07 Oct 2026 07:55:00 -0400", "Corvellum Pay | Q3 2026 update") + doc(f"""
        Hi Theodora, Marcus,

        Headline: [[flag.conflicting_figures|MRR crossed $210K]] in September (~$2.5M ARR) and payment volume hit a record $61M for the month. [[key_highlight|We went live with our first two construction-supply distributors on embedded payables]].

        Detail below, same table we send the board.

        | Metric | Q2 (Jun) | Q3 (Sep) |
        |---|---|---|
        | MRR | $168,000 | [[monthly_revenue|{usd(m['monthly_revenue'])}]] |
        | Net burn / mo | $230,000 | [[monthly_burn|{usd(m['monthly_burn'])}]] |
        | Cash | $4.60M | [[cash|{mm(m['cash'])}]] |
        | Runway (mo) | 20 | [[runway_months|{m['runway_months']}]] |
        | Headcount | 22 | [[headcount|{m['headcount']}]] |
        | Customers | 34 | [[customers|{m['customers']}]] |

        MRR in the table excludes one-time implementation fees ($18K in September).

        Risk: [[key_risk|our sponsor bank renegotiation slipped to Q1 and they are asking for a higher reserve]].

        Felix
        """)
    return "C08_corvellum_2026-10-07.txt", src, [("conflicting_figures", "flag.conflicting_figures")], \
        {"received_date": "2026-10-07", "channel": "email body"}, "(h) summary vs table conflict"


def q3_C09():  # (i) "ARR" for non-recurring project revenue, deck export
    m = metrics(Q3, "C09")
    src = doc(f"""
        # Stillmote Studios: Q3 2026
        _Deck export (PDF to markdown). 9 slides._

        ## Slide 1: Stillmote Studios
        AI-assisted video production for consumer brands.

        ## Slide 2: Highlights
        - [[flag.non_recurring_arr|ARR: $1.2M]] (September, annualized)
        - [[customers|{m['customers']}]] brand clients served (up from 11)
        - [[key_highlight|Two repeat clients booked Q4 holiday campaigns]]

        ## Slide 4: Revenue mix
        - 100% of Q3 revenue came from one-off brand campaign production projects
        - September billings: [[monthly_revenue|{k(m['monthly_revenue'])}]]
        - Average project size up 22% vs Q2

        ## Slide 6: Team and spend
        - Team of [[headcount|{m['headcount']}]] (hired a second producer)
        - Monthly net burn [[monthly_burn|{k(m['monthly_burn'])}]]
        - Cash [[cash|{k(m['cash'])}]], roughly [[runway_months|{m['runway_months']} months]] of runway

        ## Slide 8: Risks
        - [[key_risk|No contracted revenue beyond November; pipeline is project by project]]
        """)
    return "C09_stillmote_Q3-deck.md", src, [("non_recurring_arr", "flag.non_recurring_arr")], \
        {"received_date": "2026-10-13", "channel": "email attachment (deck export)"}, "(i) 'ARR' used for non-recurring revenue"


def q3_C10():  # (j) EUR with European number formatting, bullets
    m = metrics(Q3, "C10")
    src = doc(f"""
        Vellstrom Data - Q3 2026 Update [[flag.non_usd_currency|(all figures in EUR)]]

        - MRR: [[monthly_revenue|{eur_k_eu(m['monthly_revenue'])}]] (Juni: €31,2k)
        - Customers: [[customers|{m['customers']}]] (4 new, incl. one Mittelstand logistics group)
        - Burn: [[monthly_burn|{eur_eu(m['monthly_burn'])}]] / month
        - Cash: [[cash|{eur_eu(m['cash'])}]] (30.09.2026)
        - Runway: ~[[runway_months|{m['runway_months']} months]]
        - Team: [[headcount|{m['headcount']} FTE]]
        - Highlight: [[key_highlight|DAX-listed pilot converted to a paid 2-year contract]]
        - Risk: [[key_risk|EU AI Act documentation work is pulling two engineers off roadmap]]

        Viele Gruesse,
        Katrin
        """)
    return "C10_vellstrom_2026-10-08.md", src, [("non_usd_currency", "flag.non_usd_currency")], \
        {"received_date": "2026-10-08", "channel": "email attachment"}, "(j) EUR, European number formats"


def q3_C11():  # (j) mixed units: k, $K, m, thousands
    c, m = CO["C11"], metrics(Q3, "C11")
    src = header(c, "Mon, 12 Oct 2026 11:15:00 -0500", "Kettleworn | Q3 numbers") + doc(f"""
        Hey team - numbers below, pasted from the board pack.

        Sept MRR landed at [[monthly_revenue|{k(m['monthly_revenue'], prefix='', suffix='k')}]], cash is [[cash|{mm(m['cash'], prefix='', suffix='m')}]] and we're at [[runway_months|{m['runway_months']} months]] of runway on the current plan. [[customers|{m['customers']} merchants]] live, team of [[headcount|{m['headcount']}]].

        [[flag.unit_inconsistency|(all figures $K unless noted)]]
                         Jul      Aug      Sep
        MRR              86.1     88.9     [[monthly_revenue@alt1|91.7]]
        Net burn         129      130      [[monthly_burn|131]]
        GMV processed (thousands of orders)   412   431   448

        Best news of the quarter: [[key_highlight|returns module now attached to 38% of new merchants]].
        Watching: [[key_risk|our two largest merchants are piloting an in-house checkout build]].

        Ravi
        """)
    return "C11_kettleworn_2026-10-12.txt", src, [("unit_inconsistency", "flag.unit_inconsistency")], \
        {"received_date": "2026-10-12", "channel": "email body"}, "(j) mixed units (k / $K / m / thousands)"


def q3_C12():  # (a) prose
    c, m = CO["C12"], metrics(Q3, "C12")
    src = header(c, "Mon, 05 Oct 2026 10:03:00 -0400", "Halcyra Q3: seed-2 closed") + doc(f"""
        Theodora, Marcus, and the Halyard LP-facing crew,

        The big news first: [[key_highlight|we closed an $8M seed-2 at a $60M post-money on September 15]]. Thank you both for the references. Cash at quarter end was [[cash|{mm(m['cash'])}]], and with net burn around [[monthly_burn|{k(m['monthly_burn'])}]] per month we have about [[runway_months|{m['runway_months']} months]] of runway before the hiring plan kicks in.

        Commercially, we finished September at [[monthly_revenue|{k(m['monthly_revenue'])} MRR]] (roughly [[arr|{mm(m['stated_arr'])} ARR]]) across [[customers|{m['customers']} enterprise customers]]. We are [[headcount|{m['headcount']} people]] now.

        One thing to flag: [[key_risk|the SOC 2 Type II renewal audit slipped to November, and two enterprise deals are waiting on it]].

        Odessa
        """)
    return "C12_halcyra_2026-10-05.txt", src, [], {"received_date": "2026-10-05", "channel": "email body"}, "(a) prose email"


def q3_C13():  # (d) bullets
    m = metrics(Q3, "C13")
    src = doc(f"""
        PEBBLEQUILL // Q3 2026

        * MRR: [[monthly_revenue|{k(m['monthly_revenue'])}]]
        * Schools: [[customers|{m['customers']}]]
        * Burn: [[monthly_burn|{k(m['monthly_burn'])}]]/mo
        * Cash: [[cash|{k(m['cash'])}]]
        * Runway: [[runway_months|{m['runway_months']} months]]
        * Team: [[headcount|{m['headcount']}]] (no change)
        * Good: [[key_highlight|94% renewal rate on school-year contracts]]
        * Bad: [[key_risk|budget freezes in two pilot districts]]
        """)
    return "C13_pebblequill_2026-10-16.md", src, [], {"received_date": "2026-10-16", "channel": "email attachment"}, "(d) bullet-only update"


def q3_C14():  # (b) markdown pipe table in an email
    c, m = CO["C14"], metrics(Q3, "C14")
    src = header(c, "Tue, 13 Oct 2026 09:12:00 -0400", "Wrenfield Cover Q3 KPIs") + doc(f"""
        Hi Theodora, Marcus,

        Pasting our KPI table from the board deck, short commentary below.

        | KPI | Jun 2026 | Sep 2026 |
        |---|---|---|
        | Monthly revenue (fees + commission) | $47,300 | [[monthly_revenue|{usd(m['monthly_revenue'])}]] |
        | Active policies | 2,140 | [[customers|{m['customers']:,}]] |
        | Net burn / month | $175,000 | [[monthly_burn|{usd(m['monthly_burn'])}]] |
        | Cash | $3,950,000 | [[cash|{usd(m['cash'])}]] |
        | Runway (months) | 22 | [[runway_months|{m['runway_months']}]] |
        | FTEs | 15 | [[headcount|{m['headcount']}]] |

        Commentary: [[key_highlight|loss ratio improved to 54% on the renters book]]. On the risk side, [[key_risk|our reinsurance treaty renews January 1 and pricing is up across the market]].

        Lena
        """)
    return "C14_wrenfield_2026-10-13.txt", src, [], {"received_date": "2026-10-13", "channel": "email body"}, "(b) pasted table (markdown)"


def q3_C15():  # (c) deck export
    m = metrics(Q3, "C15")
    src = doc(f"""
        # DUNMARSH GRID | Q3 FY26 Investor Update
        _Exported from Keynote_

        ## Slide 1: Cover
        Dunmarsh Grid: interconnection-queue software for utilities

        ## Slide 2: KPIs
        | | Sep 2026 |
        |---|---|
        | MRR | [[monthly_revenue|{k(m['monthly_revenue'])}]] |
        | Utility customers | [[customers|{m['customers']}]] |
        | Headcount | [[headcount|{m['headcount']}]] |

        ## Slide 3: Wins
        - [[key_highlight|Sixth utility signed; first investor-owned utility]]

        ## Slide 9: Cash
        - Net burn: [[monthly_burn|{k(m['monthly_burn'])}]] / month
        - Cash: [[cash|{mm(m['cash'])}]]
        - Runway: [[runway_months|{m['runway_months']} months]]

        ## Slide 10: Risks
        - [[key_risk|FERC interconnection rule implementation dates keep moving]]
        """)
    return "C15_dunmarsh_Q3-FY26-deck.md", src, [], {"received_date": "2026-10-19", "channel": "email attachment (deck export)"}, "(c) deck export markdown"


def q3_C16():  # (a) prose
    c, m = CO["C16"], metrics(Q3, "C16")
    src = header(c, "Thu, 08 Oct 2026 13:44:00 -0400", "Ashvane - Q3") + doc(f"""
        Hi Halyard,

        We did [[monthly_revenue|{usd(m['monthly_revenue'])}]] in MRR in September, up about 23% on the quarter, with [[customers|{m['customers']} law firms]] now paying. The quarter's milestone: [[key_highlight|our first 200+ lawyer firm signed a firmwide license]].

        We hired two engineers, so headcount is [[headcount|{m['headcount']}]]. Net burn was ~[[monthly_burn|{k(m['monthly_burn'])}]] and we ended the quarter with [[cash|{mm(m['cash'])}]] in the bank, i.e. [[runway_months|{m['runway_months']} months]] of runway.

        The thing I'm watching: [[key_risk|a large research incumbent started bundling a competing drafting tool for free]].

        Noor
        """)
    return "C16_ashvane_2026-10-08.txt", src, [], {"received_date": "2026-10-08", "channel": "email body"}, "(a) prose email"


def q3_C17():  # (d) bullets
    m = metrics(Q3, "C17")
    src = doc(f"""
        velloway q3

        - usage revenue sept [[monthly_revenue|{k(m['monthly_revenue'])}]] (all recurring, per-vehicle monthly)
        - fleets: [[customers|{m['customers']}]]
        - burn [[monthly_burn|{k(m['monthly_burn'])}]]
        - cash [[cash|{mm(m['cash'])}]] / runway ~[[runway_months|{m['runway_months']}mo]]
        - ppl: [[headcount|{m['headcount']}]]
        - [[key_highlight|4th fleet live, 1,100 vehicles]]
        - [[key_risk|EV transition grants for fleets paused at the state level]]
        """)
    return "C17_velloway_2026-10-20.md", src, [], {"received_date": "2026-10-20", "channel": "email attachment"}, "(d) bullet-only update"


def q3_C18():  # (b) space-aligned pasted table
    c, m = CO["C18"], metrics(Q3, "C18")
    src = header(c, "Fri, 16 Oct 2026 08:00:00 -0700", "Thistlecrumb Q3 numbers") + doc(f"""
        Hi both, here's the quarter.

                           Q2 '26 (Jun)    Q3 '26 (Sep)
        Revenue (month)    $210,000        [[monthly_revenue|{usd(m['monthly_revenue'])}]]
        Retail doors       410             [[customers|{m['customers']}]]
        Net burn           $120,000        [[monthly_burn|{usd(m['monthly_burn'])}]]
        Cash               $2,200,000      [[cash|{usd(m['cash'])}]]
        Runway             18 mo           [[runway_months|{m['runway_months']} mo]]
        Team               17              [[headcount|{m['headcount']}]]

        Burn improved as gross margin moved to 41%. [[key_highlight|We added 55 doors with a regional grocery chain]]. Heads up: [[key_risk|slotting fees for the Q1 shelf reset will spike burn in January]].

        Hattie
        """)
    return "C18_thistlecrumb_2026-10-16.txt", src, [], {"received_date": "2026-10-16", "channel": "email body"}, "(b) pasted table (space-aligned)"


def q3_C19():  # (a) prose, pre-revenue
    c, m = CO["C19"], metrics(Q3, "C19")
    src = header(c, "Wed, 14 Oct 2026 16:30:00 -0400", "Marrowlight Bio Q3 update") + doc(f"""
        Dear Theodora and Marcus,

        Science first: [[key_highlight|the assay was validated on a second design partner's samples at target sensitivity]]. We remain [[monthly_revenue|pre-revenue]] with [[customers|no paying customers yet]], as planned; two design partners are working with us unpaid.

        We brought on a senior scientist (team of [[headcount|{m['headcount']}]]). Burn was [[monthly_burn|{k(m['monthly_burn'])}]] per month and cash at quarter end was [[cash|{mm(m['cash'])}]], giving [[runway_months|{m['runway_months']} months]] of runway.

        Main risk: [[key_risk|lead times on a key reagent doubled to 14 weeks]], which could push our next milestone by a month.

        Best regards,
        Elio
        """)
    return "C19_marrowlight_2026-10-14.txt", src, [], {"received_date": "2026-10-14", "channel": "email body"}, "(a) prose email"


def q3_C20():  # (c) deck export
    m = metrics(Q3, "C20")
    src = doc(f"""
        # Sorrel & Pike People: Quarterly Investor Update (Q3 2026)
        _Exported from Pitch.com_

        ## Slide 1: Q3 2026
        HR and payroll ops for 20-200 person companies

        ## Slide 2: The quarter in numbers
        - MRR [[monthly_revenue|{k(m['monthly_revenue'])}]], ARR [[arr|{k(m['stated_arr'])}]]
        - [[customers|{m['customers']}]] customers
        - [[headcount|{m['headcount']}]] team members

        ## Slide 4: What worked
        - [[key_highlight|Payroll-sync integrations drove 40% of new logos]]

        ## Slide 6: Runway
        - Net burn [[monthly_burn|{k(m['monthly_burn'])}]] / mo
        - Cash [[cash|{mm(m['cash'])}]]
        - [[runway_months|{m['runway_months']} months]] runway

        ## Slide 7: Risks
        - [[key_risk|SMB logo churn at 2.4% monthly, up from 2.1%]]
        """)
    return "C20_sorrelpike_Q3-update-deck.md", src, [], {"received_date": "2026-10-09", "channel": "email attachment (deck export)"}, "(c) deck export markdown"


def q3_C21():  # (a) prose
    c, m = CO["C21"], metrics(Q3, "C21")
    src = header(c, "Sun, 11 Oct 2026 21:10:00 -0400", "lanternwick q3 - self-serve worked") + doc(f"""
        hey Theodora + Marcus,

        Short one. [[key_highlight|MRR nearly tripled after the self-serve launch]]: we ended September at [[monthly_revenue|{k(m['monthly_revenue'])}]] MRR (vs $9.8K in June) across [[customers|{m['customers']} paying customers]].

        We hired three engineers, so we're [[headcount|{m['headcount']}]] now and burn went up to [[monthly_burn|{k(m['monthly_burn'])}]]/mo. Cash is [[cash|{mm(m['cash'])}]] which is [[runway_months|{m['runway_months']} months]] at this burn.

        Watching closely: [[key_risk|model API costs are 38% of revenue and rising with usage]].

        kit
        """)
    return "C21_lanternwick_2026-10-11.txt", src, [], {"received_date": "2026-10-11", "channel": "email body"}, "(a) prose email"


def q3_C22():  # (b) pasted table
    c, m = CO["C22"], metrics(Q3, "C22")
    src = header(c, "Tue, 20 Oct 2026 12:00:00 -0700", "Cinderquay Games - Q3") + doc(f"""
        Hi Halyard - table below (copied out of Notion so formatting may be off)

        Metric | June | September
        In-app purchase revenue (month) | $31,000 | [[monthly_revenue|{usd(m['monthly_revenue'])}]]
        Paying users | 3,900 | [[customers|{m['customers']:,}]]
        Net burn | $90,000 | [[monthly_burn|{usd(m['monthly_burn'])}]]
        Cash | $1,500,000 | [[cash|{usd(m['cash'])}]]
        Runway | 16 months | [[runway_months|{m['runway_months']} months]]
        Headcount | 9 | [[headcount|{m['headcount']}]]

        [[key_highlight|Soft-launch D30 retention came in at 14%]]. [[key_risk|One app store's platform fee change from January will cost us ~3 points of margin]].

        Rosalind
        """)
    return "C22_cinderquay_2026-10-20.txt", src, [], {"received_date": "2026-10-20", "channel": "email body"}, "(b) pasted table (pipe-separated)"


Q3_BUILDERS = {fn.__name__[3:]: fn for fn in [
    q3_C01, q3_C02, q3_C03, q3_C04, q3_C05, q3_C07, q3_C08, q3_C09, q3_C10, q3_C11,
    q3_C12, q3_C13, q3_C14, q3_C15, q3_C16, q3_C17, q3_C18, q3_C19, q3_C20, q3_C21, q3_C22]}

# --------------------------------------------------------------------------- answer key records

UNITS = {"monthly_revenue": "currency", "arr": "currency", "monthly_burn": "currency", "cash": "currency",
         "runway_months": "months", "headcount": "count", "customers": "count",
         "key_highlight": "text", "key_risk": "text"}


def periods(q):
    if q == "Q3":
        return {"monthly_revenue": "2026-09", "arr": "2026-09", "monthly_burn": "2026-Q3", "cash": "2026-09-30",
                "runway_months": "2026-09-30", "headcount": "2026-09-30", "customers": "2026-09-30",
                "key_highlight": "2026-Q3", "key_risk": "2026-Q3"}
    return {"monthly_revenue": "2026-06", "arr": "2026-06", "monthly_burn": "2026-Q2", "cash": "2026-06-30",
            "runway_months": "2026-06-30", "headcount": "2026-06-30", "customers": "2026-06-30",
            "key_highlight": "2026-Q2", "key_risk": "2026-Q2"}


def null_field(f):
    return {"value": None, "unit": UNITS[f], "currency": None, "period": None, "source_file": None,
            "source_span": None, "quote": None, "confidence": 1.0}


def span_obj(rel, sp):
    return {"source_file": rel, "source_span": {"start": sp[0], "end": sp[1]}, "quote": sp[2]}


def build_record(cid, q, rel, spans, m, flags, status):
    c = CO[cid]
    per = periods(q)
    fields = {}
    if m is None:
        for f in NUMERIC_FIELDS + TEXT_FIELDS:
            fields[f] = null_field(f)
        revenue_type = None
    else:
        revenue_type = m["revenue_type"]
        truth = {
            "monthly_revenue": m["monthly_revenue"],
            "arr": (m["stated_arr"] or 12 * m["monthly_revenue"]) if revenue_type == R else None,
            "monthly_burn": m["monthly_burn"], "cash": m["cash"], "runway_months": m["runway_months"],
            "headcount": m["headcount"], "customers": m["customers"],
        }
        for f in NUMERIC_FIELDS:
            v = truth[f]
            if v is None:
                assert f not in spans, (cid, q, f)
                fields[f] = null_field(f)
                continue
            rec = {"value": v, "unit": UNITS[f],
                   "currency": m["currency"] if f in MONEY_FIELDS else None, "period": per[f]}
            if f in spans:
                rec.update(span_obj(rel, spans[f]))
            elif f == "arr":  # recurring revenue, ARR not stated: derived from the MRR span
                rec.update(span_obj(rel, spans["monthly_revenue"]))
                rec["derivation"] = "12 x monthly_revenue (ARR not stated)"
            else:
                raise AssertionError(f"{cid} {q}: no span for {f}")
            rec["confidence"] = 1.0
            alts = sorted(key for key in spans if key.startswith(f + "@"))
            if alts:
                rec["alt_spans"] = [{"start": spans[a][0], "end": spans[a][1], "quote": spans[a][2]} for a in alts]
            if f == "customers":
                rec["note"] = CUSTOMER_LABEL[cid]
            fields[f] = rec
        for f in TEXT_FIELDS:
            sp = spans[f]
            fields[f] = {"value": sp[2], "unit": "text", "currency": None, "period": per[f],
                         **span_obj(rel, sp), "confidence": 1.0}
    flag_objs = []
    for flag, marker in flags:
        assert flag in FLAG_VOCAB
        if marker is None:
            flag_objs.append({"flag": flag, "source_file": None, "source_span": None, "quote": None})
        else:
            flag_objs.append({"flag": flag, **span_obj(rel, spans[marker])})
    return {"company_id": cid, "company": c["name"], "period": f"2026-{q}", "update_status": status,
            "source_file": rel, "revenue_type": revenue_type, "fields": fields, "flags": flag_objs}


# --------------------------------------------------------------------------- fund math

def quarters():
    out = []
    for y in (2023, 2024, 2025, 2026):
        for qn in (1, 2, 3, 4):
            if (y, qn) > (2026, 3):
                break
            end = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}[qn]
            out.append((f"{y}-Q{qn}", dt.date(y, *end)))
    return out


def quarter_of(date_str):
    d = dt.date.fromisoformat(date_str)
    return f"{d.year}-Q{(d.month - 1) // 3 + 1}"


def capital_account():
    inv = {}
    for c in CO.values():
        qq = quarter_of(c["entry_date"])
        inv[qq] = inv.get(qq, 0) + c["check"]
    rows, cash, cum_called, cum_dist = [], 0, 0, 0
    for qq, end in quarters():
        investments = inv.get(qq, 0)
        fees = 200_000
        expenses = 35_000 + (300_000 if qq == "2023-Q1" else 0)
        proceeds = SECONDARY["proceeds"] if qq == quarter_of(SECONDARY["date"]) else 0
        dist = proceeds
        need = investments + fees + expenses
        call = max(0, math.ceil((need + 250_000 - cash) / 100_000) * 100_000)
        cash += call - need + proceeds - dist
        cum_called += call
        cum_dist += dist
        rows.append({"quarter": qq, "quarter_end": end.isoformat(), "capital_called": call,
                     "investments": investments, "management_fees": fees, "fund_expenses": expenses,
                     "realized_proceeds": proceeds, "distributions": dist, "ending_fund_cash": cash,
                     "cumulative_called": cum_called, "cumulative_distributed": cum_dist,
                     "unfunded_commitment": FUND["total_commitments_usd"] - cum_called})
    return rows


def marks():
    out = []
    for cid, c in CO.items():
        cost = c["check"]
        own_q2, method = c["own"], c["method"]
        realized_cost = realized_proceeds = 0
        if method == "Cost":
            mark_q2 = cost
        elif method.startswith("Last round less"):
            mark_q2 = round(c["own"] / 100 * c["last_post"] * 0.7)
        elif method == "Secondary transaction":
            cost -= SECONDARY["cost_sold"]
            realized_cost, realized_proceeds = SECONDARY["cost_sold"], SECONDARY["proceeds"]
            own_q2, mark_q2 = SECONDARY["own_after"], SECONDARY["mark"]
        else:
            mark_q2 = round(c["own"] / 100 * c["last_post"])
        own_q3, mark_q3, method_q3 = own_q2, mark_q2, method
        last_post, last_date = c["last_post"], c["last_round_date"]
        if cid in Q3_ROUNDS:
            r = Q3_ROUNDS[cid]
            own_q3 = own_q2 * (1 - r["size"] / r["post"])
            mark_q3 = int(round(own_q3 / 100 * r["post"], -3))
            method_q3, last_post, last_date = "Last round (post-money)", r["post"], r["date"]
        out.append({"company_id": cid, "company": c["name"], "sector": c["sector"], "stage_at_entry": c["stage"],
                    "hq": c["hq"], "initial_investment_date": c["entry_date"], "last_round_date": last_date,
                    "last_round_post_money_usd": last_post, "cost_basis_usd": cost,
                    "realized_cost_usd": realized_cost, "realized_proceeds_usd": realized_proceeds,
                    "ownership_pct_q2_2026": round(own_q2, 4), "ownership_pct_q3_2026": round(own_q3, 4),
                    "mark_q2_2026_usd": mark_q2, "mark_q3_2026_usd": mark_q3,
                    "valuation_method_q2": method, "valuation_method_q3": method_q3})
    return out


def xirr(flows):
    d0 = flows[0][0]

    def npv(r):
        return sum(a / (1 + r) ** ((d - d0).days / 365.0) for d, a in flows)
    lo, hi = -0.99, 10.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if npv(mid) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def fund_metrics(ca, mk, q):
    upto = [r for r in ca if r["quarter"] <= q]
    row = upto[-1]
    mark_key = "mark_q2_2026_usd" if q == "2026-Q2" else "mark_q3_2026_usd"
    portfolio_fv = sum(m[mark_key] for m in mk)
    nav = portfolio_fv + row["ending_fund_cash"]
    paid_in, dist = row["cumulative_called"], row["cumulative_distributed"]
    flows = []
    for r in upto:
        d = dt.date.fromisoformat(r["quarter_end"])
        if r["capital_called"]:
            flows.append((d, -r["capital_called"]))
        if r["distributions"]:
            flows.append((d, r["distributions"]))
    flows.append((dt.date.fromisoformat(row["quarter_end"]), nav))
    cost = sum(m["cost_basis_usd"] for m in mk)
    return {"quarter": q, "as_of": row["quarter_end"], "total_commitments_usd": FUND["total_commitments_usd"],
            "paid_in_capital_usd": paid_in, "unfunded_commitment_usd": row["unfunded_commitment"],
            "cumulative_distributions_usd": dist, "portfolio_cost_basis_usd": cost,
            "portfolio_fair_value_usd": portfolio_fv, "fund_cash_usd": row["ending_fund_cash"], "nav_usd": nav,
            "tvpi": round((nav + dist) / paid_in, 2), "dpi": round(dist / paid_in, 2), "rvpi": round(nav / paid_in, 2),
            "gross_moic_on_invested": round((portfolio_fv + SECONDARY["proceeds"]) / (cost + SECONDARY["cost_sold"]), 2),
            "net_irr_estimate_pct": round(100 * xirr(flows), 1),
            "irr_method": "Since-inception XIRR on LP cash flows (calls negative, distributions positive) dated at quarter end, ending NAV as terminal value. Net of fees and expenses; no carried-interest accrual modeled."}


# --------------------------------------------------------------------------- LPs

def lps(rng):
    n, total, unit = 35, FUND["total_commitments_usd"] - FUND["gp_commitment_usd"], 50_000
    weights = [rng.paretovariate(1.6) for _ in range(n)]
    s = sum(weights)
    amts = [max(250_000, int(total * w / s / unit) * unit) for w in weights]
    amts[amts.index(max(amts))] += total - sum(amts)
    out = []
    for i, a in enumerate(amts, 1):
        t = LP_TYPES[rng.randrange(len(LP_TYPES))]
        out.append({"lp_id": f"LP-{i:02d}", "name": f"LP-{i:02d} {t}", "type": t, "commitment_usd": a,
                    "pct_of_fund": round(100 * a / FUND["total_commitments_usd"], 4)})
    out.append({"lp_id": "GP", "name": "Halyard Ventures GP I, LLC (GP commitment)", "type": "General Partner",
                "commitment_usd": FUND["gp_commitment_usd"],
                "pct_of_fund": round(100 * FUND["gp_commitment_usd"] / FUND["total_commitments_usd"], 4)})
    assert sum(x["commitment_usd"] for x in out) == FUND["total_commitments_usd"]
    return out


# --------------------------------------------------------------------------- writers

def write(rel, text):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def write_json(rel, obj):
    write(rel, json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def write_csv(rel, rows):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def money_short(v):
    return f"${v / 1_000_000:.2f}M"


def prior_report(fm, mk, ca, q2_key):
    q2row = next(r for r in ca if r["quarter"] == "2026-Q2")
    ytd = [r for r in ca if r["quarter"] in ("2026-Q1", "2026-Q2")]
    lines = [
        "# Halyard Ventures Fund I, L.P. — Quarterly Report to Limited Partners, Q2 2026",
        "",
        "_FICTIONAL. Synthetic data for the Deal Flow VC Hackathon. Period ended June 30, 2026. Unaudited. Prepared by the General Partner._",
        "",
        "## 1. Fund summary",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Total commitments | {usd(fm['total_commitments_usd'])} |",
        f"| Paid-in capital (cumulative) | {usd(fm['paid_in_capital_usd'])} ({100 * fm['paid_in_capital_usd'] / fm['total_commitments_usd']:.1f}% called) |",
        f"| Unfunded commitment | {usd(fm['unfunded_commitment_usd'])} |",
        f"| Cumulative distributions | {usd(fm['cumulative_distributions_usd'])} |",
        f"| Portfolio fair value | {usd(fm['portfolio_fair_value_usd'])} |",
        f"| Fund cash | {usd(fm['fund_cash_usd'])} |",
        f"| Net asset value (NAV) | {usd(fm['nav_usd'])} |",
        f"| TVPI | {fm['tvpi']:.2f}x |",
        f"| DPI | {fm['dpi']:.2f}x |",
        f"| RVPI | {fm['rvpi']:.2f}x |",
        f"| Net IRR (estimate) | {fm['net_irr_estimate_pct']:.1f}% |",
        "",
        "Net IRR is a since-inception estimate on LP cash flows dated at quarter end, with ending NAV as the terminal value; no carried-interest accrual is modeled.",
        "",
        "## 2. Capital account and fees (fund level)",
        "",
        "| | Q2 2026 | YTD 2026 | Inception to date |",
        "|---|---|---|---|",
        f"| Capital contributions | {usd(q2row['capital_called'])} | {usd(sum(r['capital_called'] for r in ytd))} | {usd(q2row['cumulative_called'])} |",
        f"| Distributions | {usd(q2row['distributions'])} | {usd(sum(r['distributions'] for r in ytd))} | {usd(q2row['cumulative_distributed'])} |",
        f"| Management fees | {usd(q2row['management_fees'])} | {usd(sum(r['management_fees'] for r in ytd))} | {usd(sum(r['management_fees'] for r in ca if r['quarter'] <= '2026-Q2'))} |",
        f"| Partnership expenses | {usd(q2row['fund_expenses'])} | {usd(sum(r['fund_expenses'] for r in ytd))} | {usd(sum(r['fund_expenses'] for r in ca if r['quarter'] <= '2026-Q2'))} |",
        "",
        f"Q2 distribution: {usd(SECONDARY['proceeds'])} from a partial secondary sale of Tidewright Labs (25% of the Fund's position, cost {usd(SECONDARY['cost_sold'])}), distributed pro rata on {SECONDARY['date']}.",
        "",
        "## 3. Portfolio",
        "",
        "| Company | Stage | Sector | Cost | Q2 2026 fair value | MOIC | Method | Q2 note |",
        "|---|---|---|---|---|---|---|---|",
    ]
    keyed = {r["company_id"]: r for r in q2_key["companies"]}
    for m in mk:
        hl = keyed[m["company_id"]]["fields"]["key_highlight"]["value"]
        moic = (m["mark_q2_2026_usd"] + m["realized_proceeds_usd"]) / (m["cost_basis_usd"] + m["realized_cost_usd"])
        lines.append(f"| {m['company']} | {m['stage_at_entry']} | {m['sector']} | {money_short(m['cost_basis_usd'] + m['realized_cost_usd'])} | "
                     f"{money_short(m['mark_q2_2026_usd'])} | {moic:.2f}x | {m['valuation_method_q2']} | {hl[0].upper() + hl[1:]}. |")
    lines += [
        "",
        "## 4. Letter from the General Partners",
        "",
        "Dear Limited Partners,",
        "",
        f"The Fund ended the second quarter with a NAV of {money_short(fm['nav_usd'])} and a TVPI of {fm['tvpi']:.2f}x on {money_short(fm['paid_in_capital_usd'])} of paid-in capital. "
        f"The quarter's notable event was the Fund's first distribution: we sold a quarter of our Tidewright Labs position in a secondary transaction at roughly 3.8x cost and returned {money_short(SECONDARY['proceeds'])} to you. "
        "We kept the rest of the position because the company's self-serve growth remains strong.",
        "",
        "Across the portfolio, revenue grew at most companies and the median company reports more than 18 months of runway. "
        "Two areas we are watching: Gantrell Dental Cloud gave us a heads-up on churn among smaller practices, and several companies flagged longer enterprise sales cycles. "
        "We expect two portfolio companies to raise priced rounds in the second half of the year.",
        "",
        "The Fund is 22 companies into a 22-company plan. Reserves are earmarked for follow-ons from 2027 onward.",
        "",
        "Thank you for your continued support.",
        "",
        "Theodora Halloway and Marcus Penwright",
        "General Partners, Halyard Ventures",
        "",
    ]
    return "\n".join(lines)


SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://halyard.example/schema/extracted_metrics.schema.json",
    "title": "Extracted metrics for one portfolio company, one quarter",
    "description": "FICTIONAL demo schema. One file per company (predictions dir) or a list under `companies` (answer key). Money values are whole units of `currency` (e.g. 141500, not 141.5). Offsets are Python str indices (Unicode code points) into the UTF-8-decoded source file, end-exclusive.",
    "type": "object",
    "required": ["company_id", "company", "period", "update_status", "source_file", "revenue_type", "fields", "flags"],
    "properties": {
        "company_id": {"type": "string", "pattern": "^C[0-9]{2}$"},
        "company": {"type": "string"},
        "period": {"type": "string", "examples": ["2026-Q3"]},
        "update_status": {"enum": ["received", "received_no_numbers", "not_received"]},
        "source_file": {"type": ["string", "null"], "description": "Path relative to the data-pack root."},
        "revenue_type": {"enum": ["recurring", "non_recurring", "none", None]},
        "fields": {
            "type": "object",
            "required": NUMERIC_FIELDS + TEXT_FIELDS,
            "properties": {f: {"$ref": "#/$defs/metric"} for f in NUMERIC_FIELDS + TEXT_FIELDS},
            "additionalProperties": False,
        },
        "flags": {"type": "array", "items": {"$ref": "#/$defs/flag"}},
    },
    "$defs": {
        "span": {
            "type": ["object", "null"],
            "required": ["start", "end"],
            "properties": {"start": {"type": "integer", "minimum": 0}, "end": {"type": "integer", "minimum": 0}},
        },
        "metric": {
            "type": "object",
            "required": ["value", "unit", "currency", "period", "source_file", "source_span", "quote", "confidence"],
            "properties": {
                "value": {"type": ["number", "string", "null"], "description": "Normalized value; null if not reported."},
                "unit": {"enum": ["currency", "months", "count", "text"]},
                "currency": {"enum": ["USD", "EUR", None], "description": "As reported. Do not convert."},
                "period": {"type": ["string", "null"], "examples": ["2026-09", "2026-Q3", "2026-09-30"]},
                "source_file": {"type": ["string", "null"]},
                "source_span": {"$ref": "#/$defs/span"},
                "quote": {"type": ["string", "null"], "description": "Must equal file_text[start:end]."},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "derivation": {"type": "string", "description": "Optional. How a value not stated verbatim was computed."},
                "alt_spans": {"type": "array", "description": "Optional (answer key). Other spans stating the same value."},
                "note": {"type": "string"},
            },
        },
        "flag": {
            "type": "object",
            "required": ["flag"],
            "properties": {
                "flag": {"enum": FLAG_VOCAB},
                "source_file": {"type": ["string", "null"]},
                "source_span": {"$ref": "#/$defs/span"},
                "quote": {"type": ["string", "null"]},
            },
        },
    },
}

ILPA_MAP = """# Field map: data pack to ILPA reporting sections

> **Approximate, verify against the ilpa.org template.** This map was written from general knowledge of the ILPA Reporting Template (capital account statement plus fees, expenses and carried interest schedule) and ILPA's performance-reporting guidance, without access to the current published files. Section and line names below are paraphrased, not quoted. Check the current template (ilpa.org, Reporting Template and Performance Template) before claiming ILPA alignment in front of judges.

## A. Capital account statement (fund level; per LP = fund level x `pct_of_fund`)

ILPA presents each line for the period (QTD), year to date and inception to date.

| ILPA-style line | Source in this pack | Notes |
|---|---|---|
| Beginning NAV | prior quarter NAV (`answer_key/q3_2026_fund_metrics.json` → `prior_quarter.nav_usd`) | Q2 NAV also in `fund/prior_report_Q2_2026.md` |
| Contributions | `fund/capital_account.csv` → `capital_called` | Per LP: multiply by `fund_profile.json` → `lps[].pct_of_fund / 100` |
| Distributions | `capital_account.csv` → `distributions` | Only Q2 2026 is non-zero (Tidewright secondary) |
| Management fees (gross) | `capital_account.csv` → `management_fees` | 2% of commitments, quarterly |
| Fee offsets / waivers | none in this fund | Report as 0 |
| Partnership expenses | `capital_account.csv` → `fund_expenses` | 2023-Q1 includes $300K organizational costs; not broken out by category (gap vs ILPA detail) |
| Realized gain / loss | `portfolio_marks.csv` → `realized_proceeds_usd - realized_cost_usd` | Tidewright only |
| Change in unrealized gain / loss | `portfolio_marks.csv` → `mark_q3_2026_usd - mark_q2_2026_usd` | Only Loomvale and Halcyra move in Q3 |
| Carried interest (accrued) | not modeled | State this explicitly in the report |
| Ending NAV | portfolio fair value + `ending_fund_cash` | |
| Unfunded commitment | `capital_account.csv` → `unfunded_commitment` | |

## B. Fees, expenses and carried interest schedule

| ILPA-style item | Source | Notes |
|---|---|---|
| Management fee, gross and net of offsets | `management_fees` | No offsets |
| Partnership expenses by category | `fund_expenses` (single line) | Category split not provided; flag as a known gap |
| Portfolio company fees (transaction, monitoring) | none | Report as 0 |
| Carried interest paid / accrued | not modeled | |

## C. Performance (fund level)

| Metric | Source | Notes |
|---|---|---|
| TVPI, DPI, RVPI | computed from `capital_account.csv` + marks | Expected Q3 values in `answer_key/q3_2026_fund_metrics.json` |
| Net IRR | XIRR on LP cash flows dated at quarter end, NAV as terminal value | Estimate; ILPA guidance prefers actual cash-flow dates |
| Gross IRR | not computed | Would need investment-level cash-flow dates |

## D. Portfolio company information (schedule of investments)

| Field | Source |
|---|---|
| Company, sector, HQ, stage at entry | `portfolio_marks.csv` |
| Initial investment date | `initial_investment_date` |
| Cost basis (remaining) / realized cost / realized proceeds | `cost_basis_usd`, `realized_cost_usd`, `realized_proceeds_usd` |
| Fair value (current, prior) | `mark_q3_2026_usd`, `mark_q2_2026_usd` |
| Ownership % (fully diluted, approximate) | `ownership_pct_q3_2026` |
| Valuation methodology | `valuation_method_q3` |
| Last round date / post-money | `last_round_date`, `last_round_post_money_usd` |

## E. Not ILPA template fields: company operating metrics

Founder-reported KPIs are not part of the ILPA capital account or fee templates. VC funds typically report them in the GP letter or a supplemental portfolio schedule. In this product they feed the GP narrative and the per-company table, each with a source span.

| Our field | Use in the LP report |
|---|---|
| `monthly_revenue`, `arr`, `revenue_type` | Portfolio table and narrative; never show `arr` for non-recurring revenue |
| `monthly_burn`, `cash`, `runway_months` | Risk section; `low_runway` drives a watch-list entry |
| `headcount`, `customers` | Portfolio table |
| `key_highlight`, `key_risk` | GP letter, one line per company |
| `flags` | Internal review queue before the report goes out; `missing_update` and `no_numbers_reported` become "update not received" rows |
| Currency (`EUR`) | Show as reported; convert for roll-ups with `fund_profile.json` → `fx_assumption` and say so |
"""


def readme(manifest, cases, fm3):
    tree = []
    for dirpath, dirnames, filenames in sorted(os.walk(ROOT)):
        dirnames.sort()
        rel = os.path.relpath(dirpath, ROOT)
        if "__pycache__" in rel:
            continue
        depth = 0 if rel == "." else rel.count(os.sep) + 1
        if rel != ".":
            tree.append("    " * (depth - 1) + os.path.basename(dirpath) + "/")
        for f in sorted(filenames):
            if f.endswith(".pyc") or f == ".DS_Store":
                continue
            tree.append("    " * depth + f)
    case_rows = "\n".join(f"| {c['case']} | {c['company']} (`{c['company_id']}`) | `{c['file'] or 'none (see manifest)'}` | {c['what']} |" for c in cases)
    fmt_rows = "\n".join(f"| `{m['company_id']}` | {m['company']} | {m['format'] or 'no update'} | `{m['file'] or '-'}` |" for m in manifest)
    tree.insert(0, "README.md")
    return f"""# Halyard Ventures Fund I: synthetic LP-reporting data pack

**Everything here is fictional.** Fund, GPs, LPs, companies and founders are invented; email domains use the reserved `.example` TLD. Any resemblance to a real company or person is coincidental. Built for the Deal Flow VC Hackathon (2026-10-24), LP-reporting track.

The product this pack feeds: messy founder updates → extracted metrics with source spans → reconciliation against last quarter → an ILPA-aligned quarterly LP report plus a GP narrative letter. Every number is one click from its source.

## Quick start

```bash
python3 generate.py                      # rebuilds everything below (deterministic, idempotent)
python3 eval/check_answer_key.py         # asserts every answer-key span equals its quote
python3 eval/score.py answer_key/q3_2026_metrics.json   # sanity: 100%
python3 eval/score.py path/to/your_predictions/          # your extractor, scored next to the carry-forward baseline
```

Stdlib Python 3 only. No network, no keys, no LLM calls.

## What's in the pack

| Path | What it is |
|---|---|
| `fund/fund_profile.json` | Fund terms, GPs, 35 LPs + GP commitment (`pct_of_fund` for per-LP capital accounts), FX assumption |
| `fund/capital_account.csv` | Fund-level calls, investments, fees, expenses, distributions, cash and unfunded, 2023-Q1 to 2026-Q3 |
| `fund/portfolio_marks.csv` | Per company: cost, realized, ownership, Q2 and Q3 2026 marks, valuation method, round dates |
| `fund/prior_report_Q2_2026.md` | Last quarter's LP report (NAV, TVPI, DPI, IRR, portfolio table, GP letter): the format to beat |
| `updates/Q2_2026/` | 22 clean Q2 founder updates (the "last quarter" side of the reconciliation) + `manifest.json` |
| `updates/Q3_2026/` | 21 messy Q3 founder updates (one company sent nothing) + `manifest.json` |
| `answer_key/q3_2026_metrics.json` | True Q3 values per company, each with file, char span and quote; expected flags |
| `answer_key/q2_2026_metrics.json` | Same for Q2 (source of the baseline and of "what moved") |
| `answer_key/q3_2026_fund_metrics.json` | Expected Q3 fund-level NAV, TVPI, DPI, RVPI, IRR and the Q2 comparison |
| `schema/extracted_metrics.schema.json` | JSON Schema for one company's extraction (every field = value, unit, currency, period, source_file, source_span, quote, confidence) |
| `schema/ilpa_field_map.md` | Our fields → ILPA reporting sections (approximate; verify against ilpa.org) |
| `eval/score.py` | Scores predictions vs the key, always next to the do-nothing baseline |
| `eval/baseline_carry_forward.json` | The baseline: Q2 values carried forward unchanged as the Q3 answer |
| `eval/check_answer_key.py` | Integrity test: spans, manifest, schema shape |

### File tree

```
{chr(10).join(tree)}
```

## Field definitions (the contract the scorer uses)

- `monthly_revenue`: latest month in the quarter (September for Q3). MRR when recurring, monthly billings when not. `0` for pre-revenue.
- `arr`: only for recurring revenue. The founder's stated ARR if given, else `12 x monthly_revenue` (marked `derivation` in the key, span = the MRR span). `null` for non-recurring revenue, even if the founder calls it ARR.
- `monthly_burn`: monthly net burn as reported. In a month-by-month table, the latest month.
- `cash`: cash at quarter end. `runway_months`: as stated by the founder (scorer allows ±0.5).
- `headcount`, `customers`: as of quarter end. `customers` means whatever the company counts (policies, doors, paying users); the key's `note` names it.
- Money is in whole units of the reported currency. Vellstrom reports in EUR: extract EUR, do not convert. `fund_profile.json` has a fixed FX rate for USD roll-ups.
- Spans are Python string indices (code points) into the UTF-8-decoded file, end-exclusive. `quote == text[start:end]`.
- `revenue_type`: `recurring` / `non_recurring` / `none`.
- Flags vocabulary: {", ".join(f"`{f}`" for f in FLAG_VOCAB)}.

## The messy cases and where each lives

| Case | Company | File | What to catch |
|---|---|---|---|
{case_rows}

### Format per company (Q3)

| ID | Company | Format | File |
|---|---|---|---|
{fmt_rows}

## Scoring

`eval/score.py` takes a predictions directory (one `<company_id>.json` per company, schema-shaped) or a single JSON file (`{{"companies": [...]}}`). It reports:

- **Field accuracy**: 7 numeric fields + `revenue_type` x 22 companies. Money within 1% and same currency; runway within 0.5 months; counts exact. A field whose true value is `null` (not reported) is correct only if you also return `null`: abstaining is scored, hallucinating is penalized.
- **Accuracy on reported fields** (truth non-null) and **abstention accuracy** (truth null), so nulls can't inflate the headline.
- **Flags**: micro precision, recall, F1 against the expected flags.
- **Traceback**: of the correctly valued reported fields, the share whose cited span is in the right file and overlaps the key's span.

Every number prints next to the **carry-forward baseline** (Q2 values copied unchanged). An accuracy figure without that column means nothing: the baseline already gets some fields right (headcount that didn't change, revenue type).

## Demo story: three companies

1. **Gantrell Dental Cloud (`C07`), the troubled one.** The email is upbeat ("biggest pipeline yet"). Revenue is down from $61K to $52.8K MRR, customers from 87 to 74, burn up, and the only place runway appears is a footnote under the signature: `~4 months`. The GP's Q3 mark still holds it at the last round ($1.65M). Show: `low_runway` + `revenue_decline` flags, each linked to its span, and the report's watch list. The judge line: a GP skimming 22 emails misses this one; the system doesn't.
2. **Corvellum Pay (`C08`), the conflicting one.** The headline says "MRR crossed $210K"; the board table says $192,400; a line under the table explains the gap (one-time implementation fees, $18K). Show: the `conflicting_figures` flag with both spans side by side, and the system choosing the table figure with the reason.
3. **Loomvale Systems (`C01`), the clean one.** Prose email, every metric present, a new round at a $48M post that drives the Q3 markup from $1.5M to $3.15M. Show the happy path end to end: extraction → reconcile vs Q2 (MRR +20%, headcount 14 → 19) → the company's line in the LP report → the mark change in the capital account.

Expected Q3 fund numbers (for checking your report): NAV {usd(fm3['nav_usd'])}, TVPI {fm3['tvpi']:.2f}x, DPI {fm3['dpi']:.2f}x, net IRR estimate {fm3['net_irr_estimate_pct']:.1f}%.

## Known simplifications

- Marks are set by formula (ownership x last post-money, cost, a 30% discount, or the secondary price); there is no independent valuation policy.
- Calls are sized to keep at least $250K of fund cash; no recallable distributions, no credit facility, no carry accrual.
- Gantrell's Q3 mark is deliberately stale (held at last round despite the update). That's a demo hook for "flag marks that the founder update contradicts", not an answer-key flag.
- One answer per field. Where a founder states a value twice consistently (Kettleworn MRR), the key lists the second mention in `alt_spans` and traceback accepts either.
"""


# --------------------------------------------------------------------------- main

def main():
    rng = random.Random(SEED)
    for rel in GENERATED:
        p = os.path.join(ROOT, rel)
        if os.path.isdir(p):
            shutil.rmtree(p)
        elif os.path.exists(p):
            os.remove(p)

    # Q2 updates + key
    q2_records, q2_manifest = [], []
    for cid in CO:
        fname, src, flags, extra = q2_update(cid, rng)
        text, spans = render(src)
        rel = f"updates/Q2_2026/{fname}"
        write(rel, text)
        q2_records.append(build_record(cid, "Q2", rel, spans, metrics(Q2, cid), flags, "received"))
        q2_manifest.append({"company_id": cid, "company": CO[cid]["name"], "file": rel,
                            "from": f"{CO[cid]['founder']} <{email_of(CO[cid])}>", **extra})
    write_json("updates/Q2_2026/manifest.json", {"period": "2026-Q2", "requested": "2026-07-01", "due": "2026-07-17", "updates": q2_manifest})
    q2_key = {"fund": FUND["name"], "period": "2026-Q2", "fictional": True, "companies": q2_records}
    write_json("answer_key/q2_2026_metrics.json", q2_key)

    # Q3 updates + key
    q3_records, q3_manifest, cases = [], [], []
    for cid in CO:
        c = CO[cid]
        if cid == "C06":
            q3_records.append(build_record(cid, "Q3", None, {}, None, [("missing_update", None)], "not_received"))
            q3_manifest.append({"company_id": cid, "company": c["name"], "file": None, "from": None, "received_date": None,
                                "channel": None, "status": "not_received",
                                "note": "No Q3 update received as of 2026-10-23. Requested 2026-10-02, reminder sent 2026-10-16."})
            fmt = None
            q3_manifest[-1]["format"] = fmt
            continue
        fname, src, flags, extra, fmt = Q3_BUILDERS[cid]()
        text, spans = render(src)
        rel = f"updates/Q3_2026/{fname}"
        write(rel, text)
        status = "received_no_numbers" if cid == "C05" else "received"
        q3_records.append(build_record(cid, "Q3", rel, spans, metrics(Q3, cid), flags, status))
        q3_manifest.append({"company_id": cid, "company": c["name"], "file": rel,
                            "from": f"{c['founder']} <{email_of(c)}>", **extra, "status": status, "format": fmt})
    # format labels live in the README, not in the inbox manifest the extractor sees
    readme_manifest = [{"company_id": m["company_id"], "company": m["company"], "file": m["file"], "format": m.pop("format")} for m in q3_manifest]
    write_json("updates/Q3_2026/manifest.json", {"period": "2026-Q3", "requested": "2026-10-02", "due": "2026-10-16",
                                                 "as_of": "2026-10-23", "updates": q3_manifest})
    q3_key = {"fund": FUND["name"], "period": "2026-Q3", "fictional": True,
              "notes": "True values. Money in whole units of `currency` as reported. Spans are code-point offsets into the UTF-8 file, end-exclusive.",
              "companies": q3_records}
    write_json("answer_key/q3_2026_metrics.json", q3_key)

    files = {m["company_id"]: m["file"] for m in readme_manifest}
    cases = [
        {"case": "(a) prose email, numbers in sentences", "company_id": "C01", "what": "Also C12, C16, C19, C21. Q2 numbers appear in the same sentences as distractors."},
        {"case": "(b) pasted table email", "company_id": "C02", "what": "Tab-separated sheet paste; take the Sep column. Also C14 (markdown), C18 (space-aligned), C22 (pipe text)."},
        {"case": "(c) deck export markdown", "company_id": "C03", "what": "Metrics spread across slide headings and a financials table. Also C15, C20."},
        {"case": "(d) bullet-only update", "company_id": "C04", "what": "Terse bullets, no currency symbols ('MRR 19.8K', 'cash 1.24M'). Also C13, C17."},
        {"case": "(e) 'all good, will send numbers next week'", "company_id": "C05", "what": "All fields null; flag `no_numbers_reported`. Don't carry Q2 forward as if reported."},
        {"case": "(f) no update at all", "company_id": "C06", "what": "Recorded in `updates/Q3_2026/manifest.json` as `not_received`; flag `missing_update`."},
        {"case": "(g) quietly in trouble", "company_id": "C07", "what": "Upbeat prose; revenue down vs Q2; cash and `~4 months` runway only in a footnote. Flags `low_runway`, `revenue_decline`."},
        {"case": "(h) summary vs table conflict", "company_id": "C08", "what": "Summary 'MRR crossed $210K' vs table $192,400 (gap = one-time fees, explained below the table). True MRR = table. Flag `conflicting_figures`."},
        {"case": "(i) 'ARR' for non-recurring revenue", "company_id": "C09", "what": "'ARR: $1.2M' but 100% project revenue. `arr` = null, `revenue_type` = non_recurring, flag `non_recurring_arr`."},
        {"case": "(j) units and currency", "company_id": "C10", "what": "EUR with European formats ('€38,5k', '€2.412.000'). Flag `non_usd_currency`. Units: C11 mixes '91.7k', '1.65m', a '$K' table and a 'thousands' row; flag `unit_inconsistency`."},
    ]
    for cs in cases:
        cs["company"] = CO[cs["company_id"]]["name"]
        cs["file"] = files[cs["company_id"]]

    # fund files
    profile = dict(FUND)
    profile["lps"] = lps(rng)
    profile["lp_count"] = sum(1 for x in profile["lps"] if x["lp_id"] != "GP")
    profile["portfolio"] = [{"company_id": c["id"], "company": c["name"], "sector": c["sector"], "stage_at_entry": c["stage"],
                             "hq": c["hq"], "founder": c["founder"], "founder_title": c["title"]} for c in CO.values()]
    write_json("fund/fund_profile.json", profile)
    ca = capital_account()
    write_csv("fund/capital_account.csv", ca)
    mk = marks()
    write_csv("fund/portfolio_marks.csv", mk)
    fm2 = fund_metrics(ca, mk, "2026-Q2")
    fm3 = fund_metrics(ca, mk, "2026-Q3")
    q3row = next(r for r in ca if r["quarter"] == "2026-Q3")
    fm3_out = dict(fm3)
    fm3_out["quarter_activity"] = {k2: q3row[k2] for k2 in ("capital_called", "investments", "management_fees", "fund_expenses", "realized_proceeds", "distributions")}
    fm3_out["unrealized_change_usd"] = sum(m["mark_q3_2026_usd"] - m["mark_q2_2026_usd"] for m in mk)
    fm3_out["marks_changed"] = [{"company_id": m["company_id"], "from": m["mark_q2_2026_usd"], "to": m["mark_q3_2026_usd"]}
                                for m in mk if m["mark_q3_2026_usd"] != m["mark_q2_2026_usd"]]
    fm3_out["prior_quarter"] = fm2
    write_json("answer_key/q3_2026_fund_metrics.json", fm3_out)
    write("fund/prior_report_Q2_2026.md", prior_report(fm2, mk, ca, q2_key))

    # schema + map
    write_json("schema/extracted_metrics.schema.json", SCHEMA)
    write("schema/ilpa_field_map.md", ILPA_MAP)

    # baseline: carry Q2 forward unchanged, relabeled as the Q3 answer
    base = []
    for r in json.loads(json.dumps(q2_records)):
        r["period"] = "2026-Q3"
        base.append(r)
    write_json("eval/baseline_carry_forward.json", {
        "description": "Do-nothing baseline: every company's Q2 2026 values and flags carried forward unchanged as the Q3 2026 answer. Spans point at the Q2 files.",
        "companies": base})

    write("README.md", readme(readme_manifest, cases, fm3))
    print(f"wrote data pack to {ROOT}")
    print(f"Q2 NAV {fm2['nav_usd']:,} TVPI {fm2['tvpi']} IRR {fm2['net_irr_estimate_pct']}% | "
          f"Q3 NAV {fm3['nav_usd']:,} TVPI {fm3['tvpi']} IRR {fm3['net_irr_estimate_pct']}%")


if __name__ == "__main__":
    main()
