"""Draw watch.html from seen.json and readings.toml. This script makes no network requests.

Run from the project root, after watch.py:
    uv run python sensors/8k-watch/draw.py
"""

import datetime as dt
import html
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import watch  # noqa: E402

OUT = HERE.parent.parent / "watch.html"
WIDE = {"width": 960, "left": 92, "right": 24, "r": 7.5, "every": 1, "labels": True, "cls": "wide"}
PHONE = {"width": 360, "left": 58, "right": 12, "r": 6, "every": 2, "labels": False, "cls": "phone"}
LANE_Y = {"high": 62, "medium": 138, "low": 214}
AXIS_Y = 256
LEVEL_TEXT = {
    "high": "Read the same day. It changes the shares, ownership, leadership or a big deal.",
    "medium": "Read this week. Results or new business information.",
    "low": "Skim. A notice or routine vote, with no new numbers.",
}
e = html.escape


def x_of(iso, start, end, size=WIDE):
    first, last = dt.date.fromisoformat(start), dt.date.fromisoformat(end)
    share = (dt.date.fromisoformat(iso) - first).days / max((last - first).days, 1)
    return round(size["left"] + share * (size["width"] - size["left"] - size["right"]), 1)


def _months(start, end):
    first, last = dt.date.fromisoformat(start), dt.date.fromisoformat(end)
    year, month = first.year, first.month
    while (year, month) <= (last.year, last.month):
        day = dt.date(year, month, 1)
        if day >= first:
            yield day
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)


def _item_list(entry, flags):
    return ", ".join(f"{i} {watch.item_name(i)}" + (" (flagged)" if i in flags else "") for i in entry["items"]) or "none found"


def _chart(rows, flags, start, end, company, size):
    width, left, right = size["width"], size["left"], size["right"]
    parts = [f'<svg class="{size["cls"]}" viewBox="0 0 {width} 290" role="img" aria-label="Timeline of {e(company)} 8-K filings from {e(watch.nice_date(start))} to {e(watch.nice_date(end))}, in three lanes by attention. The table below holds every filing.">']
    for level, y in LANE_Y.items():
        parts.append(f'<line class="lane" x1="{left}" x2="{width - right}" y1="{y}" y2="{y}"/>')
        parts.append(f'<text class="lane-name" x="0" y="{y + 4}">{level.capitalize()}</text>')
    parts.append(f'<line class="axis" x1="{left}" x2="{width - right}" y1="{AXIS_Y}" y2="{AXIS_Y}"/>')
    for n, day in enumerate(_months(start, end)):
        if n % size["every"]:
            continue
        x = x_of(day.isoformat(), start, end, size)
        parts.append(f'<line class="axis" x1="{x}" x2="{x}" y1="{AXIS_Y}" y2="{AXIS_Y + 5}"/>')
        name = day.strftime("%b") if day.month > 1 or not size["labels"] else day.strftime("%b %Y")
        parts.append(f'<text class="tick" x="{x}" y="{AXIS_Y + 20}" text-anchor="middle">{name}</text>')
    for entry, rated in rows:
        x, y = x_of(entry["filed"], start, end, size), LANE_Y[rated["attention"]]
        is_flagged = any(i in flags for i in entry["items"])
        shape = "solid" if is_flagged else "hollow"
        tip = {"date": watch.nice_date(entry["filed"]), "level": rated["attention"].capitalize(),
               "items": ", ".join(entry["items"]) or "none found", "flagged": "flagged" if is_flagged else "not flagged",
               "reason": rated["reason"]}
        label = (rated["reading"] or {}).get("label")
        if label and size["labels"]:
            # Centred on its own dot, so it cannot read as the label of a close neighbour.
            parts.append(f'<text class="direct" x="{x}" y="{y - 14}" text-anchor="middle">{e(label)}</text>')
        parts.append(f'<a class="mark" href="{e(entry["url"])}" data-tip="{e(json.dumps(tip))}" aria-label="{e(tip["date"])}, {e(rated["attention"])} attention: {e(rated["reason"])}">'
                     f'<circle class="hit" cx="{x}" cy="{y}" r="14"/><circle class="dot {rated["attention"]} {shape}" cx="{x}" cy="{y}" r="{size["r"]}"/></a>')
    parts.append("</svg>")
    return "".join(parts)


