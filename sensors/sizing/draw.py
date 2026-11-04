"""Sizing lesson: draw sizing.html from the Corning valuation run and made-up ideas.

    .venv/bin/python -I sensors/sizing/draw.py
    .venv/bin/python -I sensors/sizing/test_sizing.py

No network. Keep the page on this computer, because it holds a Yahoo price.
Rules/sizing.md: whole method approved by the owner, Nov. 3, 2026.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
RUN = json.loads((ROOT / "sensors/valuation/runs/2026-11-03-01.json").read_text())
OUT = ROOT / "sizing.html"

PORTFOLIO = 100_000
LIMIT = 5.0
EQUAL = 20_000
COLS = [20, 30, 40, 50, 60, 70, 80, 90, 100]
GRADES = [("Strong", "score 8 to 10", 20.0), ("Middling", "score 5 to 7", 10.0), ("Thin", "score 3 to 4, or 5 and up with any 0", 5.0)]
CAP = {g[0]: g[2] for g in GRADES}

YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart/GLW?range=1d&interval=1d"
SRC_PRICE = f'<a href="{YAHOO}">close of Nov. 2, 2026, Yahoo through yfinance, fetched Nov. 2, 2026</a>'
SRC_RUN = "<code>sensors/valuation/runs/2026-11-03-01.md</code>, Nov. 3, 2026"


def round_up_loss(loss):
    return min(100, math.ceil(round(loss, 9) / 10) * 10)


def size_pct(cap, loss, limit=LIMIT):
    """Smaller of the cap and limit / loss, rounded down to 0.1% of the portfolio."""
    room = limit / round_up_loss(loss) * 100
    return math.floor(round(min(cap, room) * 10, 6)) / 10


def dollars(pct):
    return round(pct * PORTFOLIO / 100)


def usd(v):
    return f"${v:,.0f}"


base = RUN["base"]
PRICE = RUN["price"]["close"]
idea_c = {
    "name": "Corning", "real": True, "price": PRICE, "low": base["low"], "mid": base["mid"], "high": base["high"],
    "down": 0.0, "scores": [0, 1, 1, 1, 0], "grade": "Thin", "gated": True,
}
idea_a = {
    "name": "Made-up A", "real": False, "price": 50.0, "low": 18.0, "mid": 40.0, "high": 60.0,
    "down": 3.0, "scores": [2, 2, 2, 1, 2], "grade": "Strong", "gated": False,
}
idea_b = {
    "name": "Made-up B", "real": False, "price": 40.0, "low": 34.0, "mid": 38.0, "high": 42.0,
    "down": 2.0, "scores": [1, 2, 1, 2, 1], "grade": "Middling", "gated": False,
}
IDEAS = [idea_c, idea_a, idea_b]
for i in IDEAS:
    i["wrong"] = i["low"] - i["down"]
    i["loss"] = (i["price"] - i["wrong"]) / i["price"] * 100
    i["cover"] = i["mid"] / i["price"] * 100
    i["below"] = i["mid"] / 0.75
    i["score"] = sum(i["scores"])
    i["pct"] = 0.0 if i["gated"] else size_pct(CAP[i["grade"]], i["loss"])
    i["usd"] = dollars(i["pct"])
    i["lost"] = i["usd"] * i["loss"] / 100
    i["eq_lost"] = EQUAL * i["loss"] / 100

CASH = PORTFOLIO - sum(i["usd"] for i in IDEAS)
BOTH = sum(i["lost"] for i in IDEAS)
ZERO = sum(i["usd"] for i in IDEAS)
C_THIN = dollars(size_pct(CAP["Thin"], idea_c["loss"]))
C_THIN_LOST = C_THIN * idea_c["loss"] / 100
C_AT_BELOW = (idea_c["below"] - idea_c["wrong"]) / idea_c["below"] * 100
LIMIT_USD = PORTFOLIO * LIMIT / 100
DBL_LOST = idea_a["usd"] * 2 * (100 - idea_a["wrong"]) / 100
DBL_PORT = PORTFOLIO + idea_a["usd"]
DBL_SHARE = DBL_LOST / DBL_PORT * 100
PEAK = max(v for _, v in RUN["series"])
FALL = (1 - PRICE / PEAK) * 100
PAST_LOW = RUN["no_vote"][0]["low"]
RIVAL_LOW = RUN["no_vote"][1]["low"]


def alt(limit):
    a = dollars(size_pct(20.0, idea_a["loss"], limit))
    b = dollars(size_pct(10.0, idea_b["loss"], limit))
    return a, b, PORTFOLIO - a - b, a * idea_a["loss"] / 100, dollars(size_pct(20.0, 100, limit))


# ---------- word claims are tested before they are written ----------
assert idea_b["usd"] > idea_a["usd"] and idea_b["lost"] < idea_a["lost"]
assert idea_a["lost"] <= LIMIT_USD and idea_b["lost"] <= LIMIT_USD
assert idea_a["eq_lost"] > LIMIT_USD and idea_c["eq_lost"] > LIMIT_USD and idea_b["eq_lost"] < LIMIT_USD
assert idea_a["pct"] < CAP["Strong"] and idea_b["pct"] == CAP["Middling"]
assert idea_a["price"] < idea_a["below"] and idea_b["price"] < idea_b["below"] and PRICE > idea_c["below"]
assert idea_a["cover"] >= 75 and idea_b["cover"] >= 75 and idea_c["cover"] < 75
assert 8 <= idea_a["score"] <= 10 and 0 not in idea_a["scores"]
assert 5 <= idea_b["score"] <= 7 and 0 not in idea_b["scores"]
assert 0 in idea_c["scores"]
assert 0 < C_THIN_LOST <= LIMIT_USD


# ---------- grid ----------
def grid():
    head = "".join(f'<th class="n" scope="col">{c}%</th>' for c in COLS)
    rows = []
    for name, note, cap in GRADES:
        cells = []
        for c in COLS:
            pct = size_pct(cap, c)
            d = dollars(pct)
            by_cap = cap < LIMIT / c * 100
            mix = pct / 20 * 52
            mark = ""
            hit = ""
            for i in IDEAS:
                if not i["gated"] and i["grade"] == name and round_up_loss(i["loss"]) == c:
                    mark = f'<span class="pill">{i["name"]}</span>'
                    hit = " hit"
            who = f"the {name} cap sets it" if by_cap else f"5% ÷ {c}% sets it"
            cells.append(
                f'<td class="cell{hit}" style="--m:{mix:.0f}%" data-tip="&lt;b&gt;{name}, loss up to {c}%&lt;/b&gt;&lt;br&gt;{usd(d)} is {pct:.1f}% of the portfolio. {who.capitalize()}. '
                f'Lost if wrong at {c}%: {usd(d * c / 100)}.">{mark}<b>{usd(d)}</b><small>{pct:.1f}%{" · cap" if by_cap else ""}</small></td>'
            )
        rows.append(f'<tr><th scope="row">{name}<small>{note}<br>cap {cap:.0f}%</small></th>{"".join(cells)}</tr>')
    cells = []
    for c in COLS:
        mark = ""
        hit = ""
        if round_up_loss(idea_c["loss"]) == c:
            mark = '<span class="pill">Corning</span>'
            hit = " hit"
        cells.append(f'<td class="cell none{hit}" data-tip="&lt;b&gt;A gate failed&lt;/b&gt;&lt;br&gt;No position, whatever the loss.">{mark}<b>$0</b></td>')
    rows.append(f'<tr><th scope="row">No position<small>a gate failed, or score 0 to 2</small></th>{"".join(cells)}</tr>')
    return (
        '<div class="wrap"><table class="grid-t"><thead><tr><th scope="col">Thesis grade ↓<br>Loss if wrong, up to →</th>'
        f'{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
    )


# ---------- loss bars ----------
def bars():
    x0, w, xmax = 150, 730, EQUAL
    sx = lambda v: x0 + v / xmax * w
    top = 42
    gh = 76
    out, words = [], []
    for t in range(0, 20001, 5000):
        if t == LIMIT_USD:
            continue
        out.append(f'<line class="grid" x1="{sx(t):.1f}" x2="{sx(t):.1f}" y1="{top - 6}" y2="{top + gh * 3}"/>')
        out.append(f'<text class="ax" x="{sx(t):.1f}" y="{top + gh * 3 + 18}" text-anchor="middle">{usd(t)}</text>')
    for n, i in enumerate(IDEAS):
        y = top + n * gh + 8
        words.append(f'<text class="lv" x="{x0 - 12}" y="{y + 19}" text-anchor="end">{i["name"]}</text>')
        words.append(f'<text class="ax" x="{x0 - 12}" y="{y + 36}" text-anchor="end">falls {i["loss"]:.1f}%</text>')
        if i["usd"]:
            word = f'{usd(i["lost"])} on {usd(i["usd"])}'
            out.append(f'<rect class="b1" x="{x0}" y="{y}" width="{i["lost"] / xmax * w:.1f}" height="18" rx="3" data-tip="&lt;b&gt;{i["name"]}, this method&lt;/b&gt;&lt;br&gt;{usd(i["usd"])} × {i["loss"]:.1f}% = {usd(i["lost"])}. {i["lost"] / LIMIT_USD * 100:.0f}% of the limit."/>')
            words.append(f'<text class="lv halo" x="{max(sx(i["lost"]), sx(LIMIT_USD)) + 8:.1f}" y="{y + 14}">{word}</text>')
        else:
            words.append(f'<text class="lv halo" x="{sx(LIMIT_USD) + 8:.1f}" y="{y + 14}">$0: no position, the gates failed</text>')
        y2 = y + 24
        out.append(f'<rect class="b2" x="{x0 + 0.75}" y="{y2 + 0.75}" width="{i["eq_lost"] / xmax * w - 1.5:.1f}" height="16.5" rx="3" data-tip="&lt;b&gt;{i["name"]}, equal dollars&lt;/b&gt;&lt;br&gt;{usd(EQUAL)} × {i["loss"]:.1f}% = {usd(i["eq_lost"])}. {i["eq_lost"] / LIMIT_USD:.1f} times the limit."/>')
        words.append(f'<text class="lab halo" x="{max(sx(i["eq_lost"]), sx(LIMIT_USD)) + 8:.1f}" y="{y2 + 14}">{usd(i["eq_lost"])}</text>')
    lx = sx(LIMIT_USD)
    out.append(f'<line class="limit" x1="{lx:.1f}" x2="{lx:.1f}" y1="{top - 6}" y2="{top + gh * 3}"/>')
    out.append(f'<text class="lv" x="{lx:.1f}" y="{top - 14}" text-anchor="middle">Limit: {usd(LIMIT_USD)}</text>')
    out.append(f'<text class="lv" x="{lx:.1f}" y="{top + gh * 3 + 18}" text-anchor="middle">{usd(LIMIT_USD)}</text>')
    h = top + gh * 3 + 28
    label = (f"Loss if wrong against the {usd(LIMIT_USD)} limit. This method: "
             + ", ".join(f'{i["name"]} {usd(i["lost"])}' for i in IDEAS)
             + f". Equal {usd(EQUAL)} each: " + ", ".join(f'{i["name"]} {usd(i["eq_lost"])}' for i in IDEAS) + ".")
    return f'<svg viewBox="0 0 1000 {h}" role="img" aria-label="{label}">{"".join(out + words)}</svg>'


# ---------- portfolio bar ----------
def stack():
    x0, w = 10, 980
    parts = [("A", idea_a["usd"], "b1"), ("B", idea_b["usd"], "b3"), ("Cash", CASH, "b0")]
    out, x = [], x0
    for name, v, cls in parts:
        pw = v / PORTFOLIO * w
        out.append(f'<rect class="{cls}" x="{x + 1:.1f}" y="52" width="{pw - 2:.1f}" height="34" rx="3" data-tip="&lt;b&gt;{name}&lt;/b&gt;&lt;br&gt;{usd(v)}, {v / PORTFOLIO * 100:.1f}% of the portfolio."/>')
        out.append(f'<text class="lab" x="{x + 2:.1f}" y="22">{name}</text>')
        out.append(f'<text class="lv" x="{x + 2:.1f}" y="41">{usd(v)}</text>')
        x += pw
    label = f'Paper portfolio of {usd(PORTFOLIO)}: Made-up A {usd(idea_a["usd"])}, Made-up B {usd(idea_b["usd"])}, Corning $0, cash {usd(CASH)}.'
    return f'<svg class="stack" viewBox="0 0 1000 92" role="img" aria-label="{label}">{"".join(out)}</svg>'


# ---------- arithmetic ----------
def m(v):
    return f"${v:,.2f}"


def rows_arith():
    gate = {True: "fail all three", False: "pass all three"}
    capword = lambda i: "0% while gated" if i["gated"] else f'{CAP[i["grade"]]:.0f}%'
    room = lambda i: "not reached" if i["gated"] else f'5% ÷ {round_up_loss(i["loss"])}% = {LIMIT / round_up_loss(i["loss"]) * 100:.1f}%'
    setby = lambda i: "the gates" if i["gated"] else ("the cap" if CAP[i["grade"]] < LIMIT / round_up_loss(i["loss"]) * 100 else "the limit")
    defs = [
        ("Price", lambda i: m(i["price"])),
        ("Base low", lambda i: m(i["low"])),
        ("Base middle", lambda i: m(i["mid"])),
        ("Coverage, middle ÷ price (bar 75%)", lambda i: f'{i["cover"]:.1f}%'),
        ("Buy-below, middle ÷ 0.75", lambda i: m(i["below"])),
        ("Downside that stays if wrong", lambda i: m(i["down"]) if i["down"] else "none"),
        ("Value if wrong", lambda i: m(i["wrong"])),
        ("Loss if wrong, (price − value) ÷ price", lambda i: f'{i["loss"]:.1f}%'),
        ("Gates", lambda i: gate[i["gated"]]),
        ("Score, of 10", lambda i: f'{i["score"]}'),
        ("Grade", lambda i: f'{i["grade"]}, gated out' if i["gated"] else i["grade"]),
        ("Grade's cap", capword),
        ("Limit's room, 5% ÷ loss rounded up", room),
    ]
    body = "".join(
        f'<tr><th scope="row">{lab}</th>' + "".join(f'<td class="n">{fn(i)}</td>' for i in IDEAS) + "</tr>" for lab, fn in defs
    )
    body += '<tr class="total"><th scope="row">Size</th>' + "".join(f'<td class="n">{usd(i["usd"])}</td>' for i in IDEAS) + "</tr>"
    body += '<tr><th scope="row">Lost if wrong</th>' + "".join(f'<td class="n">{usd(i["lost"])}</td>' for i in IDEAS) + "</tr>"
    body += '<tr><th scope="row">What set the size</th>' + "".join(f'<td class="n">{setby(i)}</td>' for i in IDEAS) + "</tr>"
    return (
        '<div class="wrap narrow"><table><thead><tr><th scope="col">Step</th><th class="n" scope="col">Corning</th>'
        '<th class="n" scope="col">Made-up A<br><small>invented</small></th><th class="n" scope="col">Made-up B<br><small>invented</small></th></tr></thead>'
        f"<tbody>{body}</tbody></table></div>"
    )


TESTS = [
    ("Mechanism", "Thesis, Latest results, Cash flow", "Filings show every step, down to owner cash", "Filings show the cause, but one step rests on a target", "Filings do not show the cause"),
    ("Record", "Ten-year history, Normal earnings, Cash flow", "Normal earnings and deposit-out cash both grew over ten years", "One of them grew", "Neither grew"),
    ("Customers", "What customers say", "Three independent public sources, each on a different customer, confirm the claim the thesis rests on", "The sources exist but leave that claim open", "Fewer than three"),
    ("Kill lines", "Thesis, kill criteria", "Every claim has a line with a threshold and a date, a filing can settle it, and none is crossed", "Lines exist, but a claim has none or a line rests on someone's word", "No lines, or one is crossed"),
    ("Unknowns", "Thesis, \"we simply do not know\"", "No fact that would settle the case is missing", "One is missing, and it would not change the decision", "A fact that would change the decision is missing"),
]
WHY = [
    "Your ruling: the engine is not shown, and no filing read shows today's growth comes from scarcity and long deals (Journal, Nov. 3, 2026).",
    "Normalized EPS rose from $1.16 to $1.77 from FY2016 to FY2025 (calc., <code>normal.html</code>, Nov. 3, 2026). Free cash flow stayed flat at $1,407M to $1,413M (calc., <code>priced-in.html</code>, Nov. 3, 2026).",
    "Seven public voices, but none gives a fiber price or says how firm the deals are (Corning note, What customers say, gathered Nov. 3, 2026).",
    "Nine lines and none crossed, but claims C6 and C8 have no line (<code>Research/2026-11-03 Corning kill criteria.md</code>, Nov. 3, 2026).",
    "How firm the deals are and what price they carry are not in the vault (<code>Research/2026-11-03 Corning thesis note.md</code>, Nov. 3, 2026).",
]


def rubric():
    body = "".join(
        f'<tr><th scope="row">{t[0]}<small>{t[1]}</small></th><td>{t[2]}</td><td>{t[3]}</td><td>{t[4]}</td></tr>' for t in TESTS
    )
    return f'<div class="wrap"><table class="rub"><thead><tr><th scope="col">Test, and where in the note</th><th scope="col">2</th><th scope="col">1</th><th scope="col">0</th></tr></thead><tbody>{body}</tbody></table></div>'


def scores():
    body = ""
    for n, t in enumerate(TESTS):
        body += (f'<tr><th scope="row">{t[0]}</th><td class="n">{idea_c["scores"][n]}</td><td class="wy">{WHY[n]}</td>'
                 f'<td class="n">{idea_a["scores"][n]}</td><td class="n">{idea_b["scores"][n]}</td></tr>')
    body += (f'<tr class="total"><th scope="row">Total</th><td class="n">{idea_c["score"]}</td><td class="wy">Two zeros cap it at Thin. The gates still give no position.</td>'
             f'<td class="n">{idea_a["score"]}</td><td class="n">{idea_b["score"]}</td></tr>')
    return ('<div class="wrap"><table><thead><tr><th scope="col">Test</th><th class="n" scope="col">Corning</th><th scope="col">Evidence for Corning</th>'
            f'<th class="n" scope="col">A<br><small>invented</small></th><th class="n" scope="col">B<br><small>invented</small></th></tr></thead><tbody>{body}</tbody></table></div>')


def portfolio_table():
    rows = ""
    for i in IDEAS:
        share = "none" if not i["usd"] else f'{i["lost"] / LIMIT_USD * 100:.0f}%'
        rows += (f'<tr><th scope="row">{i["name"]}</th><td class="n">{usd(i["usd"])}</td><td class="n">{i["pct"]:.1f}%</td>'
                 f'<td class="n">{usd(i["lost"])}</td><td class="n">{share}</td></tr>')
    rows += f'<tr><th scope="row">Cash</th><td class="n">{usd(CASH)}</td><td class="n">{CASH / PORTFOLIO * 100:.1f}%</td><td class="n"></td><td class="n"></td></tr>'
    rows += f'<tr class="total"><th scope="row">Total</th><td class="n">{usd(PORTFOLIO)}</td><td class="n">100.0%</td><td class="n">{usd(BOTH)}</td><td class="n"></td></tr>'
    return ('<div class="wrap narrow"><table><thead><tr><th scope="col">Holding</th><th class="n" scope="col">Dollars</th><th class="n" scope="col">Share</th>'
            f'<th class="n" scope="col">Lost if wrong</th><th class="n" scope="col">Share of the {usd(LIMIT_USD)} limit</th></tr></thead><tbody>{rows}</tbody></table></div>')


def limit_table():
    rows = ""
    for lim in (3.0, 5.0, 8.0):
        a, b, cash, lost, floor = alt(lim)
        bold = ' class="total"' if lim == LIMIT else ""
        rows += (f'<tr{bold}><th scope="row">{lim:.0f}%{" (approved)" if lim == LIMIT else ""}</th><td class="n">{usd(a)}</td><td class="n">{usd(b)}</td><td class="n">{usd(cash)}</td>'
                 f'<td class="n">{usd(floor)}</td><td class="n">{(1 / (1 - lim / 100) - 1) * 100:.1f}%</td></tr>')
    return ('<div class="wrap narrow"><table><thead><tr><th scope="col">Limit</th><th class="n" scope="col">Made-up A</th><th class="n" scope="col">Made-up B</th><th class="n" scope="col">Cash</th>'
            f'<th class="n" scope="col">Size at a 100% loss, Strong</th><th class="n" scope="col">Gain that repairs a full-limit loss</th></tr></thead><tbody>{rows}</tbody></table></div>')


CSS = """
:root{color-scheme:light;--page:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink-2:#52514e;--muted:#6f6d68;--grid:#e1e0d9;--axis:#a9a89e;--border:rgba(11,11,11,.10);--link:#1c5cab;--s0:#8f8e85;--s1:#2a78d6;--s2:#eb6834;--tint2:rgba(42,120,214,.07)}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])){color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--ink:#f0efec;--ink-2:#c3c2b7;--muted:#a3a198;--grid:#2c2c2a;--axis:#5a5a55;--border:rgba(255,255,255,.10);--link:#7db2f0;--s0:#77766f;--s1:#3987e5;--s2:#d95926;--tint2:rgba(57,135,229,.11)}}
:root[data-theme="dark"]{color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--ink:#f0efec;--ink-2:#c3c2b7;--muted:#a3a198;--grid:#2c2c2a;--axis:#5a5a55;--border:rgba(255,255,255,.10);--link:#7db2f0;--s0:#77766f;--s1:#3987e5;--s2:#d95926;--tint2:rgba(57,135,229,.11)}
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1080px;margin:0 auto;padding:32px 16px 48px}
h1{font-size:26px;line-height:1.25;margin:0 0 8px;font-weight:650;text-wrap:balance}
h2{font-size:19px;margin:38px 0 6px;font-weight:650;text-wrap:balance}
p,ul.txt{margin:0 0 10px;max-width:75ch}ul.txt{padding-left:20px}ul.txt li{margin-bottom:6px}.lede{color:var(--ink-2)}
a{color:var(--link)}a:focus-visible{outline:2px solid var(--link);outline-offset:2px}
code{font-size:.92em}
.note{font-size:13.5px;color:var(--muted)}
.card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px;margin:12px 0}
.answer{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:14px 18px;margin:14px 0;max-width:80ch}.answer ul{margin:6px 0 0;padding-left:20px}.answer li{margin-bottom:5px}
.formula{font-size:17px;font-weight:600;margin:10px 0;max-width:none}
.legend{display:flex;flex-wrap:wrap;gap:4px 18px;margin:0 0 8px;padding:0;list-style:none;font-size:13.5px;color:var(--ink-2)}
.key{display:inline-block;width:14px;height:10px;margin-right:7px;border-radius:3px}
.k1{background:var(--s1)}.k2{border:1.5px solid var(--s0)}.k3{background:var(--s2)}.k0{background:var(--s0)}.kl{background:var(--ink);width:3px;height:14px;vertical-align:-2px;border-radius:0}
.scroll{overflow-x:auto}
svg{display:block;width:100%;min-width:640px;height:auto;font:13px system-ui,-apple-system,"Segoe UI",sans-serif}
svg text{fill:var(--ink-2)}svg .lv{fill:var(--ink);font-weight:650;font-variant-numeric:tabular-nums}svg .ax{fill:var(--muted)}svg .lab{fill:var(--ink-2)}
svg .halo{paint-order:stroke;stroke:var(--surface);stroke-width:4px;stroke-linejoin:round}
.grid{stroke:var(--grid);stroke-width:1}.limit{stroke:var(--ink);stroke-width:2}
.b1{fill:var(--s1)}.b3{fill:var(--s2)}.b0{fill:var(--s0)}.b2{fill:none;stroke:var(--s0);stroke-width:1.5}
rect[data-tip]{cursor:crosshair;pointer-events:all}
figure{margin:0}figcaption{margin-top:8px;color:var(--muted);font-size:13px;max-width:85ch}
#tip{position:fixed;z-index:5;pointer-events:none;background:var(--page);border:1px solid var(--border);border-radius:8px;padding:8px 10px;font-size:12.5px;max-width:290px;box-shadow:0 2px 10px rgba(0,0,0,.14)}#tip b{font-weight:650}
.wrap{overflow-x:auto;margin-top:10px}.wrap.narrow{max-width:820px}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{text-align:left;vertical-align:top;padding:7px 12px 7px 0;border-bottom:1px solid var(--border)}
thead th{border-bottom:1px solid var(--axis);font-weight:650;vertical-align:bottom}tbody th{font-weight:600}
th small,td small{display:block;font-weight:400;color:var(--muted);font-size:12px;line-height:1.35}
.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}thead .n{white-space:normal}
.wy{min-width:300px}.rub td{min-width:170px}.rub th{min-width:150px}
.total th,.total td{font-weight:650;border-top:1px solid var(--axis)}
.grid-t{min-width:900px;table-layout:fixed;border-collapse:separate;border-spacing:2px}
.grid-t th:first-child{width:150px}.grid-t thead th{border:0;padding:4px 6px 6px 0;font-size:13px}.grid-t tbody th{border:0;padding:8px 8px 8px 0}
.cell{border:0;border-radius:4px;padding:8px 4px;text-align:center;vertical-align:middle;background:color-mix(in srgb,var(--s1) var(--m),var(--surface));font-variant-numeric:tabular-nums;line-height:1.25;cursor:crosshair}
.cell b{display:block;font-weight:650;font-size:13.5px}.cell small{color:var(--ink-2);font-size:11.5px}
.cell.none{background:transparent;box-shadow:inset 0 0 0 1px var(--grid);color:var(--muted)}.cell.none b{font-weight:400}
.cell.hit{box-shadow:inset 0 0 0 2px var(--ink)}
.pill{display:block;font-size:11px;font-weight:650;color:var(--ink);margin-bottom:2px;white-space:nowrap}
footer{margin-top:36px;padding-top:12px;border-top:1px solid var(--border);color:var(--muted);font-size:13px}
"""

JS = """
const tip=document.getElementById('tip');
document.querySelectorAll('[data-tip]').forEach(el=>{
  el.addEventListener('mousemove',e=>{tip.innerHTML=el.dataset.tip;tip.hidden=false;
    const w=tip.offsetWidth,h=tip.offsetHeight;
    tip.style.left=Math.min(e.clientX+14,innerWidth-w-8)+'px';
    tip.style.top=Math.max(8,e.clientY-h-10)+'px';});
  el.addEventListener('mouseleave',()=>{tip.hidden=true});
});
"""

A, B, C = idea_a, idea_b, idea_c
a3, b3, c3, _, _ = alt(3.0)
a8, b8, c8, _, _ = alt(8.0)

PAGE = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Position Sizing Lesson</title>
<style>{CSS}</style></head><body><main>
<h1>Size by the thesis, then cap it by the loss</h1>
<p class="lede">The thesis sets how big you want to go. The loss sets how big you can afford to go. The smaller one wins, so a strong thesis never buys its way past the limit.</p>
<p class="note"><strong>A lesson, not advice.</strong> You approved the whole method on Nov. 3, 2026 (<code>Rules/sizing.md</code>). Corning stays no buy, and this page does not reopen that. A and B are invented, with invented numbers. The portfolio is paper. No holding is on file.</p>

<div class="answer"><strong>On {usd(PORTFOLIO)} of paper money</strong> (all calc.)
<ul>
<li><strong>Made-up B, middling thesis, small downside: {usd(B["usd"])}.</strong> It can lose {usd(B["lost"])}. The thesis cap sets the size.</li>
<li><strong>Made-up A, strong thesis, big downside: {usd(A["usd"])}.</strong> It can lose {usd(A["lost"])}. The limit sets the size, well under its {CAP["Strong"]:.0f}% cap.</li>
<li><strong>Corning as we studied it: $0.</strong> It fails all three gates. The sizing never starts.</li>
<li><strong>Cash: {usd(CASH)}.</strong> Two positions sit under the 5 that rule 2 asks for, and the method does not fill the gap.</li>
</ul></div>

<h2>The method</h2>
<p class="formula">Size = the smaller of the grade's cap and 5% ÷ loss if wrong</p>
<ul class="txt">
<li><strong>Gates first.</strong> A recorded thesis, your ruling that it survived the skeptic's review, and a price under the buy-below. Any "no" means $0.</li>
<li><strong>Grade from the note.</strong> Five tests, each 0, 1 or 2. The price enters none of them.</li>
<li><strong>Loss from the numbers.</strong> Value if wrong is base low, less any downside that still bites if the thesis is wrong. Loss is the fall from the price to that value.</li>
<li><strong>One hard limit.</strong> If the thesis is wrong, no position may lose more than 5% of the portfolio. Positions resting on one thesis share one limit, counted whole. They rest on one thesis if one named event would break both in the same direction (<code>overlap.html</code>).</li>
</ul>

<h2>The grid: thesis strength against downside</h2>
<p>Read a cell for the size on {usd(PORTFOLIO)}. Moving right, the limit shrinks the size. Moving down, the cap does. Round the loss up to the next column.</p>
<div class="card">{grid()}
<p class="note" style="margin:10px 0 0">Darker means bigger. "cap" marks a cell where the thesis cap sets the size. Elsewhere 5% ÷ loss sets it. An outline marks an idea. Hover for the sum. Sizes round down to 0.1% of the portfolio (calc.).</p></div>

<h2>Each idea's loss if wrong, against the limit</h2>
<p>Equal dollars would break the limit on two of the three ideas. {usd(EQUAL)} is the largest equal stake rule 2 allows, one position in 5. Made-up B stays under the limit at any size this method allows.</p>
<div class="card"><ul class="legend"><li><span class="key k1"></span>This method</li><li><span class="key k2"></span>Equal {usd(EQUAL)} each, for comparison</li><li><span class="key kl"></span>The limit</li></ul>
<figure><div class="scroll">{bars()}</div>
<figcaption>Dollars lost = position × loss if wrong (calc.). Corning's fall is from the {m(PRICE)} {SRC_PRICE} to base low {m(C["low"])} ({SRC_RUN}). A and B are invented.</figcaption></figure></div>

<h2>The paper portfolio and the cash</h2>
<div class="card"><ul class="legend"><li><span class="key k1"></span>A: made-up A</li><li><span class="key k3"></span>B: made-up B</li><li><span class="key k0"></span>Cash</li></ul>
<figure><div class="scroll">{stack()}</div>
<figcaption>Corning holds $0, so it has no segment.</figcaption></figure>
{portfolio_table()}
<p class="note" style="margin:10px 0 0">{usd(PORTFOLIO)} − {usd(A["usd"])} − {usd(B["usd"])} = {usd(CASH)} (calc.). If both positions are wrong, the loss is {usd(BOTH)}. If both go to zero, it is {usd(ZERO)}. Rule 4 asks for a cash reserve and sets no figure yet. You will set one next.</p></div>

<h2>The arithmetic</h2>
{rows_arith()}
<p class="note" style="margin-top:8px">Corning: {SRC_RUN}. Price: {SRC_PRICE}. A and B are invented. All sums calc.</p>
<ul class="txt">
<li><strong>Corning's loss is not a wild number.</strong> The price already fell {FALL:.0f}% from its {m(PEAK)} close on June 29, 2026 to {m(PRICE)} (calc., {SRC_PRICE}). The vault cannot say why (<code>Research/2026-11-03 Corning thesis note.md</code>, Nov. 3, 2026). Its lowest no-vote mark, own past multiples at {m(PAST_LOW)}, would still be a fall of {(1 - PAST_LOW / PRICE) * 100:.0f}% (calc., {SRC_RUN}).</li>
<li><strong>Corning with the gates ignored.</strong> The Thin cap would allow {usd(C_THIN)}, which loses {usd(C_THIN_LOST)} (calc.). That is a sum to learn from, not a size.</li>
<li><strong>Passing the bar does not make a small downside.</strong> At the {m(C["below"])} buy-below, Corning's fall to base low would still be {C_AT_BELOW:.1f}% (calc.).</li>
<li><strong>The downside that stays.</strong> Corning's only downside scenario, −$3.75, cuts the margin on added sales ({SRC_RUN}). If the thesis is wrong those sales are not there, so it is not subtracted. That is Claude's reading, for you to correct. A's and B's are invented ones that stay.</li>
</ul>

<h2>Grading the thesis from the note</h2>
<p>Each score links to evidence, Claude proposes it and you rule. A grade changes only on a dated event, never on a price move.</p>
{rubric()}
<p class="note" style="margin-top:8px">8 to 10 is Strong, cap 20%, one position in 5. 5 to 7 is Middling, cap 10%, one in 10. 3 to 4 is Thin, cap 5%, one in 20, and so is 5 or more with any 0. 0 to 2 is no position.</p>
<h3 style="font-size:15px;margin:18px 0 4px">The three scores</h3>
<p class="note">Corning's are Claude's reading, for you to correct. A's and B's are invented.</p>
{scores()}

<h2>What the limit does and does not do</h2>
<ul class="txt">
<li><strong>Why 5% is a judgment.</strong> No data here proves it. At a 100% loss it gives 5%, one position in 20, so it fits inside rule 2. A 5% loss takes a 5.3% gain to repair (calc.).</li>
<li><strong>It rests on an estimate.</strong> If the estimate is wrong and a position goes to zero, the loss is its whole size, at most {CAP["Strong"]:.0f}% of the portfolio. That takes a 25% gain to repair (calc.). The cap is what stops it going further.</li>
<li><strong>It covers one failure, not all of them.</strong> Ten positions all failing at the limit would lose 50% (calc.). In early 2020 the typical random portfolio fell about 40% at every size (calc., <code>concentration.html</code>, Nov. 3, 2026). A market fall is not a failed thesis, and the limit does not cover it.</li>
<li><strong>It never forces a sale.</strong> At a buy it is absolute. After a buy, a break means an alert and no adds. Selling stays with <code>when-to-trim</code> and a broken thesis.</li>
</ul>
{limit_table()}
<p class="note" style="margin-top:8px">B does not move, because its cap sets its size at all three limits (calc.).</p>

<h2>What you decided, Nov. 3, 2026</h2>
<ul class="txt">
<li>The limit is 5%. The caps are 20%, 10% and 5%.</li>
<li>A rise through the limit only alerts you. So if A doubled to $100, a fall to its $15 value if wrong would lose {usd(DBL_LOST)}, or {DBL_SHARE:.1f}% of a {usd(DBL_PORT)} portfolio (calc.). Below its trim-above, no sale is allowed.</li>
<li>Rule 4's reserve figure, open on this list at first, was set the same day: <code>Rules/cash.md</code>.</li>
</ul>

<footer>Built Nov. 3, 2026 by <code>sensors/sizing/draw.py</code>, checked by <code>test_sizing.py</code>. Keep this page on this computer: it holds a Yahoo price. Method: <code>Rules/sizing.md</code>.</footer>
<div id="tip" hidden></div>
<script>{JS}</script>
</main></body></html>
"""

OUT.write_text(PAGE)
print(f"wrote {OUT.name}: A {usd(A['usd'])}, B {usd(B['usd'])}, Corning {usd(C['usd'])}, cash {usd(CASH)}, peak {PEAK}, fall {FALL:.1f}, past {PAST_LOW:.2f}")
