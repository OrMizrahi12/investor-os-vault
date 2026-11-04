#!/usr/bin/env python3
"""Portfolio manager sums: one action per company, from Rules/sizing.md and Rules/cash.md.

    .venv/bin/python -I .claude/skills/portfolio-manager/scripts/pm.py INPUTS.json
    .venv/bin/python -I .claude/skills/portfolio-manager/scripts/pm.py INPUTS.json --json
    .venv/bin/python -I .claude/skills/portfolio-manager/scripts/pm.py INPUTS.json --portfolio "Portfolio/Paper portfolio.md"

Reads only. Writes no file, uses no network, places no order. Input shape: references/inputs.md.
Anything it cannot work out stays None and goes on the unsure list. It never estimates.
"""
import argparse
import json
import math
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
ACTIONS = ("buy", "add", "hold", "trim", "sell", "no position")
LIMIT = 5.0      # Rules/sizing.md, hard limit, % of portfolio
BAR = 0.75       # Rules/when-to-buy.md
RESERVE = 15.0   # Rules/cash.md, normal
FLOOR = 5.0      # Rules/cash.md, floor
TESTS = ("mechanism", "record", "customers", "kill_lines", "unknowns")
CAP = {"Strong": 20.0, "Middling": 10.0, "Thin": 5.0, "None": 0.0}
CLOSER = "The decision is yours."


def stop(msg):
    sys.exit(f"pm.py stopped: {msg}")


def floor_tenth(pct):
    """Round down to 0.1% of the portfolio. The inner round stops 7.1 becoming 7.0 on float noise."""
    return math.floor(round(pct * 10, 6)) / 10


def round_up_loss(loss_pct):
    """Round up to the next 10 points, the size grid in Rules/sizing.md."""
    return min(100, math.ceil(round(loss_pct, 9) / 10) * 10)


def grade_of(scores):
    if scores is None:
        return None, None
    for t in TESTS:
        if scores.get(t) not in (0, 1, 2):
            stop(f"score for {t} must be 0, 1 or 2, got {scores.get(t)!r}")
    total = sum(scores[t] for t in TESTS)
    any_zero = any(scores[t] == 0 for t in TESTS)
    if total <= 2:
        return total, "None"
    if total <= 4 or any_zero:
        return total, "Thin"
    return total, "Middling" if total <= 7 else "Strong"