def _row(entry, rated, flags):
    items = []
    for number in entry["items"]:
        flag = number in flags
        items.append(f'<span class="item{" on" if flag else ""}" title="{e(watch.item_name(number))}">{"⚑ " if flag else ""}{e(number)}</span>')
    links = [f'<a href="{e(entry["url"])}">{e(entry["form"])}, filed {e(watch.nice_date(entry["filed"]))}</a>']
    reading = rated["reading"]
    if reading and reading.get("source_url"):
        links.append(f'<a href="{e(reading["source_url"])}">{e(reading.get("source_label", "exhibit"))}</a>')
    by = "" if reading else '<div class="why">Not read yet. Rating comes from the item numbers.</div>'
    return (f'<tr class="row"><td class="when">{e(watch.nice_date(entry["filed"]))}</td>'
            f'<td class="level"><i class="chip {rated["attention"]}"></i>{rated["attention"].capitalize()}</td>'
            f'<td class="items">{"".join(items) or "none found"}</td>'
            f'<td><div class="reason">{e(rated["reason"])}</div>{by}<div class="why">{" · ".join(links)}</div></td></tr>')


def _findings(rows, flags):
    """Counted from the rows, so the sentence cannot go stale when new filings arrive."""
    total = len(rows)
    flagged = [r for r in rows if any(i in flags for i in r[0]["items"])]
    missed = [r for r in rows if r[1]["attention"] == "high" and r not in flagged]
    low_flagged = [r for r in flagged if r[1]["attention"] == "low"]
    used = {i for r in rows for i in r[0]["items"]}
    unused = [i for i in flags if i not in used]
    gaps = [(r[0], [i for i in r[0]["items_filing"] if i not in r[0]["items_index"]]) for r in rows]
    gaps = [(entry, only) for entry, only in gaps if only]
    out = [f"<li><b>{len(flagged)} of {total} filings carry a flagged item.</b> {len(low_flagged)} of those are low attention, so a flag alone does not sort the pile.</li>"]
    if missed:
        names = "; ".join(f'{watch.nice_date(r[0]["filed"])}, items {", ".join(r[0]["items"])}' for r in missed)
        out.append(f"<li><b>{len(missed)} high-attention filing{'s' if len(missed) > 1 else ''} carr{'y' if len(missed) > 1 else 'ies'} no flagged item:</b> {e(names)}. It is drawn as a hollow dot.</li>")
    if unused:
        out.append(f"<li>Flagged items that never appeared: {e(', '.join(unused))}.</li>")
    if gaps:
        names = "; ".join(f'{e(watch.nice_date(entry["filed"]))}: {e(", ".join(only))}' for entry, only in gaps)
        out.append(f"<li>EDGAR's index left out items the filing lists on {len(gaps)} filings ({names}). The sensor reads each filing, so these are kept.</li>")
    changed = [(r, watch.rule_rating(r[0]["items"])[0]) for r in rows if r[1]["rated_by"] == "reading"]
    changed = [(r, rule) for r, rule in changed if rule != r[1]["attention"]]
    if changed:
        names = "; ".join(f'{watch.nice_date(r[0]["filed"])}: {rule} to {r[1]["attention"]}' for r, rule in changed)
        out.append(f"<li><b>Reading changed the rule's rating on {len(changed)} of {total} filings</b> ({e(names)}). A new filing keeps the rule's rating until someone reads it.</li>")
    return "".join(out)


def build_page(flags, companies, seen, readings, today):
    sections, summary = [], []
    for company in companies:
        entries = sorted((x for x in seen.values() if x["ticker"] == company["ticker"]), key=lambda x: (x["filed"], x["accession"]))
        if not entries:
            continue
        rows = [(x, watch.rating(x, readings)) for x in entries]
        count = {level: sum(1 for r in rows if r[1]["attention"] == level) for level in watch.LEVELS}
        highs = [r for r in rows if r[1]["attention"] == "high"]
        summary.append(f'{e(company["name"])}: {count["high"]} of {len(rows)} 8-Ks since {e(watch.nice_date(company["since"]))} deserve high attention, {count["medium"]} medium and {count["low"]} low.')
        unread = sum(1 for r in rows if r[1]["rated_by"] == "rule")
        sections.append(
            f'<h2>{e(company["name"])} ({e(company["ticker"])})</h2>'
            f'<div class="card"><figure><ul class="legend">'
            + "".join(f'<li><i class="chip {level}"></i><b>{level.capitalize()}:</b> {e(LEVEL_TEXT[level])}</li>' for level in watch.LEVELS)
            + '<li><i class="chip neutral"></i>Solid dot: has a flagged item</li><li><i class="chip neutral hollow"></i>Hollow dot: no flagged item</li></ul>'
            f'<div class="plot">{_chart(rows, flags, company["since"], today, company["name"], WIDE)}{_chart(rows, flags, company["since"], today, company["name"], PHONE)}<div class="tip" hidden></div></div>'
            f'<figcaption>Filing date across, attention down. {len(rows)} filings. Click a dot to open the filing. {unread} rated from item numbers only, {len(rows) - unread} rated after reading.</figcaption></figure></div>'
            f'<h3>What the flags caught</h3><ul class="notes">{_findings(rows, flags)}</ul>'
            '<h3>Every filing</h3><div class="wrap"><table><thead><tr><th scope="col">Filed</th><th scope="col">Attention</th><th scope="col">Items (⚑ flagged)</th><th scope="col">Why, and source</th></tr></thead><tbody>'
            + "".join(_row(x, rated, flags) for x, rated in rows)
            + "</tbody></table></div>")
    if not sections:
        raise watch.WatchError("seen.json holds no filings for this watchlist. Run watch.py first.")
    names = ", ".join(f"{i} {watch.item_name(i)}" for i in flags)
    return PAGE.replace("{{SUMMARY}}", " ".join(summary)).replace("{{SECTIONS}}", "".join(sections)).replace(
        "{{TODAY}}", e(watch.nice_date(today))).replace("{{FLAGS}}", e(names))


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>8-K Watch</title><style>
:root{color-scheme:light;--page:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink-2:#52514e;--muted:#6f6d68;--grid:#e1e0d9;--axis:#a9a89e;--border:rgba(11,11,11,.10);--link:#1c5cab;--high:#d03b3b;--medium:#fab219;--low:#8f8d85}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])){color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--ink:#f0efec;--ink-2:#c3c2b7;--muted:#a3a198;--grid:#2c2c2a;--axis:#5a5a55;--border:rgba(255,255,255,.10);--link:#7db2f0;--high:#e0524f;--low:#8a8880}}
:root[data-theme="dark"]{color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--ink:#f0efec;--ink-2:#c3c2b7;--muted:#a3a198;--grid:#2c2c2a;--axis:#5a5a55;--border:rgba(255,255,255,.10);--link:#7db2f0;--high:#e0524f;--low:#8a8880}
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1080px;margin:0 auto;padding:32px 16px 48px}
h1{font-size:24px;line-height:1.25;margin:0 0 8px;font-weight:650}
h2{font-size:17px;margin:28px 0 6px;font-weight:650}h3{font-size:15px;margin:24px 0 6px;font-weight:650}
p{margin:0 0 10px;max-width:75ch}.lede{color:var(--ink-2)}
a{color:var(--link)}a:focus-visible{outline:2px solid var(--link);outline-offset:2px}
figure{margin:0}.card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px;margin:12px 0}
.legend{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:4px 18px;margin:0 0 12px;padding:0;list-style:none;font-size:13px;color:var(--ink-2)}
.chip{display:inline-block;width:11px;height:11px;border-radius:50%;margin-right:7px;vertical-align:-1px;flex:none}
.chip.high{background:var(--high)}.chip.medium{background:var(--medium)}.chip.low{background:var(--low)}.chip.neutral{background:var(--muted)}
.chip.neutral.hollow{background:none;border:2.5px solid var(--muted)}
.plot{position:relative}
svg{display:block;width:100%;height:auto;font:12px system-ui,-apple-system,"Segoe UI",sans-serif}
svg.phone{display:none}
.lane{stroke:var(--grid)}.axis{stroke:var(--axis)}
.lane-name{fill:var(--ink-2);font-size:13px;font-weight:600}.tick{fill:var(--muted);font-size:12px}.direct{fill:var(--ink);font-size:12.5px}
.dot{stroke:var(--surface);stroke-width:2}
.dot.high{fill:var(--high)}.dot.medium{fill:var(--medium)}.dot.low{fill:var(--low)}
.dot.hollow{fill:var(--surface);stroke-width:3.5}.dot.high.hollow{stroke:var(--high)}.dot.medium.hollow{stroke:var(--medium)}.dot.low.hollow{stroke:var(--low)}
.hit{fill:transparent}.mark{outline:none}.mark:focus-visible .hit{fill:var(--border)}
.tip{position:absolute;z-index:2;pointer-events:none;background:var(--page);border:1px solid var(--border);border-radius:8px;padding:8px 10px;font-size:12.5px;width:290px;box-shadow:0 2px 10px rgba(0,0,0,.18)}
.tip[hidden]{display:none}.tip .h{font-weight:650}.tip .m{color:var(--muted);margin-bottom:4px}
figcaption{margin-top:6px;color:var(--muted);font-size:13px;max-width:80ch}
.wrap{overflow-x:auto}
table{border-collapse:collapse;width:100%;min-width:680px;font-size:14px}
th,td{text-align:left;vertical-align:top;padding:9px 14px 9px 0;border-bottom:1px solid var(--border)}
thead th{border-bottom:1px solid var(--axis);font-weight:650}
.when,.level{white-space:nowrap}.items{min-width:120px}
.item{display:inline-block;margin:0 5px 3px 0;padding:0 6px;border:1px solid var(--border);border-radius:5px;font-size:12.5px;color:var(--muted);font-variant-numeric:tabular-nums;white-space:nowrap}
.item.on{color:var(--ink);font-weight:600;border-color:var(--axis)}
.reason{color:var(--ink)}.why{color:var(--muted);font-size:12.5px;margin-top:2px}
ul.notes{margin:0 0 10px;padding-left:18px;max-width:80ch}ul.notes li{margin-bottom:6px}
.foot{color:var(--muted);font-size:13px}
@media (max-width:640px){
  svg.wide{display:none}svg.phone{display:block}
  table{min-width:0}thead{display:none}
  table,tbody,tr,td{display:block}
  tr{padding:10px 0;border-bottom:1px solid var(--border)}
  td{border:0;padding:0}
  td.when,td.level{display:inline-block;margin-right:12px;font-weight:600}
  td.items{margin:4px 0}
}
</style></head><body><main>
<h1>8-K watch</h1>
<p class="lede">{{SUMMARY}}</p>
<p class="foot">This page sorts filings for reading. It is not a buy, trim or sell view. Drawn {{TODAY}} from <code>sensors/8k-watch/seen.json</code>.</p>
{{SECTIONS}}
<h2>How to read this</h2>
<ul class="notes">
<li><b>A flag and an attention rating are different things.</b> A flag means the filing has an item on the owner's list: {{FLAGS}}. Attention is how much the filing's content matters.</li>
<li><b>Attention is Claude's judgment, for the owner to confirm.</b> A new filing starts with a rating from its item numbers. Claude's reading in <code>readings.toml</code> replaces it. No thesis is written yet, so ratings say how much a filing changes the facts, not how it bears on a thesis.</li>
<li><b>An 8-K watch sees 8-Ks only.</b> As checked Nov. 2, 2026, the Amazon, Verizon and AT&amp;T deals were first named in a Corning filing 50, 49 and 28 days after first news (calc.), and no filing names Zayo. See the Corning note and <a href="filings.html">filings.html</a>.</li>
<li>Item names come from <a href="https://www.sec.gov/files/form8-k.pdf">SEC Form 8-K, undated, retrieved Nov. 2, 2026</a>. Each filing's items are the union of EDGAR's index and the filing's own headings.</li>
</ul>
</main>
<script>
document.querySelectorAll(".plot").forEach(function(plot){
  var tip=plot.querySelector(".tip");
  function show(mark){
    var d=JSON.parse(mark.getAttribute("data-tip"));
    tip.textContent="";
    [["h",d.date+" · "+d.level],["m","Items "+d.items+" · "+d.flagged],["r",d.reason]].forEach(function(p){var el=document.createElement("div");el.className=p[0];el.textContent=p[1];tip.appendChild(el);});
    var box=plot.getBoundingClientRect(),dot=mark.getBoundingClientRect();
    tip.hidden=false;
    var left=Math.min(Math.max(0,dot.left-box.left+18),box.width-tip.offsetWidth);
    var top=dot.bottom-box.top+2;
    if(top+tip.offsetHeight>box.height)top=Math.max(0,dot.top-box.top-tip.offsetHeight-2);
    tip.style.left=left+"px";tip.style.top=top+"px";
  }
  plot.querySelectorAll(".mark").forEach(function(mark){
    mark.addEventListener("mouseenter",function(){show(mark);});
    mark.addEventListener("focus",function(){show(mark);});
    mark.addEventListener("mouseleave",function(){tip.hidden=true;});
    mark.addEventListener("blur",function(){tip.hidden=true;});
  });
});
</script>
</body></html>
"""


def main():
    try:
        flags, companies = watch.load_watchlist()
        page = build_page(flags, companies, watch.load_seen(), watch.load_readings(), dt.date.today().isoformat())
    except watch.WatchError as error:
        sys.exit(f"Stopped: {error}")
    OUT.write_text(page)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