def read_portfolio_file(path):
    """Read cash and positions from a Portfolio note: frontmatter cash, table under ## Positions."""
    text = Path(path).read_text()
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        stop(f"{path} has no frontmatter")
    front = dict(re.findall(r"^([\w ]+):\s*\"?([^\"\n]*)\"?\s*$", m.group(1), re.M))
    if "cash" not in front:
        stop(f"{path} has no cash line")
    sect = re.search(r"^## Positions\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    if not sect:
        stop(f"{path} has no Positions section")
    shares = {}
    rows = [r for r in sect.group(1).splitlines() if r.startswith("|")]
    for row in rows[2:]:
        cells = [c.strip() for c in row.strip("|").split("|")]
        shares[cells[0]] = float(cells[1].replace(",", ""))
    return {"kind": front.get("kind", "unknown"), "cash": float(front["cash"]), "shares": shares, "file": str(path)}


def load_company(c):
    """Fill value figures from a saved valuation run, so nothing is re-typed by hand."""
    c = dict(c)
    if c.get("run"):
        run = json.loads((ROOT / c["run"]).read_text())
        c.setdefault("price", run["price"]["close"])
        c.setdefault("price_date", run["price"]["date"])
        c.setdefault("base", {"low": run["base"]["low"], "mid": run["base"]["mid"], "high": run["base"]["high"]})
        c.setdefault("strategic", run["strategic"])
        downs = [x for x in run.get("scenarios", []) if x.get("full", 0) < 0]
        c["run_downside"] = -sum(x["full"] for x in downs) if downs else None
    for key in ("price", "price_date", "base", "strategic", "scores", "downside_if_wrong", "rose_through_trim"):
        c.setdefault(key, None)
    c.setdefault("thesis", "none")
    c.setdefault("thesis_state", None)
    c.setdefault("skeptic", "not_run")
    c.setdefault("kill_line_crossed", None)
    c.setdefault("scores_status", "claude_reading")
    if c["thesis"] not in ("none", "draft", "recorded"):
        stop(f'{c["ticker"]}: thesis must be none, draft or recorded')
    if c["skeptic"] not in ("survived", "did_not_survive", "not_run"):
        stop(f'{c["ticker"]}: skeptic must be survived, did_not_survive or not_run')
    return c


def analyze(c):
    p, b = c["price"], c["base"]
    a = {"name": c["name"], "ticker": c["ticker"], "price": p, "price_date": c["price_date"], "unsure": [], "blocked_by": []}
    a["base_low"], a["base_mid"] = (b["low"], b["mid"]) if b else (None, None)
    a["strategic"] = c["strategic"]
    a["coverage_pct"] = b["mid"] / p * 100 if b and p else None
    a["buy_below"] = b["mid"] / BAR if b else None
    a["trim_above"] = b["mid"] + c["strategic"] if b and c["strategic"] is not None else None
    a["value_if_wrong"] = None
    a["loss_pct"] = None
    if b and p and c["downside_if_wrong"] is not None:
        a["value_if_wrong"] = b["low"] - c["downside_if_wrong"]
        a["loss_pct"] = (p - max(a["value_if_wrong"], 0)) / p * 100
    a["loss_grid"] = round_up_loss(a["loss_pct"]) if a["loss_pct"] is not None else None
    a["gates"] = {
        "thesis_recorded": c["thesis"] == "recorded",
        "skeptic_survived": c["skeptic"] == "survived",
        "under_buy_below": (p < a["buy_below"]) if (p and a["buy_below"]) else None,
    }
    a["gates_pass"] = all(v is True for v in a["gates"].values())
    a["score"], a["grade"] = grade_of(c["scores"])
    a["cap"] = CAP[a["grade"]] if a["grade"] else None
    a["limit_room"] = LIMIT / a["loss_grid"] * 100 if a["loss_grid"] else None
    a["size_pct"] = None
    if a["cap"] is not None and a["limit_room"] is not None:
        a["size_pct"] = floor_tenth(min(a["cap"], a["limit_room"]))
    return a


def run(data, portfolio_file=None):
    label = data.get("label", "unnamed") + (f", run against {portfolio_file}" if portfolio_file else "")
    as_of = data.get("as_of")
    companies = [load_company(c) for c in data["companies"]]
    by = {c["ticker"]: c for c in companies}

    src = data.get("portfolio")
    if portfolio_file:
        src = {"file": portfolio_file}
    if src is None:
        stop("no portfolio given")
    if "file" in src:
        path = Path(src["file"])
        pf = read_portfolio_file(path if path.is_absolute() else ROOT / path)
        kind = pf["kind"]
        cash = pf["cash"]
        held = {}
        for t, n in pf["shares"].items():
            if t not in by:
                stop(f"{t} is in the portfolio file but not in the inputs. A whole-portfolio run must cover every position.")
            if by[t]["price"] is None:
                stop(f"{t} has no price, so the portfolio cannot be valued")
            held[t] = n * by[t]["price"]
        source_name = str(src["file"])
    else:
        kind = "made-up"
        cash = float(src["cash"])
        held = {t: float(v) for t, v in src["positions"].items()}
        source_name = src.get("source", "made up in the inputs")
        for t in held:
            if t not in by:
                stop(f"{t} is held but not in the inputs")
    total = cash + sum(held.values())
    if total <= 0:
        stop("the portfolio is worth nothing")

    rows = {c["ticker"]: analyze(c) for c in companies}
    for t, a in rows.items():
        a["held_usd"] = held.get(t, 0.0)
        a["held_pct"] = a["held_usd"] / total * 100
        a["loss_share_pct"] = a["held_pct"] * a["loss_pct"] / 100 if a["loss_pct"] is not None and a["held_usd"] else (0.0 if not a["held_usd"] else None)

    groups = []
    for g in data.get("groups", []):
        status = g.get("status", "proposed")
        if status not in ("proposed", "ruled"):
            stop(f'group {g["name"]}: status must be proposed or ruled')
        for t in g["members"]:
            if t not in rows:
                stop(f'group {g["name"]}: {t} is not in the inputs')
        groups.append({"name": g["name"], "event": g.get("event"), "status": status, "members": list(g["members"]),
                       "evidence": g.get("evidence")})

    # Several hits at once: highest score first, then highest coverage (Rules/cash.md).
    order = sorted(rows.values(), key=lambda a: (-(a["score"] or 0), -(a["coverage_pct"] or 0), a["ticker"]))
    state_cash = cash
    state_held = dict(held)
    tally = {}

    def add_room(a):
        """How much of the portfolio this whole position may be, inside every group it sits in."""
        room = None
        for g in groups:
            if a["ticker"] not in g["members"]:
                continue
            used = 0.0
            for t in g["members"]:
                if t == a["ticker"] or not state_held.get(t):
                    continue
                other = rows[t]
                if other["loss_pct"] is None:
                    a["blocked_by"].append(f'group "{g["name"]}": {t} is held with an unknown loss, so the group cannot be summed')
                    return 0.0
                used += state_held[t] / total * 100 * other["loss_pct"] / 100
            this = (LIMIT - used) / (a["loss_pct"] / 100)
            room = this if room is None else min(room, this)
        return room

    for a in order:
        c = by[a["ticker"]]
        t = a["ticker"]
        is_held = a["held_usd"] > 0
        kill = c["kill_line_crossed"]
        broken = c["thesis_state"] == "broken"
        action, size = None, 0.0
        why = None
        a["trim_to_usd"] = None

        over_trim = a["trim_above"] is not None and a["price"] is not None and a["price"] > a["trim_above"]
        under_buy = a["gates"]["under_buy_below"] is True
        conflict = over_trim and under_buy
        intact = c["thesis"] == "recorded" and c["thesis_state"] == "intact"

        # Can the rules buy any more of this?
        can_add, amount = False, 0.0
        if a["gates_pass"] and kill is not True and (not is_held or intact) and not conflict:
            if a["size_pct"] is None:
                a["blocked_by"].append("grade or loss unknown, so no size")
            elif a["size_pct"] > 0:
                pct = a["size_pct"]
                room = add_room(a)
                if room is not None and room < pct:
                    a["group_limited"] = True
                    pct = floor_tenth(max(room, 0))
                want = max(pct / 100 * total - state_held.get(t, 0.0), 0.0)
                keep = (FLOOR if a["grade"] == "Strong" else RESERVE) / 100 * total
                payable = max(state_cash - keep, 0.0)
                amount = want
                if payable < want:
                    a["cash_limited"] = True
                    amount = floor_tenth(payable / total * 100) / 100 * total
                can_add = amount > 0
            else:
                a["blocked_by"].append("grade None: no position")

        if broken:
            if is_held:
                action, size, why = "sell", a["held_usd"], "you ruled the thesis broken, so the whole position is up for reassessment"
            else:
                action, why = "no position", "thesis broken and nothing held"
        elif is_held:
            if conflict:
                action, why = "hold", "price is above the trim-above and under the buy-below at once, so the rules point both ways"
            elif intact and c["rose_through_trim"] is True and over_trim:
                action, why = "trim", "a rise took the price through the trim-above with the thesis intact"
            elif can_add:
                action, size, why = "add", amount, "all three gates pass, and the size, the limits and the cash leave room"
            else:
                action, why = "hold", "no rule calls for an add or a sale"
        else:
            if can_add:
                action, size, why = "buy", amount, "all three gates pass, and the size, the limits and the cash leave room"
            else:
                failed = [k for k, v in a["gates"].items() if v is not True]
                if failed:
                    action, why = "no position", "gates not met: " + ", ".join(f.replace("_", " ") for f in failed)
                elif kill is True:
                    action, why = "no position", "a kill line is crossed, and a review comes first"
                else:
                    action, why = "no position", "the limits or the cash leave no room"

        if action == "trim":
            # The rules set no amount. Claude's proposal: back to the most cap and limit allow today.
            if a["size_pct"] is not None and a["held_pct"] > a["size_pct"] > 0:
                a["trim_to_usd"] = a["size_pct"] / 100 * total
                size = a["held_usd"] - a["trim_to_usd"]
            else:
                size = None
        if action not in ACTIONS:
            stop(f"{t}: action {action!r}")
        a["action"], a["size_usd"], a["why"] = action, size, why

        if action in ("buy", "add"):
            state_cash -= size
            state_held[t] = state_held.get(t, 0.0) + size
            tally[t] = size
        a["position_after_usd"] = state_held.get(t, 0.0) if action in ("buy", "add") else a["held_usd"]
        a["lost_if_wrong_usd"] = a["position_after_usd"] * a["loss_pct"] / 100 if a["loss_pct"] is not None else (0.0 if not a["position_after_usd"] else None)

        # Unsure list
        u = a["unsure"]
        if a["size_pct"] is None and not a["gates_pass"] and a["base_low"] is None:
            u.append("No base value on file, so coverage, the buy-below and the loss if wrong are unknown. The valuation skill and its fit check come first.")
        if c["thesis"] == "none":
            u.append("No thesis on file. So there is nothing to prove wrong, no kill line and no claim to test.")
        if c["thesis"] == "draft":
            u.append("The thesis is a draft, not recorded. Gate 1 fails, and no thesis can be called intact or broken.")
        if c["skeptic"] == "not_run":
            u.append("No skeptic's review has run.")
        if is_held and c["thesis"] != "recorded" and action == "hold":
            u.append('Held with no recorded thesis. "Hold" here is by elimination: only a trim or a broken thesis may lead to a sale (override 7), and neither applies. It is not a view that the position is sound. Write a thesis, or rule on it yourself.')
        if c["scores"] is not None and c["scores_status"] != "ruled":
            u.append("The five test scores are Claude's reading, not your ruling.")
        if c["scores"] is None:
            u.append("No scores, so no grade and no cap.")
        if is_held and over_trim and c["rose_through_trim"] is None:
            if intact:
                u.append("Price is above the trim-above, but I cannot tell if a rise took it through. Being above is not the test. Needs the buy date and cost.")
            else:
                u.append("Price is above the trim-above, but no trim can apply: it needs a recorded, intact thesis and a rise through the line. A draft or no thesis cannot be intact, so an entry date alone would not make it a trim.")
        if kill is True:
            u.append("A kill line is crossed. That opens a review, never a sale. No buy or add until you have ruled.")
        if kill is None and is_held and c["thesis"] != "none":
            u.append("No kill-line reading was given for this position.")
        if c.get("run_downside") and c["downside_if_wrong"] == 0 and c["base"] and c["price"]:
            alt = c["base"]["low"] - c["run_downside"]
            alt_loss = (c["price"] - max(alt, 0)) / c["price"] * 100
            u.append(f'The saved run has a downside of ${c["run_downside"]:.2f}, left out of value if wrong. If it still bites when the thesis is wrong, value if wrong is ${alt:.2f} and the loss {alt_loss:.1f}% (calc.). Your ruling.')
        if conflict:
            u.append(f'Buy-below ${a["buy_below"]:.2f} is above trim-above ${a["trim_above"]:.2f}, and the price sits between. This happens when strategic value is under a third of the base middle (calc.). The rules do not say which wins. Your ruling.')
        if action == "trim":
            u.append("The rules set no trim amount. The suggested amount is Claude's proposal: back to the most the cap and the limit allow today. If no such amount exists it stays unset.")
        if action == "sell":
            u.append('The rule says "reassess the whole position", not "sell". "Sell" here is the reading of your ruling that the thesis is broken.')
        if a.get("cash_limited"):
            u.append("Cash, not the size rule, set this amount. Rounded down to 0.1% of the portfolio is Claude's reading of how to round it.")
        if a.get("group_limited"):
            u.append("A shared limit cut this size. Sized by the unrounded loss, as the group sum uses it: Claude's reading.")
        if a["value_if_wrong"] is not None and a["value_if_wrong"] < 0:
            u.append("Value if wrong is below zero, so the loss is capped at 100%: Claude's reading.")
        if as_of and a["price_date"] and (date.fromisoformat(as_of) - date.fromisoformat(a["price_date"])).days > 7:
            u.append(f'The price is from {a["price_date"]}, over a week before {as_of}.')
        if c["price"] is None:
            u.append("No price on file.")

    # Groups: sums, and names against bets
    def share_after(t):
        """Position after these actions, as a loss in % of the portfolio. None if the loss is unknown."""
        if rows[t]["loss_pct"] is None:
            return None
        return state_held.get(t, 0.0) / total * rows[t]["loss_pct"]

    for g in groups:
        members_held = [t for t in g["members"] if state_held.get(t)]
        known = sum(share_after(t) for t in members_held if share_after(t) is not None)
        unknown = [t for t in members_held if share_after(t) is None]
        g["members_held"] = members_held
        g["known_loss_pct"] = known
        g["unknown_loss"] = unknown
        g["money_pct"] = sum(state_held[t] / total * 100 for t in members_held)
        g["over_limit"] = True if known > LIMIT else (None if unknown else False)

    def bet_count(use, book):
        parent = {t: t for t in rows if book.get(t)}
        def find(x):
            while parent[x] != x:
                x = parent[x]
            return x
        for g in use:
            ms = [t for t in g["members"] if t in parent]
            for t in ms[1:]:
                parent[find(t)] = find(ms[0])
        return len({find(t) for t in parent})

    after_cash = state_cash
    alerts, port_unsure = [], []
    cash_pct = cash / total * 100
    after_pct = after_cash / total * 100
    level = "above normal" if cash_pct > RESERVE else ("normal" if cash_pct >= FLOOR else "under the floor")
    if cash_pct < FLOOR:
        alerts.append(f"Cash {cash_pct:.1f}% is under the {FLOOR:.0f}% floor. Add nothing. It never forces a sale.")
    if cash_pct > 50:
        port_unsure.append("Cash is above 50%. The review alert needs 24 months in a row, and this run cannot see the history. Read the note's date for when the count began.")
    n = sum(1 for t in rows if state_held.get(t))
    if n > 20:
        alerts.append(f"{n} positions, over the 20 in rule 2.")
    elif n > 10:
        port_unsure.append(f"{n} positions: rule 2 needs good reason above 10.")
    elif n < 5:
        port_unsure.append(f"{n} positions after these actions, under the 5 in rule 2. Nothing here forces a buy: rule 4 and when-to-buy come first.")
    for a in rows.values():
        if a["held_usd"] and a["loss_share_pct"] is not None and a["loss_share_pct"] > LIMIT:
            alerts.append(f'{a["name"]}: {a["held_pct"]:.1f}% × {a["loss_pct"]:.1f}% loses {a["loss_share_pct"]:.1f}% of the portfolio if wrong, over the {LIMIT:.0f}% limit (calc.). Add nothing. It never forces a sale.')
        if a["held_usd"] and a["loss_share_pct"] is None:
            port_unsure.append(f'{a["name"]}: the {LIMIT:.0f}% limit cannot be checked, because its loss if wrong is unknown.')
        if a["held_usd"] and a["cap"] is not None and a["held_pct"] > a["cap"]:
            alerts.append(f'{a["name"]}: {a["held_pct"]:.1f}% of the portfolio is over its {a["grade"]} cap of {a["cap"]:.0f}%. Add nothing. It never forces a sale.')
    for g in groups:
        if g["over_limit"] is True:
            more = f', and {", ".join(g["unknown_loss"])} unknown' if g["unknown_loss"] else ""
            alerts.append(f'Group "{g["name"]}" ({g["status"]}): at least {g["known_loss_pct"]:.1f}% of the portfolio is lost if its event comes{more}, over the {LIMIT:.0f}% limit (calc.). Add nothing to the group. It never forces a sale.')
        if g["over_limit"] is None and g["unknown_loss"]:
            port_unsure.append(f'Group "{g["name"]}": the limit cannot be checked, since {", ".join(g["unknown_loss"])} have no known loss.')
        if g["status"] == "proposed":
            port_unsure.append(f'Group "{g["name"]}" is Claude\'s proposal, not your ruling. It is counted as one bet here. Without your ruling, the count is the "ruled only" figure.')

    ruled_groups = [g for g in groups if g["status"] == "ruled"]
    bets_all = bet_count(groups, state_held)
    bets_ruled = bet_count(ruled_groups, state_held)
    if not groups and n >= 2 and not data.get("ruled_separate"):
        port_unsure.append(f"{n} positions and no group in the inputs. That means the test for one thesis was not run, not that it passed. If they were one thesis, the sum of their losses is what the 5% limit would test.")
    bought = sum(tally.values())
    out = {
        "label": label, "as_of": as_of, "kind": kind, "portfolio_source": source_name, "total": total,
        "cash": cash, "cash_pct": cash_pct, "cash_level": level, "cash_after": after_cash, "cash_after_pct": after_pct,
        "bought": bought, "positions": n, "groups_count": len(groups), "bets_with_proposed": bets_all, "bets_ruled_only": bets_ruled,
        "positions_before": sum(1 for t in rows if held.get(t)), "alerts": alerts, "portfolio_unsure": port_unsure, "groups": groups,
        "order": [a["ticker"] for a in order], "rows": [rows[c["ticker"]] for c in companies],
    }
    for a in out["rows"]:
        ws = data.get("what_if_size")
        if ws and a["loss_pct"] is not None:
            a["what_if"] = {"size": ws, "lost": ws * a["loss_pct"] / 100}
    return out


def usd(v):
    return "unknown" if v is None else f"${v:,.0f}"


def money(v):
    return "unknown" if v is None else f"${v:,.2f}"


def pct(v):
    return "unknown" if v is None else f"{v:.1f}%"


def gate(v):
    return {True: "met", False: "not met", None: "unknown"}[v]


def render(o):
    w = [f"# {o['label']}, as of {o['as_of']}", ""]
    if o["kind"] != "real":
        w += [f"**{o['kind'].capitalize()} portfolio, not real holdings.** Source: {o['portfolio_source']}. All sums calc.", ""]
    w += [f"Portfolio {usd(o['total'])}. Cash {usd(o['cash'])}, {pct(o['cash_pct'])}: {o['cash_level']}. After these actions: {usd(o['cash_after'])}, {pct(o['cash_after_pct'])}.",
          f"Names against bets, after these actions: {o['positions']} positions, {o['groups_count']} groups, {o['bets_with_proposed']} bets with proposed groups, {o['bets_ruled_only']} on your rulings only.", ""]
    w += ["| Company | Action | Size | Position after | Lost if wrong |", "|---|---|---|---|---|"]
    for a in o["rows"]:
        size = "not set by the rules" if a["size_usd"] is None else usd(a["size_usd"])
        w.append(f"| {a['name']} | **{a['action']}** | {size} | {usd(a['position_after_usd'])} | {usd(a['lost_if_wrong_usd'])} |")
    w.append("")
    for a in o["rows"]:
        w += [f"## {a['name']}: {a['action']}", f"- Why: {a['why']}."]
        w.append(f"- Price {money(a['price'])} ({a['price_date'] or 'no date'}). Base low {money(a['base_low'])}, middle {money(a['base_mid'])}. Coverage {pct(a['coverage_pct'])}. Buy-below {money(a['buy_below'])}. Strategic {money(a['strategic'])}. Trim-above {money(a['trim_above'])}.")
        w.append(f"- Gates: thesis recorded {gate(a['gates']['thesis_recorded'])}; survived the skeptic by your ruling {gate(a['gates']['skeptic_survived'])}; under the buy-below {gate(a['gates']['under_buy_below'])}.")
        grade = f"{a['score']}, {a['grade']}, cap {a['cap']:.0f}%" if a["grade"] else "unknown"
        w.append(f"- Score and grade: {grade}. Value if wrong {money(a['value_if_wrong'])}. Loss if wrong {pct(a['loss_pct'])}, on the grid {a['loss_grid'] if a['loss_grid'] else 'unknown'}. 5% ÷ loss {pct(floor_tenth(a['limit_room']) if a['limit_room'] else None)}. " + (f"Rule's size {pct(a['size_pct'])} before the groups and the cash." if a["gates_pass"] else "No size while a gate fails: any figure would be a sum, not a size."))
        w.append(f"- Held {usd(a['held_usd'])}, {pct(a['held_pct'])}.")
        if a.get("what_if"):
            w.append(f"- What-if, a sum and not a size: {usd(a['what_if']['size'])} would lose {usd(a['what_if']['lost'])} if the thesis is wrong (calc.).")
        if a["trim_to_usd"] is not None:
            w.append(f"- Claude's proposed trim: sell {usd(a['size_usd'])}, keeping {usd(a['trim_to_usd'])}.")
        for b in a["blocked_by"]:
            w.append(f"- Blocked: {b}.")
        for u in a["unsure"]:
            w.append(f"- Unsure: {u}")
        w.append("")
    if o["groups"]:
        w.append("## Shared exposures")
        for g in o["groups"]:
            state = {True: "over the limit", False: "inside the limit", None: "cannot tell"}[g["over_limit"]]
            w.append(f"- {g['name']} ({g['status']}): event: {g['event']}. Members {', '.join(g['members'])}. Held {pct(g['money_pct'])} of the money. Known loss {pct(g['known_loss_pct'])} against {LIMIT:.0f}%, unknown for {', '.join(g['unknown_loss']) or 'none'}: {state}.")
        w.append("")
    if o["alerts"]:
        w.append("## Alerts")
        w += [f"- {x}" for x in o["alerts"]] + [""]
    if o["portfolio_unsure"]:
        w.append("## Unsure about the portfolio")
        w += [f"- {x}" for x in o["portfolio_unsure"]] + [""]
    w.append(CLOSER)
    return "\n".join(w)


def main():
    ap = argparse.ArgumentParser(description="One action per company. Reads only, places no order.")
    ap.add_argument("inputs")
    ap.add_argument("--portfolio", help="use this Portfolio note in place of the inputs' portfolio")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--what-if-size", type=float, help="dollars the owner named: shows what that sum would lose, labeled as not a size")
    args = ap.parse_args()
    data = json.loads(Path(args.inputs).read_text())
    if args.what_if_size:
        data["what_if_size"] = args.what_if_size
    out = run(data, args.portfolio)
    print(json.dumps(out, indent=1) if args.json else render(out))


if __name__ == "__main__":
    main()
