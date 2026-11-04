"""Turn the saved data into HTML and charts. Everything from a file is escaped.

Note text comes partly from filings, so it must never reach Streamlit's markdown: an image link in a
note would make the browser fetch it on page load. Links are plain clicks and only https.
"""

import datetime as dt
import html
import re

import altair as alt
import pandas as pd

import data
import health

e = html.escape
YIELD, AAA = "Corning earnings yield", "Moody's Aaa"
# Same colours as economy.html and watch.html, so a series or level means the same on every page.
# The dark orange is one step darker than economy.html's, which falls outside the validated lightness band.
SERIES = {"light": {YIELD: "#6250d6", AAA: "#d95926"}, "dark": {YIELD: "#9085e9", AAA: "#e8622c"}}

CSS = """<style>
.d-wrap{overflow-x:auto;margin:.25rem 0 .5rem}
.d-table{border-collapse:collapse;width:100%;min-width:48rem;font-size:.9rem;line-height:1.4}
.d-table th{text-align:left;font-weight:600;padding:.4rem .6rem;border-bottom:1px solid color-mix(in srgb,currentColor 35%,transparent);white-space:nowrap}
.d-table td{padding:.5rem .6rem;border-bottom:1px solid color-mix(in srgb,currentColor 12%,transparent);vertical-align:top}
.d-num,.d-table th.d-num{text-align:right;font-variant-numeric:tabular-nums}
.d-nowrap{white-space:nowrap}
.d-muted{opacity:.72;font-size:.84rem}
.d-chip{display:inline-block;width:.7rem;height:.7rem;border-radius:50%;margin-right:.4rem;background:var(--lvl)}
tr.lvl-high{--lvl:#d03b3b}tr.lvl-medium{--lvl:#fab219}tr.lvl-low{--lvl:#8f8d85}tr.lvl-unknown{--lvl:transparent}
tr.lvl-high td{background:color-mix(in srgb,var(--lvl) 13%,transparent)}
tr.lvl-medium td{background:color-mix(in srgb,var(--lvl) 13%,transparent)}
tr[class^=lvl-] td:first-child{border-left:4px solid var(--lvl)}
tr.lvl-unknown .d-chip{border:1px solid currentColor}
.d-flag{font-weight:650}
.d-tiles{display:flex;flex-wrap:wrap;gap:2.5rem;margin:.25rem 0 .75rem}
.d-tile b{display:block;font-size:2rem;font-weight:600;line-height:1.2;font-variant-numeric:tabular-nums}
.d-score{margin:.4rem 0 1.1rem}
.d-score h5{margin:0 0 .3rem;font-size:.9rem;font-weight:600;padding:0}
.d-bar{display:flex;gap:2px;height:.9rem;margin-bottom:.35rem}
.d-bar i{display:block;background:var(--c);min-width:2px}
.d-bar i:first-child{border-radius:4px 0 0 4px}.d-bar i:last-child{border-radius:0 4px 4px 0}
.d-keys{display:flex;flex-wrap:wrap;gap:.2rem 1rem;font-size:.85rem}
.d-keys i{display:inline-block;width:.65rem;height:.65rem;border-radius:2px;margin-right:.35rem;background:var(--c)}
.d-keys b{font-variant-numeric:tabular-nums;font-weight:600}
.d-chart-title{font-weight:600;font-size:.95rem;margin:0}
.d-result{white-space:nowrap}
.d-result-match{color:inherit}
.d-result-diff{font-weight:650;border-left:3px solid #d03b3b;padding-left:.4rem}
.d-testcopy{padding:.3rem .7rem;font-weight:700;color:#fff;background:#d03b3b;border-radius:4px}
.d-problem{padding:.6rem .8rem;border-left:4px solid #d03b3b;background:color-mix(in srgb,#d03b3b 10%,transparent);margin:.25rem 0}
small.d-src{display:block;opacity:.72;font-size:.78rem;font-weight:400;line-height:1.35}
.d-tile small.d-src{max-width:16rem}
.d-table caption.d-src{caption-side:bottom;text-align:left;opacity:.72;font-size:.78rem;padding:.3rem .6rem}
.d-prose{margin:.25rem 0 .7rem}
.d-prose p{margin:0 0 .35rem}
.d-chart-head{margin:.5rem 0 0}
.d-note{margin:.2rem 0 .55rem;line-height:1.45}
cite{font-style:normal}
.d-age,.d-run{font-size:.84rem;line-height:1.35;margin:.1rem 0}
.d-run{font-weight:600}
.d-nosrc{display:inline-block;margin:0 .35rem;padding:0 .35rem;font-size:.74rem;border:1px solid currentColor;border-radius:3px;opacity:.8;white-space:nowrap}
.c-coach{font-weight:600;margin:.1rem 0 .4rem}
.c-top{display:flex;flex-wrap:wrap;gap:.35rem 2.2rem;align-items:baseline;margin:.1rem 0 .3rem}
.c-top b.c-name{font-size:1.5rem;font-weight:650}
.c-draft{padding:.45rem .7rem;margin:.25rem 0 .6rem;border:2px dashed currentColor;border-radius:4px;font-weight:700;letter-spacing:.02em}
.c-layer{margin:.5rem 0 .15rem;font-weight:650}
.c-side{display:flex;flex-wrap:wrap;gap:1rem 2rem;align-items:flex-start;margin:.25rem 0 .75rem}
.c-side>.c-closes{flex:0 1 19rem;display:flex;flex-direction:column;gap:.7rem}
.c-side>.c-zones{flex:1 1 26rem;min-width:0}
.c-side .d-table{min-width:0}
.c-side .d-val{display:block;font-size:1.6rem;font-weight:600;font-variant-numeric:tabular-nums;line-height:1.2}
.c-missing td:first-child{font-weight:600;white-space:nowrap}
.i-jump{display:flex;flex-wrap:wrap;gap:.2rem 1.2rem;margin:.1rem 0 .5rem}
.i-flow{display:flex;flex-wrap:wrap;gap:.3rem;margin:.3rem 0 .3rem;align-items:center}
.i-arrow{opacity:.55;font-style:normal}
.i-tile{flex:1 1 5.6rem;align-self:stretch;display:block;padding:.4rem .55rem;border:1px solid color-mix(in srgb,currentColor 30%,transparent);border-radius:4px;color:inherit !important;text-decoration:none !important;line-height:1.25}
.i-tile b{display:block;font-size:1.4rem;font-weight:600;font-variant-numeric:tabular-nums}
.i-tile span{font-size:.82rem}
.i-off{border-style:dashed;margin-left:.9rem}
.i-lead{display:block;font-size:.76rem;font-weight:600;white-space:nowrap}
.i-also{margin-top:.35rem;font-size:.82rem}
.i-also p{margin:.2rem 0;font-size:.82rem}
.i-box{max-height:30rem;overflow:auto;margin:.25rem 0 .75rem;border-bottom:1px solid color-mix(in srgb,currentColor 25%,transparent)}
.i-box .d-wrap{overflow:visible;margin:0}
.i-box th{position:sticky;top:0;z-index:1;background:var(--st-background-color,Canvas)}
.i-state{min-width:11rem}
.i-state b{display:block}
.j-fold{margin:.2rem 0;padding:.35rem .6rem;border:1px solid color-mix(in srgb,currentColor 18%,transparent);border-radius:4px}
.j-fold>summary{cursor:pointer;font-weight:600;line-height:1.35}
.j-fold>summary small.d-src{display:inline;margin-left:.6rem}
.j-fold[open]>summary{margin-bottom:.5rem}
.j-sub{margin:0 0 0 1rem}
</style>"""


def link(url, text):
    text = e(str(text))
    if not (isinstance(url, str) and url.startswith("https://")):
        return text
    return f'<a href="{e(url, quote=True)}" target="_blank" rel="noopener noreferrer">{text}</a>'


def problem(message):
    return f'<div class="d-problem">{e(str(message))}</div>'


def test_copy_banner(words):
    return f'<div class="d-testcopy">{e(words)}</div>'


def fig(value, source, date, middle=""):
    """One figure with its source and date on the same line. A source is a (label, https link) pair, a vault file path, or "calc." with its inputs.

    With no source or no date it refuses, so a figure cannot reach a screen bare. `middle` is safe markup that sits between the figure and its source."""
    return f'<span class="d-fig"><b class="d-val">{e(str(value))}</b>{middle}{src(source, date, value)}</span>'


def src(source, date, value=""):
    """The small print: a source and its date, or a refusal."""
    label, url = source if isinstance(source, tuple) else (source, None)
    if not label or not date:
        raise ValueError(f"A figure needs a source and a date: {value!r}")
    label = str(label).replace("`", "")
    shown = label if str(date) in label else f"{date}, {label}"  # the date first, so an ellipsis cuts the path and not the date
    return f'<small class="d-src" title="{e(shown, quote=True)}">{link(url, shown) if url else e(shown)}</small>'


def age_tag(kind, then, today=None):
    """My limit in words, when a source is past it, and nothing when it is not. It looks like any other line: no colour and no level."""
    words = data.past_limit(kind, then, today)
    return f' <div class="d-age">{e(words)}</div>' if words else ""


def run_trouble_lines(trouble, only=None):
    """What the Daily run's own digest says about its sensors. It looks like any other line. It holds no level, and it is not on the waiting list, because no routine wrote it there."""
    if not trouble:
        return ""
    day, file = data.nice_date(trouble["day"]), trouble["file"]
    lines = [f'The {f["name"]} failed in the Daily run of {day} ({file}). {f["feeds"]} stop at what it last saved. A clean run of it would clear this line.'
             for f in trouble["failed"] if not only or f["name"] == only]
    if trouble["no_brief"] and not only:
        lines.append(f'That run left no brief in the Journal ({file}, {day}), so the waiting list does not count what it found. The next Daily run would brief it.' if lines else
                     f'The Daily run of {day} wrote its digest and no brief yet ({file}), so the waiting list does not count what it found. The next Daily run would brief it.')
    return "".join(f'<div class="d-run d-text">{e(line)}</div>' for line in lines)


def missing(what, fill):
    """Says plainly what is missing and what would fill it. A test finds any "not on file" with no "would fill" beside it."""
    return f'<p class="d-text"><b>Not on file:</b> {e(what)} What would fill it: {e(fill)}</p>'


def sourced(inner, small):
    """Prose with figures in it, and its small print under it. The figure test checks that the small print holds a date."""
    return f'<div class="d-fig d-prose">{inner}{small}</div>'


def src_markup(markup):
    """Small print whose words are already safe markup, such as a link from a note."""
    return f'<small class="d-src">{markup}</small>'


def chart_head(title, small, words=""):
    """Every chart on the Company page comes with one of these, so its figures have a source. A test counts them against the charts."""
    words = f'<p class="d-muted">{words}</p>' if words else ""
    return f'<div class="d-fig d-chart-head"><p class="d-chart-title">{e(title)}</p>{words}{small}</div>'


def _table(headers, rows, numeric=(), caption=""):
    """`caption` is safe markup: the source and date of every row. Without one, each row needs a cell of class d-src holding its own."""
    head = "".join(f'<th{" class=d-num" if i in numeric else ""}>{e(h)}</th>' for i, h in enumerate(headers))
    under = f'<caption class="d-src">{caption}</caption>' if caption else ""
    return f'<div class="d-wrap"><table class="d-table">{under}<thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


# ---- Home ----

# Tuned by measuring in Chrome at 1366 wide (dashboard/tools/measure_home.py). What does not fit is counted, and a count is always shown.
WAITING_ROWS, COMING_ROWS, INFO_ROWS, STAND_ROWS = 5, 7, 3, 5
ASKS = {"Red": "the same day: read the source, add nothing to that position or its group, then rule.",
        "Orange": "within a week and before any decision on that stock: read it and say which way a claim went."}

# Every row stays on one line, cut with an ellipsis, so a long line cannot grow the page.
HOME_CSS = """<style>
@media (min-width:1001px){
 [data-testid=stMainBlockContainer]{padding:4rem 1.1rem 0 !important}
 .h-grid{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}
 .h-wide{grid-column:1 / -1}
}
[data-testid=stMainBlockContainer]>div{gap:.3rem}
.h-top{font-size:1rem;margin:0 0 .3rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.h-grid{display:grid;gap:.55rem .9rem;font-size:.86rem;line-height:1.34}
.h-block{min-width:0;padding-top:.25rem;border-top:2px solid color-mix(in srgb,currentColor 30%,transparent)}
.h-block h2{font-size:.86rem !important;font-weight:700;margin:0 0 .12rem;padding:0 !important;line-height:1.3;letter-spacing:.02em;text-transform:uppercase;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.h-block h2 small{font-weight:400;text-transform:none;letter-spacing:0;opacity:.72}
.h-row,.h-note,.h-ask,.h-more{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.h-row{display:flex;gap:.45rem;align-items:baseline;padding:.04rem 0}
.h-row .d-fig{display:contents}
.h-row .d-val{flex:none;font-weight:600;font-variant-numeric:tabular-nums}
.h-row .d-src{flex:0 1 auto;min-width:3rem;max-width:30%;overflow:hidden;text-overflow:ellipsis;opacity:.72;font-size:.76rem}
.h-tag{flex:none;font-weight:600}
.h-kind{flex:none;opacity:.72}
.h-text{flex:1 1 0;min-width:2rem;overflow:hidden;text-overflow:ellipsis}
.h-ask{font-weight:600;margin-top:.1rem;padding-left:.35rem;border-left:3px solid var(--lvl)}
.h-red{--lvl:#d03b3b}.h-orange{--lvl:#fab219}
.h-row.h-red,.h-row.h-orange{padding-left:.35rem;border-left:3px solid var(--lvl)}
.h-note,.h-more{opacity:.72;font-size:.78rem}
.h-more{font-weight:600;opacity:1}
.h-since{display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:3;overflow:hidden;margin-bottom:.1rem}
.h-empty{padding:.1rem 0}
.h-bad{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;border-left:3px solid #d03b3b;padding-left:.35rem}
@media (max-width:1000px){
 .h-row,.h-note,.h-ask,.h-more,.h-bad,.h-top,.h-block h2{white-space:normal}
 .h-row{flex-wrap:wrap}
 .h-row .d-val,.h-tag,.h-text{flex:0 1 auto;white-space:normal}
 .h-row .d-src{max-width:100%;white-space:normal}
}
</style>"""


def screen_link(slug, words):
    """A plain click to another screen of this board, in the same tab."""
    return f'<a href="/{e(slug, quote=True)}" target="_self">{e(words)}</a>'


def _md_plain(text):
    """A line as a reader sees it, for the hover text: link targets and backticks gone."""
    return re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", str(text)).replace("`", "").replace("**", "")


def _text(markdown_line, css="h-text"):
    return f'<span class="d-text d-copied {css}" title="{e(_md_plain(markdown_line), quote=True)}">{_inline(markdown_line.replace("**", ""))}</span>'


def _condition(row):
    """An alert's words with its source link taken out, since the source has its own place on the row. The hover text keeps the whole line."""
    words = re.sub(r"\[[^\]]+\]\(https://[^)\s]+\)", "", row["text"], count=1) if isinstance(row["source"], tuple) else row["text"]
    words = re.sub(r"\.\s*:", ".", re.sub(r"\s+([,:;.])", r"\1", words.replace("**", ""))).strip(" ,:;")
    return f'<span class="d-text d-copied h-text" title="{e(_md_plain(row["text"]), quote=True)}">{_inline(words)}</span>'


def _bads(messages):
    """At most one line a block, with a count, so problems cannot push the page past one screen."""
    if not messages:
        return ""
    more = f' And {len(messages) - 1} more.' if len(messages) > 1 else ""
    return _bad(messages[0] + more)


def _bad(message):
    return f'<div class="h-bad d-text" title="{e(str(message), quote=True)}">{e(str(message))}</div>'


def _plural(n, word):
    return f'{n} {word}{"" if n == 1 else "s"}'


def home_counts(waiting):
    reds = sum(r["level"] == "Red" for r in waiting["rows"])
    return reds, len(waiting["rows"]) - reds


def _home_headline(model):
    last = (model["book"] or {}).get("last_run", {}).get("Daily run")
    newest = f'Newest daily record: {data.nice_date(last)}.' if last else "No daily record on file."
    if model["waiting"] is None:
        words = "<b>Unknown: the Journal could not be read.</b>"
    else:
        reds, oranges = home_counts(model["waiting"])
        words = f"<b>Waiting for me: {reds} Red, {oranges} Orange.</b>" if reds or oranges else "<b>Nothing waiting.</b>"
    return f'<p class="h-top d-text">Does anything need me today? {words} <span class="d-muted">{e(newest)} Read-only: this page reads files on this computer and sends nothing.</span></p>'


def _home_waiting(model):
    waiting = model["waiting"]
    if waiting is None:
        return _bad(f'The Journal could not be read: {model["book_problem"]}')
    reds, oranges = home_counts(waiting)
    shown = waiting["rows"][:WAITING_ROWS]
    parts, level = [], None
    for row in shown:
        if row["level"] != level:
            level = row["level"]
            parts.append(f'<div class="h-ask d-text h-{level.lower()}">{e(level)}, {e(ASKS[level])}</div>')
        tag = f'<span class="h-tag d-text">{e(row["rule"] or "no rule")}</span>'
        days = f'{row["days"]} day{"" if row["days"] == 1 else "s"}'
        figure = fig(f'{data.nice_date(row["day"])}, {days}', row["source"] or row["journal"], data.nice_date(row["day"]), _condition(row))
        parts.append(f'<div class="h-row h-{level.lower()}">{tag}{figure}</div>')
    if not waiting["rows"]:
        parts.append('<div class="h-empty d-text">Nothing waiting.</div>')
    hidden = waiting["rows"][WAITING_ROWS:]
    if hidden:
        hidden_reds = sum(r["level"] == "Red" for r in hidden)
        parts.append(f'<div class="h-more d-text">{screen_link("ideas", f"And {len(hidden)} more: {hidden_reds} Red, {len(hidden) - hidden_reds} Orange")}</div>')
    parts.append(_bads(waiting["problems"]))
    return "".join(parts)


def _home_since(model):
    if model["brief_problem"]:
        return _bad(f'The Journal could not be read: {model["brief_problem"]}')
    brief = model["brief"]
    if brief is None:
        return '<div class="h-empty d-text">No brief on file. The Daily run\'s next brief would fill it.</div>'
    parts = [f'<div class="h-since d-text" title="{e(_md_plain(brief["since"]), quote=True)}">{_inline(brief["since"])}</div>']
    for line in brief["info"][:INFO_ROWS]:
        parts.append(f'<div class="h-row"><span class="h-tag d-text">Info</span>{_text(line)}</div>')
    hidden = len(brief["info"]) - INFO_ROWS
    if hidden > 0:
        parts.append(f'<div class="h-more d-text">{screen_link("journal", f"And {hidden} more")}</div>')
    return "".join(parts)


def _coming_figure(row):
    source = row["source"]
    pair = (source["label"], source["url"]) if source else row["file"]
    middle = f'<span class="h-kind d-text">{e(row["kind"])}</span><span class="d-text h-text" title="{e(row["title"], quote=True)}">{e(row["title"])}</span>'
    return fig(row["when"], pair, data.nice_date(row["written"]) if not source else _date_in(source["label"]) or data.nice_date(row["written"]), middle)


def _date_in(label):
    found = re.search(r"\b[A-Z][a-z]+\.? \d{1,2}, \d{4}\b", str(label))
    return found[0] if found else None


def _home_coming(model):
    parts = [_bads(model["coming_problems"])] if model["coming_problems"] else []
    rows = model["coming"]
    parts += [f'<div class="h-row">{_coming_figure(r)}</div>' for r in rows[:COMING_ROWS]]
    if not rows and not parts:
        parts.append('<div class="h-empty d-text">No date on file in the horizon. A dated note in Catalysts/ or a calendar of checks in Research/ would fill it.</div>')
    hidden = len(rows) - COMING_ROWS
    if hidden > 0:
        parts.append(f'<div class="h-more d-text">{screen_link("ideas", f"And {hidden} more")}</div>')
    if rows:
        parts.append('<div class="h-note d-text">Dates keep the note\'s own wording. A link is the first in the note\'s When section and may not source that date.</div>')
    return "".join(parts)


def _book_row(name, note, today=None):
    if note["share"] is None:
        share = f'Share Unknown: no saved close for {", ".join(note["missing"])}'
    else:
        share = f'{note["share"]:.1%} (calc.), {note["level"]}'
    value = f'${note["cash"]:,.0f} cash, {share}, {_plural(len(note["positions"]), "position")}'
    words = data.past_limit("portfolio_note", note["last_checked"], today)
    ages = f'<div class="h-row d-age">{e(words)}</div>' if words else ""
    return f'<div class="h-row"><span class="h-tag d-text">{e(name)}</span>{fig(value, note["file"], "last checked " + data.nice_date(note["last_checked"]))}</div>{ages}'


def _stand_row(row, today=None):
    name = f'<span class="h-tag d-text">{e(row["company"])}</span>'
    price = row["price"]
    fill = data.close_fill(row["ticker"]).rstrip(".")
    close = fig(f'${price["close"]:.2f}, {data.nice_date(price["date"])}', price["source"], "fetched " + data.nice_date(price["fetched"].date())) if price else f'<span class="d-text">Close not on file. {e(fill)}.</span>'
    lines = fig(f'buy-below {_money(row["buy_below"])}, trim-above {_money(row["trim_above"])}', row["run_file"], data.nice_date(row["worked_out"]))
    words = " ".join(filter(None, [data.past_limit("close", price["date"], today) if price else "", data.past_limit("value_run", row["worked_out"], today)]))
    ages = f'<div class="h-row d-age"><span class="h-text" title="{e(words, quote=True)}">{e(words)}</span></div>' if words else ""  # one line, so Home stays on one screen
    return f'<div class="h-row">{name}{close}{lines}</div>{ages}'


def _home_stands(model):
    parts, problems, today = [], [], model.get("today")
    books = model["books"]
    if books is None:
        problems.append(f'The notes in Portfolio/ could not be read: {model["books_problem"]}')
        rows = []
    else:
        problems += books["problems"]
        rows = [_book_row("Real", n, today) for n in books["real"]] or ['<div class="h-row d-text"><span class="h-tag">Real</span>No real holdings or cash on file. A note in Portfolio/ marked real would fill it.</div>']
        rows += [_book_row("Paper, made-up money", n, today) for n in books["paper"]] or ['<div class="h-row d-text"><span class="h-tag">Paper</span>Not on file. A note in Portfolio/ marked paper would fill it.</div>']
    rows.append('<div class="h-row d-text"><span class="h-tag">Names against bets, room under the limit</span>Not on file. A saved run of the portfolio script would fill them.</div>')
    rows += [_stand_row(r, today) for r in model["stands"]]
    if not model["stands"] and not model["stands_problems"]:
        rows.append('<div class="h-row d-text">No company has a saved value run. A run of sensors/valuation/save.py would fill it.</div>')
    parts.append(_bads(problems + model["stands_problems"]))
    # A row and its age words stay together. The limit counts lines, so a day of old sources still fits one screen, and what does not fit is counted.
    used, shown = 0, 0
    for row in rows:
        lines = row.count('class="h-row')
        if used + lines > STAND_ROWS and shown:
            break
        parts.append(row)
        used, shown = used + lines, shown + 1
    hidden = len(rows) - shown
    if hidden > 0:
        parts.append(f'<div class="h-more d-text">{screen_link("portfolio", f"And {hidden} more")}</div>')
    return "".join(parts)


def _home_routines(model):
    book = model["book"]
    if book is None:
        return _bad(f'The Journal could not be read: {model["book_problem"]}')
    parts = [f'{name} {data.nice_date(book["last_run"][name]) if name in book["last_run"] else "no record"}' for name in data.ROUTINES]
    failed = [r for r in (model["waiting"] or {"rows": []})["rows"] if r["rule"] == "O16"]
    words = f'{len(failed)} failed line{"" if len(failed) == 1 else "s"} waiting. ' if failed else ""
    line = "; ".join(parts) + ". " + words + "A first run would fill a blank. A run that did not happen leaves no line."
    return f'<div class="h-row d-text"><span class="h-text" title="{e(line, quote=True)}">{e(line)}</span></div>{_home_ages(model)}'


def _home_ages(model):
    """One line, because Home has no room for more. The full table is on Ideas and alerts."""
    past = model.get("past")
    if past is None:
        return f'<div class="h-row d-age">Sources past my age limits: Unknown. {e(model.get("past_problem") or "")}</div>'
    if not past:
        return '<div class="h-row d-text">No source is past my age limits (calc., dashboard/age_limits.toml).</div>'
    names = ", ".join(p["name"] for p in past)
    return f'<div class="h-row d-age"><span class="h-text" title="{e(names, quote=True)}">Past my age limits: {_plural(len(past), "source")}, {e(names)}</span> {screen_link("ideas", "See how old")}</div>'


def home(model, now):
    """The whole of Home, as one block of markup, so it can stack in the same order on a narrow window."""
    block = lambda title, body, note="", css="": f'<section class="h-block {css}" data-block="{e(title)}"><h2 class="d-text">{e(title)}{note}</h2>{body}</section>'  # noqa: E731
    ran = data.past_limit("radar_run", model["radar_date"], model.get("today")) if model["radar_date"] else ""
    radar = f' <small>radar run {e(data.nice_date(model["radar_date"]))}{". " + e(ran) if ran else ""}</small>' if model["radar_date"] else ""
    brief = model["brief"]
    since = f' <small>{e(data.nice_date(brief["day"]))}, {e(brief["file"])}</small>' if brief else ""
    read = f' <small>Files read {e(data.nice_date(now.date()))}, {now:%H:%M} UTC.</small>'
    return (_home_headline(model) + '<div class="h-grid">'
            + block("Waiting for me", _home_waiting(model))
            + block("Coming up", _home_coming(model), radar)
            + block("Since the last brief", _home_since(model), since)
            + block("Where things stand", _home_stands(model))
            + block("Routines", _home_routines(model), read, "h-wide")
            + "</div>")


# ---- Alerts ----

ALERT_LEVELS = {"Red": "lvl-high", "Orange": "lvl-medium", "Info": "lvl-low"}
GUARD_NAMES = {"W1": "my rules", "W2": "my portfolio", "W3": "the method", "W4": "the alert map", "W5": "the guardrails", "T1": "a broker's site", "T2": "broker software or an order call",
               "T3": "a broker named with an action", "T4": "the shape of an order", "T5": "a browser, desktop or broker tool", "W?": "a walled file", "owner": "the owner's door"}


def alerts_summary(rows, days_read, read_on):
    """Counts of what the routines wrote, each level's waiting count beside it. `rows` come from data.alert_rows."""
    tiles = []
    for level in ALERT_LEVELS:
        mine = [r for r in rows if r["level"] == level]
        waiting = sum(r["state"] == "Waiting" for r in mine)
        under = "" if level == "Info" else f'<div class="d-muted">{waiting} waiting</div>'
        tiles.append(f'<div class="d-tile"><b>{len(mine)}</b>{level}{under}</div>')
    return sourced(f'<div class="d-tiles">{"".join(tiles)}</div>',
                   src(f"calc., counted from the {days_read} daily files in Journal/", read_on)) + (
        '<p class="d-muted">What the routines wrote, shown in full. A line states a condition, its rule, its source and its date, and it gives no advice. '
        'Rules/alerts.md says what each level asks of me. A Red also goes to my phone. Info asks for no ruling. A line in the Journal starting "Ruled:" closes one Red or Orange, and the board writes none.</p>')


def _alert_state(row):
    if row["state"] == "Waiting":
        return f'<b>Waiting</b>{_plural(row["days"], "day")} since its Journal day (calc.)'
    if row["state"] == "Ruled":
        return f'<b>Ruled</b><span class="d-copied">{note_inline(row["ruled"])}</span>{src(f"Journal/{row["ruled_in"]}.md", data.nice_date(row["ruled_in"]))}'
    return "No ruling asked"


def alerts_table(rows):
    """Every line in full, with its source, its Journal day and whether I have ruled. Rows from data.alert_rows."""
    if not rows:
        return '<p class="d-muted">None on file. A routine writing its next Red, Orange or Info line would fill it.</p>'
    body = []
    for row in rows:
        day = data.nice_date(row["day"])
        named = src(row["source"], day) if row["source"] else '<small class="d-muted">The line names no source.</small>'
        body.append(f'<tr class="{ALERT_LEVELS[row["level"]]}"><td class="d-nowrap"><span class="d-chip"></span>{e(row["level"])}</td><td>{e(row["rule"]) or "None"}</td>'
                    f'<td class="d-nowrap">{e(day)}</td><td>{e(row["routine"])}</td><td><span class="d-copied">{note_inline(row["text"])}</span></td>'
                    f'<td>{named}{src(row["journal"], day)}</td><td class="i-state">{_alert_state(row)}</td></tr>')
    return _table(("Level", "Rule", "Journal", "Routine", "What it says", "Source and date", "Ruled or waiting"), body)


def alert_filter_line(shown, rows):
    """How many lines the filters show, and any Red or Orange still waiting that they leave out, so a filter never hides one silently."""
    hidden = [r for r in rows if r["state"] == "Waiting" and r not in shown]
    counts = [_plural(sum(r["level"] == level for r in hidden), level) for level in ("Red", "Orange") if any(r["level"] == level for r in hidden)]
    tail = f' These filters leave out {" and ".join(counts)} still waiting.' if hidden else ""
    return f'<p class="d-text"><b>Showing {len(shown)} of {len(rows)} lines.</b>{tail}</p>'


def routine_table(book, read_on="", today=None):
    body = []
    for name in data.ROUTINES:
        last = book["last_run"].get(name)
        said = data.against_limit(data.ROUTINE_LIMITS[name], last, today) if last else "No record yet. Its first run would fill it."
        body.append(f'<tr><td>{e(name)}</td><td>{e(data.nice_date(last)) if last else "No record yet"}</td><td>{e(said)}</td></tr>')
    caption = src_markup(e(f"Journal/, read {read_on}. Limits: dashboard/age_limits.toml")) if read_on else ""
    return _table(("Routine", "Last record in the Journal", "Against my limit"), body, caption=caption)


def guard_summary(rows):
    stopped = [r for r in rows if r["how"] == "before the call"]
    undone = [r for r in rows if r["how"].startswith("after-check")]
    outside = [r for r in rows if "between calls" in r["how"]]
    return (f'<p class="d-muted">From the guardrail hook\'s own record: {len(stopped)} calls stopped, {len(undone)} files put back, {len(outside)} walled files changed between calls and left as they are, since that may be my own edit. '
            'What each routine may touch is on guardrails.html.</p>')


def guard_table(rows, caption=""):
    """Every row of the hook's own record, newest first."""
    if not rows:
        return '<p class="d-muted">Nothing on record.</p>'
    body = [f'<tr><td class="d-nowrap">{e(r["when"][:16].replace("T", " "))} UTC</td><td>{e(r["rule"])}, {e(GUARD_NAMES.get(r["rule"], ""))}</td><td>{e(r["how"])}</td><td>{e(r["tool"])}</td><td>{e(r["target"])}</td></tr>' for r in rows]
    return _table(("When", "Guardrail", "What it did", "Tool", "Target"), body, caption=caption)


NO_VIEW_LINE = "Only the price against value panel sets price against base value. It shows where the price sits and gives no buy or trim recommendation. The rest of this page gives no view."


def watchlist_table(rows, now):
    out = []
    for r in rows:
        name = f'<td>{e(r["name"])}</td><td>{e(r["ticker"])}</td>'
        p = r["price"]
        if p:
            out.append(f'<tr>{name}<td class="d-num">${p["close"]:.2f}</td><td class="d-nowrap">{e(data.nice_date(p["date"]))}</td>'
                       f'<td class="d-nowrap">{e(data.age_text(dt.date.fromisoformat(p["date"]), now.date()))}</td>'
                       f'<td class="d-muted d-src">{e(p["source"])}, fetched {e(data.nice_date(p["fetched"].date()))}. Close, not adjusted for dividends. '
                       f'File: sensors/prices/cache/{e(r["ticker"])}/{e(p["file"])}{age_tag("close", p["date"], now.date())}</td></tr>')
        else:
            why = f'{r["problem"] or "No price on file."} This page does not fetch one. {data.close_fill(r["ticker"])}'
            out.append(f'<tr>{name}<td class="d-num">Unknown</td><td>Unknown</td><td></td><td class="d-muted">{e(why)}</td></tr>')
    return _table(["Company", "Ticker", "Last close (USD)", "Close date", "Age of close", "Source"], out, numeric=(2,))


def filings_table(notes):
    out = []
    for n in notes:
        if n["problem"]:
            out.append(f'<tr class="lvl-unknown"><td class="d-nowrap">{e(n["filed"])}</td><td>Unknown</td><td></td>'
                       f'<td colspan="3">Could not read Inbox/{e(n["name"])}: {e(n["problem"])}</td></tr>')
            continue
        flagged = set(n["flagged"])
        items = ", ".join(f'<span class="d-flag">{e(str(i))} ⚑</span>' if i in flagged else e(str(i)) for i in n["items"])
        rated = {"reading": "Read. Claude's judgment, for me to confirm.", "rule": "Item numbers only. Nobody has opened it."}.get(n["rated_by"], n["rated_by"])
        source = link(n["url"], f'{n["form"]}, filed {data.nice_date(n["filed"])}')
        out.append(f'<tr class="lvl-{e(n["attention"])}"><td class="d-nowrap">{e(data.nice_date(n["filed"]))}</td>'
                   f'<td class="d-nowrap"><i class="d-chip"></i>{e(n["attention"].capitalize())}</td>'
                   f'<td>{e(n["ticker"])}</td><td class="d-nowrap">{items}</td><td>{e(n["reason"])}<div class="d-muted">{e(rated)}</div></td>'
                   f'<td class="d-src">{source}</td></tr>')
    return _table(["Filed", "Attention", "Ticker", "Items (⚑ flagged)", "Why", "Source"], out)


def radar_summary(run):
    d, screen = run["dates"], run["screen"]
    lead_text = f'{screen.get("lead_count", 0)} screen leads' if screen["status"] == "ok" else "no screen on this run"
    return (f'<p><b>{len(d["soon"])} catalyst dates due or opening within {e(str(run["horizon_days"]))} days, {len(d["passed"])} passed with no Outcome written, '
            f'{len(run["events"])} new events, {e(lead_text)}.</b></p>'
            f'<p class="d-muted">Saved run of {e(data.nice_date(run["run_date"]))}, {e(run["run_utc"][11:16])} UTC. Report: {e(run["report"])}. To run it again, follow sensors/README.md, then reload. '
            'Future dates are targets or forecasts, not results. Nothing in this panel is a view on value.</p>' + radar_hidden_line(run))


def radar_hidden_line(run):
    """What the run hid, so nothing goes missing without a count. A run saved before these rules has none."""
    hidden = run.get("hidden")
    if not hidden or not (hidden["grant_count"] or hidden["lead_count"] or hidden["step2_count"]):
        return ""
    return (f'<p class="d-muted">Hidden from these counts, and listed in the folded rows on this screen: {hidden["grant_count"]} director stock grants, '
            f'{hidden["lead_count"]} screen leads that may not be new growth, {hidden["step2_count"]} second-step links from walks started only by a screen lead.</p>')


def _date_rows(rows):
    out = []
    for c in rows:
        when = data.nice_date(c["date_start"]) if c["date_start"] == c["date_end"] else f'{data.nice_date(c["date_start"])} to {data.nice_date(c["date_end"])}'
        source = c.get("source")
        out.append(f'<tr><td>{e(c["title"])}</td><td class="d-nowrap">{e(when)}</td><td>{e(c["date_kind"])}</td><td class="d-num">{e(str(c["days_to_start"]))}</td><td class="d-num">{e(str(c["days_to_end"]))}</td>'
                   f'<td>{link(source["url"], source["label"]) if source else "No link in the note\'s When section"}</td></tr>')
    return out


def radar_dates_table(rows, caption=""):
    if not rows:
        return '<p class="d-muted">None.</p>'
    return _table(["Catalyst", "Date, as read", "Kind", "Days to its start (calc.)", "Days to its end (calc.)", "First link in the note's When section. It may not source this date."], _date_rows(rows), numeric=(3, 4), caption=caption)


def radar_events_table(events, caption=""):
    if not events:
        return '<p class="d-muted">No new events on this run.</p>'
    out = []
    for ev in events:
        bears = "; ".join(f'{b["title"]} ({b["why"]})' for b in ev["catalysts"]) or "None singled out"
        out.append(f'<tr><td class="d-nowrap">{e(data.nice_date(ev["filed"]))}</td><td>{e(ev["company"])}</td><td>{link(ev["url"], ev["label"])}</td>'
                   f'<td>{e(ev["summary"])}</td><td>{e(", ".join(ev["named"])) or "None"}</td><td>{e(bears)}</td></tr>')
    return _table(["Filed", "Company", "Source", "What the sensor saved", "Named in it", "Read against. A name match, not a reading."], out, caption=caption)


def radar_walks(walks, caption=""):
    if not walks:
        return '<p class="d-muted">Nothing to walk on this run.</p>'
    out = [f'<tr><td>{e(start)}</td><td class="d-num">{w["events"]}</td><td class="d-num">{w["step1"]}</td><td class="d-num">{w["step2"]}</td><td class="d-num">{w["weak"]}</td>'
           f'<td>{e(", ".join(w["chains"]))}</td><td>{e(", ".join(w["named"])) or "None"}</td></tr>' for start, w in walks.items()]
    return _table(["Starts at", "New events", "Links, step 1", "Links, step 2", "Weak links", "Chains", "Named in the events"], out, numeric=(1, 2, 3, 4), caption=caption)


def radar_hidden_links(walks, caption=""):
    """Second-step links hidden because only an unread screen lead started the walk."""
    out = [f'<tr><td>{e(start)}</td><td>{e(r["node"])}</td><td>{e(r["kind"])}</td><td>{e(r["a"])}</td><td>{e(r["b"])}</td><td>{e(r["chain"])}</td><td>{e(r["evidence"])}</td></tr>'
           for start, w in walks.items() for r in w.get("hidden_step2", [])]
    return _table(["Started at", "Reaches", "Link", "From", "To", "Chain", "Evidence"], out, caption=caption)


def _lead_flags(line, lead=None):
    flags = [lead["not_new_growth"]] if lead and lead.get("not_new_growth") else []
    if line.get("unit_slip"):
        flags.append("Check the units")
    if line.get("rounded_differently"):
        flags.append("Rounded differently")
    if line["accession_earlier"] == line["accession_later"]:
        flags.append("Both from one filing")
    return ", ".join(flags)


def radar_leads_table(leads, retrieved=""):
    """Largest percent first. Every row looks the same, whatever the size: a lead is not a level. Every row says what it is."""
    out = []
    until = f', retrieved in the run of {e(retrieved)}' if retrieved else ""
    for lead in leads:
        for line in lead["lines"]:
            year = "Not on file. A saved SEC frame a year earlier would fill it" if line["year_ago_pct"] is None else f'{line["year_ago_pct"]:+,.1f}%'
            sources = f'{link(line["filing_later"], "Filing")}, {link(line["frame_url_later"], line["frame_later"])}{until}'
            out.append(f'<tr><td>{e(lead["name"])}{_lead_label()}</td><td>{e(lead.get("ticker") or "None")}</td><td>{e(line["label"])}</td>'
                       f'<td class="d-num">{_usd(line["earlier"])}<div class="d-muted">{e(data.nice_date(line["end_earlier"]))}</div></td>'
                       f'<td class="d-num">{_usd(line["later"])}<div class="d-muted">{e(data.nice_date(line["end_later"]))}</div></td>'
                       f'<td class="d-num">+{line["rise_pct"]:,.1f}%</td><td class="d-num">{e(year)}</td><td>{e(_lead_flags(line, lead))}</td>'
                       f'<td>{src_markup(sources)}</td></tr>')
    return _table(["Company", "Ticker", "Measure", "Earlier", "Later", "Change (calc.)", "Same step a year earlier (calc.)", "Flags", "Source and date"], out, numeric=(3, 4, 5, 6))


def _usd(value):
    return f"${value / 1e9:,.1f}B" if abs(value) >= 1e9 else f"${value / 1e6:,.0f}M"


def radar_step_line(step):
    filled = (f'Still filling: {step["filers_later"]} of about {step["filers_earlier"]} filer rows so far.' if step["filling"]
              else f'{step["filers_later"]} filer rows against {step["filers_earlier"]}.')
    rows = sum(len(lead["lines"]) for lead in step["leads"])
    return f'<p class="d-chart-title">{e(step["earlier"])} to {e(step["later"])}: {len(step["leads"])} companies, {rows} rows</p><p class="d-muted">{e(filled)} Same step a year earlier means {e(step["year_ago_step"])}.</p>'


def yield_summary(y):
    step = y["step"]
    above = (f'Most recently above in {data.nice_month(y["last_above"])}, and at or below at the {y["since"]} month-ends since.'
             if y["last_above"] else "Never above in this window.")
    filing = link(step["url"], f'{step["form"]}, filed {data.nice_date(step["filed"])}')
    aaa_link = link(y["aaa_url"], f'FRED AAA, downloaded {data.nice_date(y["aaa_downloaded"].date())}')
    fetched = f'Yahoo through yfinance, fetched {e(data.nice_date(y["fetched"].date()))}'
    small = src_markup(f'{filing}; {fetched}; {aaa_link}')
    return sourced(f"""<div class="d-tiles">
<div class="d-tile"><b>{y["yield"]:.1f}%</b>Corning earnings yield, {e(data.nice_date(y["date"]))} (calc.)</div>
<div class="d-tile"><b>{y["aaa"]:.2f}%</b>Moody's Aaa, {e(data.nice_month(y["aaa_month"]))}</div>
</div>
<p>The yield was above Aaa at {y["above"]} of {y["compared"]} month-ends (calc.). {e(above)}</p>
<p class="d-muted">Earnings yield = ${y["eps"]:.2f} ÷ ${y["close"]:.2f} (calc.). ${y["eps"]:.2f} is trailing diluted GAAP EPS as on file that day, from the
{link(step["url"], f'{step["form"]}, filed {data.nice_date(step["filed"])}')}. ${y["close"]:.2f} is the close from Yahoo through yfinance, fetched {e(data.nice_date(y["fetched"].date()))}.
Aaa is from {link(y["aaa_url"], f'FRED AAA, downloaded {data.nice_date(y["aaa_downloaded"].date())}')}, a monthly figure.
The two dates differ, and the two yields are different things. The filing behind every EPS step is in economy.html.
<b>This is not a valuation method. It does not use base value, so it says nothing about buying or trimming.</b></p>""", small)


def month_frame(y):
    # Plain column names: Vega reads field names as paths, so an apostrophe in one stops the chart drawing.
    rows = [{"Month": pd.Timestamp(m["day"]), "Label": data.nice_month(m["day"]), "EY": m.get("EY"), "AAA": m.get("AAA"),
             "Close": m.get("close"), "EPS": m.get("eps")} for m in y["months"]]
    return pd.DataFrame(rows)


def month_table(y):
    frame = month_frame(y).drop(columns="Month").iloc[::-1]
    return frame.rename(columns={"Label": "Month", "EY": "Earnings yield % (calc.)", "AAA": "Aaa %", "Close": "Month-end close (USD)", "EPS": "Trailing EPS (USD)"}).round(2)


def month_rows_table(y):
    """Every month, as a table with its sources under it."""
    frame = month_table(y)
    rows = ["<tr>" + "".join(f'<td class="d-num">{"" if pd.isna(v) else e(f"{v:,.2f}")}</td>' if i else f'<td class="d-nowrap">{e(str(v))}</td>' for i, v in enumerate(row)) + "</tr>" for row in frame.itertuples(index=False)]
    caption = (f'Month-end close: Yahoo through yfinance, fetched {e(data.nice_date(y["fetched"].date()))}. Aaa: {link(y["aaa_url"], f"FRED AAA, downloaded {data.nice_date(y["aaa_downloaded"].date())}")}. '
               f'Trailing EPS: SEC company facts, as on file each month, newest step {link(y["step"]["url"], f"{y["step"]["form"]}, filed {data.nice_date(y["step"]["filed"])}")}, every step in economy.html. Yield: calc., EPS ÷ close.')
    return _table(list(frame.columns), rows, numeric=(1, 2, 3, 4), caption=caption)


def yield_chart(y, theme="light"):
    wide = month_frame(y)
    colors = SERIES["dark" if theme == "dark" else "light"]
    ink = "#f0efec" if theme == "dark" else "#0b0b0b"
    axis = "#5a5a55" if theme == "dark" else "#a9a89e"
    long = wide.melt(id_vars="Month", value_vars=["EY", "AAA"], var_name="Key", value_name="Percent").dropna()
    long["Series"] = long["Key"].map({"EY": YIELD, "AAA": AAA})
    scale = alt.Scale(domain=[YIELD, AAA], range=[colors[YIELD], colors[AAA]])
    room = wide["Month"].max() + pd.DateOffset(months=20)  # space for the end labels
    x = alt.X("Month:T", title=None, scale=alt.Scale(domain=[wide["Month"].min(), room]), axis=alt.Axis(format="%Y", tickCount="year", grid=False))
    y_axis = alt.Y("Percent:Q", title="Percent", scale=alt.Scale(zero=True), axis=alt.Axis(gridColor=axis, gridOpacity=0.35, domain=False, tickSize=0))
    lines = alt.Chart(long).mark_line(strokeWidth=2, strokeCap="round", strokeJoin="round").encode(
        x=x, y=y_axis, color=alt.Color("Series:N", scale=scale, title=None, legend=alt.Legend(orient="top", direction="horizontal", labelColor=ink, labelFontSize=13, symbolStrokeWidth=3)))
    ends = long.sort_values("Month").groupby("Series", as_index=False).last()
    ends["Text"] = ends.apply(lambda r: f'{r["Percent"]:.1f}%' if r["Series"] == YIELD else f'{r["Percent"]:.2f}%', axis=1)
    dots = alt.Chart(ends).mark_point(filled=True, size=70, opacity=1).encode(x=x, y=y_axis, color=alt.Color("Series:N", scale=scale, legend=None))
    labels = alt.Chart(ends).mark_text(align="left", dx=9, fontSize=13, fontWeight=600, color=ink).encode(x=x, y=y_axis, text="Text:N")
    hover = alt.selection_point(fields=["Month"], nearest=True, on="pointerover", clear="pointerout", empty=False)
    tips = [alt.Tooltip("Label:N", title="Month"), alt.Tooltip("EY:Q", title="Earnings yield % (calc.)", format=".2f"),
            alt.Tooltip("AAA:Q", title="Aaa %", format=".2f"), alt.Tooltip("Close:Q", title="Month-end close, USD", format=".2f"),
            alt.Tooltip("EPS:Q", title="Trailing EPS, USD", format=".2f")]
    # An invisible point per month catches the pointer. The rule shows which month is being read.
    catcher = alt.Chart(wide).mark_point(opacity=0, size=400).encode(x=x, y=alt.value(190), tooltip=tips).add_params(hover)
    rule = alt.Chart(wide).mark_rule(color=axis, strokeWidth=1).encode(x=x).transform_filter(hover)
    return alt.layer(rule, lines, dots, labels, catcher).properties(height=380)


def sources_table(rows, now):
    caption = src_markup(e(f"Ages: calc., against {data.nice_date(now.date())}, from the files' own manifests and dates. Limits: dashboard/age_limits.toml, approved Nov. 4, 2026"))
    out = []
    for r in rows:
        name = link(r["url"], r["name"]) if r["url"] else e(r["name"])
        if r["problem"]:
            out.append(f'<tr><td>{name}</td><td>{e(r["used_for"])}</td><td colspan="5">{e(r["problem"])}</td></tr>')
            continue
        against = data.against_limit(r["kind"], r["counted"], now.date()) if r["kind"] else r["no_limit"]
        note = f'<div class="d-muted">{e(r["note"])}</div>' if r["note"] else ""
        out.append(f'<tr><td>{name}{note}</td><td>{e(r["used_for"])}</td>'
                   f'<td class="d-nowrap">{e(data.nice_date(r["retrieved"].date()))}</td><td class="d-nowrap">{e(data.age_text(r["retrieved"], now))}</td>'
                   f'<td class="d-nowrap">{e(r["data_label"])}</td><td class="d-nowrap">{e(data.age_text(r["data_end"], now.date()))}</td><td>{e(against)}</td></tr>')
    return _table(["Source", "Used for", "Retrieved", "Age of copy", "Newest data in it", "Age of data", "Against my limit"], out, caption=caption)


# ---- Corning price against value. Everything here comes from one saved run. ----

ZONE_WORDS = {"under": "Under the buy-below", "between": "Between the buy-below and the trim-above", "above": "Above the trim-above",
              "under_and_above": "Under the buy-below and above the trim-above"}
ZONE_LINE = ("Where the price sits is not a recommendation. A buy also needs a written thesis and a skeptic's review. Considering a trim needs a rise "
             "through the line, an intact thesis and a holding on file. This panel shows neither thesis nor holding.")
# The grey is the neutral already used on this page. It carries the band, and no series.
BAND = "#8f8d85"
TOP_ROWS = 8


def _inline(text):
    """A source from the inputs: https links stay as plain clicks, everything else is escaped."""
    out, last = [], 0
    for found in re.finditer(r"\[([^\]]+)\]\(([^)\s]+)\)", str(text)):
        out.append(e(str(text)[last:found.start()]))
        out.append(link(found[2], found[1]))
        last = found.end()
    out.append(e(str(text)[last:]))
    return "".join(out).replace("`", "")


def _share(value):
    return "Unknown" if value is None else f"{value:.1%}"


def _close_small(p):
    """The saved close's own source and date."""
    return f'{p["price"]["source"]}, close of {data.nice_date(p["price"]["date"])}, fetched {data.nice_date(p["price"]["fetched"].date())}. {p["price"]["folder"]}/{p["price"]["file"]}'


def book_unknown(book):
    """Why a share is Unknown, in words, and what would fill it. Empty when every close is on file."""
    if not book["missing"]:
        return ""
    lines = "".join(f'<li><b>{e(p["ticker"])}:</b> no saved close{": " + e(p["problem"]) if p["problem"] else ""}. {e(data.close_fill(p["ticker"]))}</li>' for p in book["positions"] if p["price"] is None)
    return (f'<div class="d-text"><p><b>Not on file: the close for {e(", ".join(book["missing"]))}.</b> So what it is worth today, the total, every share and the cash level are Unknown. '
            f'Nothing falls back to cost. What would fill it:</p><ul>{lines}</ul></div>')


def book_summary(book, today=None):
    """Cash, its share and its level, with each figure's source and date on its own row."""
    file, checked = book["file"], data.nice_date(book["last_checked"])
    from_note = e(f"{file}, last checked {checked}")
    closes = f'newest close {data.nice_date(book["newest_close"])}' if book["newest_close"] else "no closes needed, no positions"
    calc = e(f"calc., cash ÷ (cash + shares at the last saved close), {file}, {closes}, last checked {checked}")
    if book["missing"]:
        calc = e(f'calc. not possible: no saved close for {", ".join(book["missing"])}. A saved close for each would fill it. {file}, last checked {checked}')
    rows = [("Cash", f'${book["cash"]:,.0f}', from_note), ("Stocks at the last saved closes", "Unknown" if book["total"] is None else f'${book["total"] - book["cash"]:,.0f}', calc),
            ("Portfolio at the last saved closes", "Unknown" if book["total"] is None else f'${book["total"]:,.0f}', calc), ("Cash as a share of the portfolio", _share(book["share"]), calc),
            ("Cash level, Rules/cash.md", book["level"] or "Unknown", calc), ("Positions", str(len(book["positions"])), e(f"calc., counted in {file}, last checked {checked}"))]
    if book["above_50_since"]:
        since = data.nice_date(book["above_50_since"])
        if book["share"] is None:
            said = f"The note says since {since}. Today's share is Unknown."
        elif book["share"] > .5:
            said = f'Since {since}: {book["above_50_months"]} of 24 months so far'
        else:
            said = f'The note says since {since}, and cash is not above 50% at the last saved closes'
        rows.append(("Cash above 50%", said, e(f"calc., whole months from the date in {file}, last checked {checked}")))
    else:
        rows.append(("Cash above 50%", "Not on file. A cash above 50% since date in the note would fill it.", from_note))
    body = [f'<tr><td>{e(a)}</td><td class="d-num">{e(b)}</td><td class="d-muted d-src">{c}</td></tr>' for a, b, c in rows]
    return age_tag("portfolio_note", book["last_checked"], today) + _table(("", "Figure", "Source and date"), body, numeric=(1,))


def book_positions_table(book, pages=None, today=None):
    """Shares at the last saved close, each close with its own date. No close, no value and no share: Unknown, with no fallback to cost."""
    if not book["positions"]:
        return f'<p class="d-text">No positions in {e(book["file"])}, last checked {e(data.nice_date(book["last_checked"]))}.</p>'
    rows = []
    for p in book["positions"]:
        page = (pages or {}).get(p["ticker"])
        thesis = f'{company_link(page, p["thesis"])}' if page else _copied(p["thesis"], "Not stated. A thesis note in the row would fill it")
        note = e(f'{book["file"]}, last checked {data.nice_date(book["last_checked"])}')
        if p["price"]:
            close, day, value = _money(p["price"]["close"]), data.nice_date(p["price"]["date"]), f'${p["value"]:,.0f}'
            small = e(_close_small(p)) + ". Value: calc. " + note + age_tag("close", p["price"]["date"], today)
            if p["share"] is None:
                small += f' Its share is Unknown because another close is missing. A saved close for {e(", ".join(book["missing"]))} would fill it.'
        else:
            close, day, value = "Unknown", "Unknown", "Unknown"
            small = f'No saved close. {e(data.close_fill(p["ticker"]))} {note}'
        rows.append(f'<tr><td>{e(p["ticker"])}</td><td class="d-num">{p["shares"]:,.0f}</td><td>{e(p["bought"])}</td><td class="d-num">{_money(p["cost"])}</td><td class="d-num">{e(close)}</td>'
                    f'<td class="d-nowrap">{e(day)}</td><td class="d-num">{e(value)}</td><td class="d-num">{e(_share(p["share"]))}</td><td>{thesis}</td><td class="d-muted d-src">{small}</td></tr>')
    return _table(("Ticker", "Shares", "Bought on", "Cost a share", "Last saved close", "Close date", "Value at that close (calc.)", "Share of the portfolio (calc.)", "Thesis note", "Source and date"), rows, numeric=(1, 3, 4, 6, 7))


def book_changes_table(book):
    if not book["changes"]:
        return f'<p class="d-text">No changes written in {e(book["file"])}.</p>'
    rows = [f'<tr><td class="d-nowrap"><span class="d-copied">{e(c["date"])}</span></td><td><span class="d-copied">{e(c["change"])}</span></td><td class="d-num"><span class="d-copied">{e(c["cash"])}</span></td><td><span class="d-copied">{e(c["yes"])}</span></td></tr>' for c in book["changes"]]
    return _table(("Date", "Change", "Cash after", "My yes"), rows, numeric=(2,), caption=e(f'{book["file"]}, as written, last checked {data.nice_date(book["last_checked"])}'))


def book_block(book, pages=None, today=None):
    """One note's whole block, the same for real and paper. Paper's label is added by the screen and cannot be left off, a test checks."""
    return (book_summary(book, today) + book_unknown(book) + '<p class="d-chart-title">Positions</p>' + book_positions_table(book, pages, today)
            + '<p class="d-chart-title">Changes in the note</p>' + book_changes_table(book))


PAPER_LABEL = "PAPER. Made-up money, a lesson, not what I own and not advice."
LIMIT_MISSING = ("Room under the 5% limit, and names against bets.", "a saved run of the portfolio script, .claude/skills/portfolio-manager/scripts/pm.py. It needs a first position, and no run is saved. The board shows those fields only, never the script's action or size.")
REAL_MISSING = ("my real holdings and cash.", "a note in Portfolio/ marked kind: real. Only I change that folder.")


def _money(value):
    return "unknown" if value is None else ("−" if value < 0 else "") + f"${abs(value):,.2f}"


def _run_src(run, how="calc.,"):
    worked = data.nice_date(run["worked_out"])
    return src_markup(e(f'{how} {run["run_file"]}, worked out {worked}'))


def value_summary(run):
    """What the panel reads, and what else the rules need. It names no zone: I read the zones myself (my ruling, Nov. 4, 2026)."""
    worked = data.nice_date(run["worked_out"])
    return (f'<p class="d-muted d-text">This panel reads only {e(run["run_file"])}. Values worked out {e(worked)}. For a newer run, start sensors/valuation/save.py by hand, then reload.</p>'
            f'<p>{e(ZONE_LINE)}</p>')


def value_table(run):
    b, p, c = run["base"], run["price"], run["coverage"]
    worked = data.nice_date(run["worked_out"])
    calc = f"calc., worked out {worked}, inputs below"
    bar = "met" if c["met"] else "not met"
    rows = [("Base value, low to high", f'{_money(b["low"])} to {_money(b["high"])}', e(calc)),
            ("Base value, middle", _money(b["mid"]), e(calc)),
            ("Price", _money(p["close"]), _inline(p["src"])),
            ("Coverage", f'{c["mid"]:.1%}', e(f'calc., middle ÷ price, worked out {worked}. Range {c["low"]:.1%} to {c["high"]:.1%}. Bar 75%: {bar}.')),
            ("Buy-below", _money(run["buy_below"]), e(f'calc., {_money(b["mid"])} ÷ 0.75, worked out {worked}')),
            ("Strategic value", _money(run["strategic"]), e(f"{calc}. Never part of coverage. Scenarios are forecasts, not results.")),
            ("Trim-above", _money(run["trim_above"]), e(f'calc., {_money(b["mid"])} + {_money(run["strategic"])}, worked out {worked}'))]
    return _table(["Measure", "Figure", "Source and date"], [f'<tr><td>{e(a)}</td><td class="d-num d-nowrap">{e(x)}</td><td class="d-muted d-src">{y}</td></tr>' for a, x, y in rows], numeric=(1,))


def value_no_vote(run):
    need = run["growth_needed"]
    rows = [f'<tr><td>{e(r["name"])}</td><td class="d-num">{e(_money(r["low"]))}</td><td class="d-num">{e(_money(r["mid"]))}</td><td class="d-num">{e(_money(r["high"]))}</td></tr>' for r in run["no_vote"]]
    return (_table(["No vote, always shown", "Low", "Middle", "High"], rows, numeric=(1, 2, 3), caption=e(f'calc., {run["run_file"]}, worked out {data.nice_date(run["worked_out"])}'))
            + sourced(f'<p class="d-muted">Growth the price needs, ten years then 3%, at 9%, no vote: {need["from_high"]:.1%} from the high cash reading, {need["from_mid"]:.1%} from the middle (calc.).</p>', _run_src(run)))


def value_inputs_table(run):
    worked = data.nice_date(run["worked_out"])
    rows = [f'<tr><td>{e(r["label"])}</td><td class="d-num">{e(f"{r["v"]:,.4g}")}</td><td class="d-muted d-src">{_inline(r["src"])}</td></tr>' for r in run["inputs"]]
    rows += [f'<tr><td>{e(s["name"])}</td><td class="d-num">{e(f"{s["chance"]:.0%}")} × {e(_money(s["full"]))}</td><td class="d-muted d-src">{e(_money(s["value"]))} a share (calc., worked out {e(worked)}). Chance {e(s["status"] or "not stated")}.</td></tr>' for s in run["scenarios"]]
    return _table(["Input", "Value", "Source and date"], rows, numeric=(1,))


def value_layers(run):
    """The two layers, apart: what is proven, and what may come later. Only the run is read."""
    b, worked = run["base"], data.nice_date(run["worked_out"])
    calc = e(f'calc., {run["run_file"]}, worked out {worked}')
    names = {"earn": "Normal earnings ÷ 9%, 40% of the vote", "cash": "The cash sum at 9%, 40% of the vote", "bond": "Normal earnings ÷ the Aaa yield, 20% of the vote"}
    money = lambda row: "".join(f'<td class="d-num">{e(_money(row[k]))}</td>' for k in ("low", "mid", "high"))  # noqa: E731
    base_rows = [f'<tr><td><b>Base value</b></td>{money(b)}</tr>']
    base_rows += [f'<tr><td>{e(names.get(k, k))}</td>{money(v)}</tr>' for k, v in b.get("votes", {}).items()]
    rows = [f'<tr><td>{e(s["name"])}</td><td class="d-num">{e(_money(s["full"]))}</td><td class="d-num">{e(f"{s["chance"]:.0%}")}</td><td class="d-num">{e(_money(s["value"]))}</td><td>{e(s["status"] or "Not stated")}</td></tr>' for s in run["scenarios"]]
    rows.append(f'<tr><td><b>Strategic value</b></td><td></td><td></td><td class="d-num"><b>{e(_money(run["strategic"]))}</b></td><td></td></tr>')
    return ('<p class="c-layer">Layer one, base value: what the business has already proven</p>'
            + _table(["A share", "Low", "Middle", "High"], base_rows, numeric=(1, 2, 3), caption=calc)
            + '<p class="c-layer">Layer two, strategic value: what may come later, as scenarios and their chances</p>'
            + '<p class="d-muted">Forecasts, not results. It adds to the trim-above line and never counts toward coverage.</p>'
            + _table(["Scenario", "Full amount a share", "Chance", "Amount × chance", "Chance status"], rows, numeric=(1, 2, 3), caption=calc))


def price_zones(run, close, today=None):
    """The zones beside the last saved close, each with its own date. It never says which zone that close is in: the board compares no close to a line."""
    buy, trim, p = run["buy_below"], run["trim_above"], run["price"]
    worked = data.nice_date(run["worked_out"])
    newest = (fig(_money(close["close"]), (f'Last saved close, {data.nice_date(close["date"])}. {close["source"]}, fetched {data.nice_date(close["fetched"].date())}. {close["folder"]}/{close["file"]}', None), data.nice_date(close["date"]))
              if close else f'<div class="d-text">Last saved close: not on file. This page does not fetch one. {e(data.close_fill(run.get("ticker") or data.CORNING))}</div>')
    used = f'<span class="d-fig"><b class="d-val">{e(_money(p["close"]))}</b>{src_markup("The close the run used: " + _inline(p["src"]))}</span>'
    ranges = [(ZONE_WORDS["under"], f"Under {_money(buy)}"), (ZONE_WORDS["above"], f"Above {_money(trim)}")]
    ranges.insert(1, (ZONE_WORDS["between"], f"{_money(buy)} to {_money(trim)}") if buy <= trim else (ZONE_WORDS["under_and_above"], f"{_money(trim)} to {_money(buy)}"))
    calc = f'calc., {run["run_file"]}, worked out {worked}'
    rows = [f'<tr><td>{e(a)}</td><td class="d-num d-nowrap">{e(x)}</td></tr>' for a, x in ranges]
    ages = (age_tag("close", close["date"], today) if close else "") + age_tag("value_run", run["worked_out"], today)
    return (f'{ages}<div class="c-side"><div class="c-closes">{newest}{used}</div><div class="c-zones">'
            + _table(["Price zone", "Close, USD"], rows, numeric=(1,), caption=e(calc))
            + '<p class="d-muted">The two dates can differ. This page sets no close against a line, so for the last saved close read the zone by eye.</p></div></div>')


def _spread(values, top, plot_px=340, gap_px=16):
    """Label heights, in dollars, pushed apart just enough to read. The lines themselves stay at their figures."""
    gap = max(top, 1) / plot_px * gap_px
    placed, floor = {}, None
    for i in sorted(range(len(values)), key=lambda i: values[i]):
        placed[i] = values[i] if floor is None else max(values[i], floor + gap)
        floor = placed[i]
    return [placed[i] for i in range(len(values))]


def value_chart(run, theme="light"):
    """The price over time. The band and lines are one date's values drawn flat, so read the price against them, not value in the past."""
    inks = _inks(theme)
    frame = pd.DataFrame(run["series"], columns=["Label", "Close"])
    frame["Day"] = pd.to_datetime(frame["Label"])
    first, last = frame["Day"].min(), frame["Day"].max()
    room = last + pd.DateOffset(years=7)  # space for the end labels
    close_name = f'{run.get("ticker") or run["company"]} close'
    names = [close_name, "Trim-above", "Buy-below", "Base range"]
    scale = alt.Scale(domain=names, range=[inks["slots"][0], inks["slots"][1], inks["slots"][2], BAND])
    years = [dt.date(y, 1, 1).isoformat() for y in range(first.year + 1, last.year + 1, 2)]
    x = alt.X("Day:T", title=None, scale=alt.Scale(domain=[first.isoformat(), room.isoformat()]), axis=alt.Axis(format="%Y", values=years, grid=False))
    y = alt.Y("Close:Q", title="USD a share", scale=alt.Scale(zero=True), axis=alt.Axis(gridColor=inks["axis"], gridOpacity=0.35, domain=False, tickSize=0))
    color = alt.Color("Series:N", scale=scale, title=None, sort=names, legend=alt.Legend(orient="top", direction="horizontal", labelColor=inks["ink"], labelFontSize=13, symbolOpacity=1))
    b = run["base"]
    ends = pd.DataFrame({"Day": [first, last]})
    band = alt.Chart(ends.assign(Close=b["low"], High=b["high"], Series="Base range")).mark_area(opacity=.3).encode(x=x, y=y, y2="High:Q", color=color)
    flat = pd.concat([ends.assign(Close=run["trim_above"], Series="Trim-above"), ends.assign(Close=run["buy_below"], Series="Buy-below")])
    lines = alt.Chart(flat).mark_line(strokeWidth=2).encode(x=x, y=y, color=color)
    price = alt.Chart(frame.assign(Series=close_name)).mark_line(strokeWidth=1.5, strokeJoin="round").encode(x=x, y=y, color=color)
    tag_rows = [(run["price"]["close"], _money(run["price"]["close"])), (run["trim_above"], f'Trim-above {_money(run["trim_above"])}'),
                (run["buy_below"], f'Buy-below {_money(run["buy_below"])}'), (b["mid"], f'Base {_money(b["low"])} to {_money(b["high"])}')]
    tags = pd.DataFrame({"Day": [last] * 4, "Close": _spread([v for v, _ in tag_rows], frame["Close"].max()), "Text": [t for _, t in tag_rows]})
    labels = alt.Chart(tags).mark_text(align="left", dx=8, fontSize=12, fontWeight=600, color=inks["ink"]).encode(x=x, y=y, text="Text:N")
    hover = alt.selection_point(fields=["Label"], nearest=True, on="pointerover", clear="pointerout", empty=False)
    tips = [alt.Tooltip("Label:N", title="Date"), alt.Tooltip("Close:Q", title="Close, USD", format=".2f")]
    catcher = alt.Chart(frame).mark_point(opacity=0, size=200).encode(x=x, y=y, tooltip=tips).add_params(hover)
    rule = alt.Chart(frame).mark_rule(color=inks["axis"], strokeWidth=1).encode(x=x).transform_filter(hover)
    return _style(alt.layer(rule, band, lines, price, labels, catcher), 400, theme)


def _row_mark(row):
    return " †" if row["ends"] else " *" if any(x["flags"] for x in row["readings"]) else ""


def _method_figure(run, out):
    return {"base": run["base"]["mid"], "buy": run["buy_below"], "trim": run["trim_above"]}[out]


def what_if_frames(run, out, limit=TOP_ROWS):
    """The widest rows for one output: a bar from the lowest reading to the method's figure and on to the highest."""
    by_key = {r["key"]: r for r in run["what_if"]["rows"]}
    method, bars, ends = _method_figure(run, out), [], []
    order = []
    for key in run["what_if"]["ranked"][out][:limit]:
        row = by_key[key]
        name = row["label"] + _row_mark(row)
        order.append(name)
        lowest, highest = min(row["readings"], key=lambda x: x[out]), max(row["readings"], key=lambda x: x[out])
        for side, reading in (("Lower reading", lowest), ("Higher reading", highest)):
            if (side == "Lower reading" and reading[out] >= method - 1e-9) or (side == "Higher reading" and reading[out] <= method + 1e-9):
                continue
            bars.append({"Name": name, "Side": side, "Start": method, "End": reading[out], "Reading": reading["text"], "Method": row["method"], "Value": reading[out]})
            ends.append({"Name": name, "End": reading[out], "Side": side, "Text": _money(reading[out])})
    return order, pd.DataFrame(bars), pd.DataFrame(ends)


def what_if_chart(run, out, theme="light", limit=TOP_ROWS):
    inks = _inks(theme)
    order, bars, ends = what_if_frames(run, out, limit)
    method = _method_figure(run, out)
    scale = alt.Scale(domain=["Lower reading", "Higher reading"], range=[inks["slots"][0], inks["slots"][1]])
    low, high = bars["End"].min(), bars["End"].max()
    pad = max((high - low) * .16, .5)
    x = alt.X("Start:Q", title="USD a share", scale=alt.Scale(domain=[low - pad, high + pad], zero=False, nice=False), axis=alt.Axis(gridColor=inks["axis"], gridOpacity=0.35, domain=False, tickSize=0, tickCount=6, format="$,.0f"))
    y = alt.Y("Name:N", title=None, sort=order, axis=alt.Axis(labelLimit=290, labelOverlap=False, ticks=False, domain=False, grid=False))
    tips = [alt.Tooltip("Name:N", title="Assumption"), alt.Tooltip("Method:N", title="Method's reading"), alt.Tooltip("Reading:N", title="This reading"), alt.Tooltip("Value:Q", title="Gives, USD (calc.)", format="$.2f")]
    drawn = alt.Chart(bars).mark_bar(height=16, cornerRadius=3).encode(x=x, x2="End:Q", y=y, tooltip=tips,
                                                                      color=alt.Color("Side:N", scale=scale, title=None, sort=["Lower reading", "Higher reading"], legend=alt.Legend(orient="top", direction="horizontal", labelColor=inks["ink"], labelFontSize=12)))
    centre = alt.Chart(pd.DataFrame({"Start": [method]})).mark_rule(color=inks["ink"], strokeWidth=1.5).encode(x=x)
    ex = alt.X("End:Q", scale=alt.Scale(domain=[low - pad, high + pad], zero=False, nice=False), title="USD a share")
    below = alt.Chart(ends[ends["Side"] == "Lower reading"]).mark_text(align="right", dx=-5, fontSize=12, color=inks["ink"]).encode(x=ex, y=y, text="Text:N")
    above = alt.Chart(ends[ends["Side"] == "Higher reading"]).mark_text(align="left", dx=5, fontSize=12, color=inks["ink"]).encode(x=ex, y=y, text="Text:N")
    return _style(alt.layer(drawn, centre, below, above), alt.Step(30), theme)


def what_if_lead(run):
    w = run["what_if"]
    by_key = {r["key"]: r for r in w["rows"]}
    names = {"base": "the base middle", "buy": "the buy-below", "trim": "the trim-above"}
    most = w["most"]
    if len(set(most.values())) == 1:
        top = by_key[most["base"]]
        first = f'{top["label"]} is the widest on all three: ' + ", ".join(f'{_money(top["swing"][o])} on {names[o]}' for o in names) + " (calc.)."
    else:
        first = " ".join(f'On {names[o]} the widest is {by_key[most[o]]["label"]}, {_money(by_key[most[o]]["swing"][o])} (calc.).' for o in names)
    changes = w["zone_changes"]
    second = (f'No reading here changes the zone. The highest coverage in any of them is {w["highest_coverage"]:.1%} (calc.).' if not changes else
              "Readings that change the zone: " + ", ".join(by_key[k]["label"] for k in changes) + f'. The highest coverage in any of them is {w["highest_coverage"]:.1%} (calc.).')
    return (sourced(f'<p><b>{e(w["label"])}</b> Nothing here is saved outside this run. {e(first)} {e(second)}</p>', _run_src(run))
            + '<p class="d-muted">"Widest" leaves out the rows marked † or *. † shows the far ends of a method choice, not a reading anyone has proposed. * has a reading that breaks the method\'s own shape, such as the ladder of chances. '
            'Those rows are still drawn. The ranking rests on the ranges chosen, each with its basis in the table below. The upright line is the method\'s figure. Hover a bar for its reading.</p>')


def what_if_table(run):
    out = []
    for row in sorted(run["what_if"]["rows"], key=lambda r: -r["swing"]["trim"]):
        for i, x in enumerate(row["readings"]):
            flag = f'<div class="d-muted">{e("; ".join(x["flags"]))}</div>' if x["flags"] else ""
            first = f'<td rowspan="{len(row["readings"])}">{e(row["label"] + _row_mark(row))}<div class="d-muted">{_inline(row["basis"])}</div></td><td rowspan="{len(row["readings"])}">{e(row["method"])}</td>' if i == 0 else ""
            out.append(f'<tr>{first}<td>{e(x["text"])}{flag}</td><td class="d-num">{e(_money(x["base"]))}</td><td class="d-num">{e(_money(x["buy"]))}</td><td class="d-num">{e(_money(x["trim"]))}</td><td class="d-num">{e(f"{x["coverage"]:.1%}")}</td></tr>')
    return _table(["Assumption and basis", "Method", "Reading", "Base middle", "Buy-below", "Trim-above", "Coverage"], out, numeric=(3, 4, 5, 6), caption=e(f'What-if, calc., {run["run_file"]}, worked out {data.nice_date(run["worked_out"])}'))


def what_if_slopes(run):
    rows = [f'<tr><td>{e(s["label"])}</td><td class="d-num">{s["base"] * 100:+.2f}%</td><td class="d-num">{s["trim"] * 100:+.2f}%</td></tr>' for s in run["what_if"]["slopes"]]
    return _table(["A 1% rise in this input", "Base middle and buy-below", "Trim-above"], rows, numeric=(1, 2), caption=e(f'What-if, calc., {run["run_file"]}, worked out {data.nice_date(run["worked_out"])}'))


# ---- Corning financial health ----

CHECK_MARK = {health.MATCH: "✓", health.APPROX: "≈", health.DIFF: "≠", health.ABSENT: "–", health.NO_FILING: "–", health.UNREAD: "?"}
# Slots 1 to 3 of the validated categorical palette, one colour for each role in a chart. Status colours are fixed in both themes.
SLOTS = {"light": ("#2a78d6", "#eb6834", "#1baf7a"), "dark": ("#3987e5", "#d95926", "#199e70")}
GOOD, AMBER, CRITICAL, NEUTRAL = "#0ca30c", "#fab219", "#d03b3b", "#8f8d85"


def _inks(theme):
    dark = theme == "dark"
    return {"ink": "#f0efec" if dark else "#0b0b0b", "axis": "#5a5a55" if dark else "#a9a89e", "slots": SLOTS["dark" if dark else "light"]}


def _value(text):
    return health.millions(text)


def _rich(cell):
    """A cell from the note with its links made safe: https links stay, everything else is escaped text."""
    out, last = [], 0
    refs = _rich.refs
    for found in re.finditer(r"\[([^\]]+)\]\[([^\]]+)\]", cell):
        out.append(e(cell[last:found.start()]))
        out.append(link(refs.get(found[2]), found[1]))
        last = found.end()
    out.append(e(cell[last:]))
    return "".join(out).replace("`", "")


_rich.refs = {}


def _row_check(measure, rows):
    """One line for a summary row: how its numbers tied."""
    mine = [r for r in rows if r["group"] == "Summary" and r["item"].startswith(measure)]
    if any(health.DIFF in (r["tenk_result"], r["other_result"]) or health.UNREAD in (r["tenk_result"], r["other_result"]) for r in mine):
        return "≠ See the check below"
    in_10k = sum(r["tenk_result"] == health.MATCH for r in mine)
    if any(r["other_result"] == health.APPROX for r in mine):
        return "– Not in this 10-K. ✓ Matches its own filing, ≈ one figure approximate"
    if in_10k == len(mine):
        return "✓ Matches the 10-K"
    if all(r["tenk_result"] == health.NO_FILING for r in mine):
        return "– No filing number. ✓ Matches the page that holds the rows"
    if any(r["tenk_result"] == health.NO_FILING for r in mine):
        return "– Mixed: some are our own calc. See the check below"
    if in_10k:
        return f"✓ {in_10k} of {len(mine)} match the 10-K, the rest their own filing"
    return "– Not in this 10-K. ✓ Matches its own filing"


def health_summary(note, rows):
    _rich.refs = note["refs"]
    out = []
    for r in note["summary"]:
        out.append(f'<tr><td>{e(r["measure"])}</td><td>{e(r["figure"])}</td><td class="d-src">{_rich(r["filing_text"])}</td><td>{e(r["means"])}</td>'
                   f'<td class="d-muted">{e(_row_check(r["measure"], rows))}</td></tr>')
    return _table(["Measure", "Figure", "Filing and date", "What it means", "Check"], out)


def check_headline(result):
    rows, tally, other = result["rows"], result["tally"], result["other"]
    tenk = result["tenk"]
    source = link(tenk["url"], data.nice_date(tenk["filed"]))
    diffs = [r for r in rows if health.DIFF in (r["tenk_result"], r["other_result"])]
    unread = [r for r in rows if health.UNREAD in (r["tenk_result"], r["other_result"])]
    lines = [f'<p><b>{len(rows)} numbers checked against the latest 10-K, filed {source}. {tally[health.MATCH]} match, '
             f'{tally[health.DIFF]} differ, {tally[health.ABSENT]} are not in that 10-K, and {tally[health.NO_FILING]} are not filing numbers (our own calc. and counts).</b></p>',
             f'<p>That 10-K reports only FY2023 to FY2025 and ends on Dec. 31, 2025. Older years, the 2026 figures and most single quarters cannot tie to it. '
             f'Those are tied to the filing they come from, except the normalized average, tied to its ten figures in the note, and the counts, tied to their pages: {other[health.MATCH]} match, {other[health.APPROX]} matches but is approximate, and {other[health.DIFF]} differ. '
             f'{len(unread)} could not be read. Filing numbers are read from the saved copies, not typed in, and this page does not fetch them.</p>']
    for r in diffs:
        lines.append(f'<p>Difference of {e(r.get("gap", ""))}: {e(r["item"])}, {e(r["ours"])} in the note. {e(r["how"])}</p>')
    return sourced("".join(lines), src_markup(f'Our numbers: Companies/Corning.md. Filing numbers: 10-K, filed {source}, and each filing in the table below.'))


def _result(text, gap=""):
    if text is None:
        return ""
    mark = CHECK_MARK[text]
    extra = f" {gap}" if gap and text in (health.DIFF, health.UNREAD) else ""
    css = "d-result-diff" if text in (health.DIFF, health.UNREAD) else "d-result-match"
    return f'<span class="d-result {css}">{mark} {e(text)}{e(extra)}</span>'


def check_table(rows, caption=""):
    """`caption` names the note and the 10-K with their dates. A row also names any other filing it was checked in."""
    out = []
    for r in rows:
        how = f'<div class="d-muted">{e(r["how"])}</div>' if r["how"] else ""
        gap = r.get("gap", "")
        tenk_gap = gap if r["other_result"] is None else ""
        other_gap = gap if r["other_result"] is not None else ""
        source = r["source"]
        where = link(source[1], source[0]) if source and source[1] else e(source[0]) if source else ""
        out.append(f'<tr><td>{e(r["item"])}{how}</td><td class="d-num">{e(r["ours"])}</td><td class="d-num">{e(r["tenk"] or "")}</td>'
                   f'<td>{_result(r["tenk_result"], tenk_gap)}</td><td>{where}</td><td class="d-num">{e(r["other"] or "")}</td><td>{_result(r["other_result"], other_gap)}</td></tr>')
    return _table(["Number", "Our number", "10-K number", "Against the 10-K", "If not there, checked in", "Its number", "Result"], out, numeric=(1, 2, 5), caption=caption)


def scoreboard_html(board, small=""):
    def bar(title, items, note):
        total = sum(n for _, n, _ in items)
        parts = "".join(f'<i style="--c:{c};flex-grow:{n}" title="{e(label, quote=True)}: {n} of {total}"></i>' for label, n, c in items)
        keys = "".join(f'<span><i style="--c:{c}"></i><b>{n}</b> {e(label)}</span>' for label, n, c in items)
        return f'<div class="d-score"><h5>{e(title)}, {total}</h5><div class="d-bar">{parts}</div><div class="d-keys">{keys}</div><div class="d-muted">{e(note)}</div></div>'

    t, f = board["tests"], board["flags"]
    count = lambda part: int(health._amount(part)[0])  # noqa: E731
    return sourced('<p class="d-chart-title">Test and flag counts</p>'
            + bar("Classic value tests", [("pass", count(t["pass"]), GOOD), ("fail", count(t["fail"]), CRITICAL), ("not settled", count(t["not settled"]), NEUTRAL)],
                  "Evidence, not a gate, and not a score: several rows share one fact. Price tests are left out.")
            + bar("Red flags", [("clear", count(f["clear"]), GOOD), ("watch", count(f["watch"]), AMBER), ("concern", count(f["concern"]), CRITICAL)],
                  f'{count(f["of watch, not tested"])} of the watch flags are simply not tested.'), small)


def _style(chart, height, theme):
    text = "#c3c2b7" if theme == "dark" else "#52514e"
    return chart.properties(height=height).configure_view(strokeWidth=0).configure_axis(labelFontSize=12, titleFontSize=12, labelColor=text, titleColor=text)


def _year_axis(field, order=None, title=None, angle=0):
    return alt.X(field, title=title, sort=order, axis=alt.Axis(labelAngle=angle, grid=False, ticks=False))


def _dollar_axis(inks, title="$M"):
    return alt.Y("Amount:Q", title=title, axis=alt.Axis(format=",.0f", gridColor=inks["axis"], gridOpacity=0.35, domain=False, tickSize=0))


def margins_chart(note, theme="light"):
    inks = _inks(theme)
    names = {"gross": "Gross", "operating": "Operating", "net": "Net"}
    rows = [{"Year": str(y["year"]), "Series": names[k], "Percent": _value(y[k])} for y in note["years"] for k in names]
    frame = pd.DataFrame(rows)
    order = sorted(frame["Year"].unique())
    scale = alt.Scale(domain=list(names.values()), range=list(inks["slots"]))
    x = _year_axis("Year:O", order)
    y = alt.Y("Percent:Q", title="Percent of sales (calc.)", axis=alt.Axis(gridColor=inks["axis"], gridOpacity=0.35, domain=False, tickSize=0))
    lines = alt.Chart(frame).mark_line(strokeWidth=2, strokeCap="round", strokeJoin="round", point=alt.OverlayMarkDef(size=45, filled=True)).encode(
        x=x, y=y, color=alt.Color("Series:N", scale=scale, title=None, legend=alt.Legend(orient="top", direction="horizontal", labelColor=inks["ink"])),
        tooltip=[alt.Tooltip("Year:O"), alt.Tooltip("Series:N"), alt.Tooltip("Percent:Q", format=".1f")])
    ends = frame[frame["Year"] == order[-1]].copy()
    ends["Text"] = ends["Percent"].map("{:.1f}%".format)
    labels = alt.Chart(ends).mark_text(align="left", dx=7, fontSize=12, fontWeight=600, color=inks["ink"]).encode(x=x, y=y, text="Text:N", tooltip=alt.value(None))
    # An invisible, larger point per value catches the pointer, because the drawn points are small.
    catcher = alt.Chart(frame).mark_point(opacity=0, size=500).encode(x=x, y=y, tooltip=[alt.Tooltip("Year:O"), alt.Tooltip("Series:N"), alt.Tooltip("Percent:Q", format=".1f")])
    return _style(alt.layer(lines, labels, catcher).properties(padding={"right": 38}), 240, theme)


def gaap_core_chart(note, theme="light"):
    inks = _inks(theme)
    rows = []
    for q in reversed(note["quarters"]):
        rows += [{"Quarter": q["quarter"], "Series": "GAAP", "Amount": _value(q["gaap"])}, {"Quarter": q["quarter"], "Series": "Core", "Amount": _value(q["core"])}]
    frame = pd.DataFrame(rows)
    order = [q["quarter"] for q in reversed(note["quarters"])]
    scale = alt.Scale(domain=["GAAP", "Core"], range=list(inks["slots"][:2]))
    chart = alt.Chart(frame).mark_bar(size=11, cornerRadiusEnd=3).encode(
        x=_year_axis("Quarter:O", order, angle=-35), xOffset=alt.XOffset("Series:N", sort=["GAAP", "Core"]), y=_dollar_axis(inks, "Net income, $M"),
        color=alt.Color("Series:N", scale=scale, title=None, legend=alt.Legend(orient="top", direction="horizontal", labelColor=inks["ink"])),
        tooltip=[alt.Tooltip("Quarter:O"), alt.Tooltip("Series:N"), alt.Tooltip("Amount:Q", format=",.0f", title="$M")])
    return _style(chart, 240, theme)


def fcf_chart(note, theme="light"):
    inks = _inks(theme)
    frame = pd.DataFrame([{"Year": str(y["year"]), "Amount": _value(y["fcf"]), "Cash": _value(y["ocf"]), "Capex": _value(y["capex"])} for y in note["years"]])
    order = sorted(frame["Year"])
    x = _year_axis("Year:O", order)
    bars = alt.Chart(frame).mark_bar(size=20, cornerRadiusEnd=4, color=inks["slots"][0]).encode(
        x=x, y=_dollar_axis(inks, "Free cash flow, $M (calc.)"),
        tooltip=[alt.Tooltip("Year:O"), alt.Tooltip("Amount:Q", format=",.0f", title="Free cash flow, $M"),
                 alt.Tooltip("Cash:Q", format=",.0f", title="Operating cash flow, $M"), alt.Tooltip("Capex:Q", format=",.0f", title="Capex, $M")])
    last = frame[frame["Year"] == order[-1]].copy()
    last["Text"] = last["Amount"].map("${:,.0f}M".format)
    label = alt.Chart(last).mark_text(dy=-8, fontSize=12, fontWeight=600, color=inks["ink"]).encode(x=x, y="Amount:Q", text="Text:N", tooltip=alt.value(None))
    return _style(alt.layer(bars, label), 220, theme)


def deposit_chart(note, theme="light"):
    inks = _inks(theme)
    rows = []
    for w in reversed(note["watch"]):
        without = _value(w["without"])
        rows.append({"Period": w["period"], "Part": "Without stated deposits", "Amount": without, "Shown": w["without"], "Step": 0, "Total": _value(w["fcf"]), "Stated": w["deposits"]})
        if re.search(r"\d", w["deposits"]):
            rows.append({"Period": w["period"], "Part": "Stated deposits", "Amount": _value(w["deposits"]), "Shown": w["deposits"], "Step": 1, "Total": _value(w["fcf"]), "Stated": w["deposits"]})
    frame = pd.DataFrame(rows)
    order = [w["period"] for w in reversed(note["watch"])]
    scale = alt.Scale(domain=["Without stated deposits", "Stated deposits"], range=list(inks["slots"][:2]))
    x = _year_axis("Period:N", order)
    bars = alt.Chart(frame).mark_bar(size=24, stroke=None).encode(
        x=x, y=alt.Y("Amount:Q", stack=True, title="Free cash flow, $M (calc.)", axis=alt.Axis(format=",.0f", gridColor=inks["axis"], gridOpacity=0.35, domain=False, tickSize=0)),
        order=alt.Order("Step:O"),
        color=alt.Color("Part:N", scale=scale, title=None, legend=alt.Legend(orient="top", direction="horizontal", labelColor=inks["ink"], labelLimit=200)),
        tooltip=[alt.Tooltip("Period:N"), alt.Tooltip("Part:N"), alt.Tooltip("Shown:N", title="Amount"), alt.Tooltip("Stated:N", title="Deposits stated in the filing")])
    tops = frame.drop_duplicates("Period").copy()
    tops["Text"] = tops["Total"].map("${:,.0f}M".format)
    labels = alt.Chart(tops).mark_text(dy=-8, fontSize=12, fontWeight=600, color=inks["ink"]).encode(x=x, y="Total:Q", text="Text:N", tooltip=alt.value(None))
    return _style(alt.layer(bars, labels), 220, theme)


def deposit_line_table(note):
    """The second reading: free cash flow without the whole filed deposits line."""
    rows = [f'<tr><td>{e(w["period"])}</td><td class="d-num">{e(w["fcf"])}</td><td class="d-num">{e(w["line"])}</td><td class="d-num">{e(w["without"])}</td>'
            f'<td class="d-src">{link(w["url"], w["filing"])}</td></tr>' for w in note["watch_line"]]
    return _table(["Period", "Free cash flow", "Filed line", "Without it (calc.)", "Source"], rows, numeric=(1, 2, 3))


def deposit_estimate_table(note):
    """The third reading, an estimate: the deposit out, older deposits applied added back."""
    rows = [f'<tr><td>{e(w["period"])}</td><td class="d-num">{e(w["fcf"])}</td><td class="d-num">{e(w["deposit"])}</td><td class="d-num">{e(w["applied"])}</td>'
            f'<td class="d-num">{e(w["estimate"])}</td><td class="d-src">{link(w["url"], w["filing"])}</td></tr>' for w in note["watch_estimate"]]
    return _table(["Period", "Free cash flow", "Deposit out", "Older deposits back", "Estimate (calc.)", "Source"], rows, numeric=(1, 2, 3, 4))


def ladder_chart(note, theme="light"):
    inks = _inks(theme)
    frame = pd.DataFrame([{"Due": r["due"], "Amount": _value(r["amount"]), "Text": r["amount"]} for r in note["ladder"]])
    x = _year_axis("Due:N", list(frame["Due"]))
    bars = alt.Chart(frame).mark_bar(size=24, cornerRadiusEnd=4, color=inks["slots"][0]).encode(
        x=x, y=_dollar_axis(inks, "Due, $M"), tooltip=[alt.Tooltip("Due:N"), alt.Tooltip("Amount:Q", format=",.0f", title="$M")])
    labels = alt.Chart(frame).mark_text(dy=-8, fontSize=12, fontWeight=600, color=inks["ink"]).encode(x=x, y="Amount:Q", text="Text:N", tooltip=alt.value(None))
    return _style(alt.layer(bars, labels), 220, theme)


# ---- Company page ----

COACH_LINE = "About to decide? The coach comes first."
# Fixed words. No argument can turn this off: whatever Research/ holds is a draft until I record a thesis in the note.
DRAFT_LABEL = "DRAFT, NOT APPROVED. Nothing in this block is a recorded thesis. It stays a draft until I record one in the note."
NO_SOURCE = "No dated source on this line. A dated link in the note would fill it"
# What counts as a figure in a line copied from a note. A plain date or a claim number does not.
NOTE_FIGURE = re.compile(r"\$\s?\d|\d\s?%|\b\d[\d,.]*\s?(?:M|B|million|billion|trillion)\b")
NOTE_SOURCE = re.compile(r"\[[^\]]*\b(?:19|20)\d\d\b[^\]]*\](?:\(|\[)|calc\.|undated, retrieved|`[^`]+`,? [^`]*\b(?:19|20)\d\d\b")
_NOTE_TOKEN = re.compile(r"!?\[\[([^\]|]+)(?:\|([^\]]+))?\]\]|!?\[([^\]]+)\]\(([^)\s]+)\)|!?\[([^\]]+)\]\[([^\]]*)\]|(`[^`]+`(?:, [A-Z][a-z]+\.? \d{1,2}, \d{4})?)|(\*\*)")
_A_YEAR = re.compile(r"\b(?:19|20)\d\d\b")


def company_href(row):
    safe = "".join(ch if ch.isascii() and (ch.isalnum() or ch in "-._~") else "".join(f"%{b:02X}" for b in ch.encode()) for ch in data.company_slug(row))
    return f"/company?company={safe}"


def company_link(row, words=None):
    return f'<a href="{e(company_href(row), quote=True)}" target="_self">{e(words or row["name"])}</a>'


def _cited(label, url):
    """A source from a note. Any https link stays a plain click, and anything else stays text. A dated one is marked, so a test can find it."""
    inner = link(url, label)
    return f"<cite>{inner}</cite>" if _A_YEAR.search(label) else inner


def note_inline(text, refs=None, pages=None):
    """One line of a note as safe markup. It keeps the words and never makes an image or a fetch. A [[name]] is a click only if that company has a page."""
    refs, pages = refs or {}, pages or {}
    out, last, bold = [], 0, False
    for found in _NOTE_TOKEN.finditer(text):
        out.append(e(text[last:found.start()]))
        last = found.end()
        if found[1]:
            shown = found[2] or found[1]
            out.append(company_link(pages[found[1]], shown) if found[1] in pages else e(shown))
        elif found[3]:
            out.append(_cited(found[3], found[4]))
        elif found[5]:
            out.append(_cited(found[5], refs.get(found[6] or found[5])))
        elif found[7]:
            word = found[7].replace("`", "")
            out.append(f"<cite>{e(word)}</cite>" if _A_YEAR.search(word) else e(word))
        else:
            out.append("</b>" if bold else "<b>")
            bold = not bold
    out.append(e(text[last:]))
    return "".join(out) + ("</b>" if bold else "")


def _flag(*cells):
    """A copied line with a figure and no dated source says so on the page, because the page cannot supply one."""
    joined = " ".join(cells)
    return f'<small class="d-nosrc">{NO_SOURCE}</small>' if NOTE_FIGURE.search(joined) and not NOTE_SOURCE.search(joined) else ""


def note_table(headers, rows, refs=None, pages=None, caption="", flag_lines=True):
    """A table as the note has it, cell for cell. A row with a figure and no source says so, unless `caption` or a dated block around it gives the source of all of them."""
    head = "".join(f'<th><span class="d-copied">{note_inline(h, refs, pages)}</span></th>' for h in headers)
    body = []
    for row in rows:
        flag = "" if caption or not flag_lines else _flag(*row)
        cells = "".join(f'<td>{flag if i == 0 else ""}<span class="d-copied">{note_inline(cell, refs, pages)}</span></td>' for i, cell in enumerate(row))
        body.append(f"<tr>{cells}</tr>")
    under = f'<caption class="d-src">{caption}</caption>' if caption else ""
    return f'<div class="d-wrap"><table class="d-table">{under}<thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def note_words(text, refs=None, pages=None, skip_tables=False, flag_lines=True):
    """A section of a note, word for word: paragraphs, lists and tables. Everything comes through note_inline, so nothing from a note reaches a browser raw.

    `flag_lines=False` is for a dated record whose block already names its file and day. The Journal's lines are that day's words, and an entry is never rewritten, so a tag asking for a source there could never be filled."""
    parts, table = [], []

    def flush():
        if table:
            cells = [[c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))] for line in table]
            rows = [r for r in cells[1:] if not all(set(c) <= set("-: ") for c in r)]
            if not skip_tables:
                parts.append(note_table(cells[0], rows, refs, pages, flag_lines=flag_lines))
            table.clear()

    for line in text.splitlines():
        if line.startswith("|"):
            table.append(line)
            continue
        flush()
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            parts.append(f'<p class="d-note d-block"><b><span class="d-copied">{note_inline(line.lstrip("# "), refs, pages)}</span></b></p>')
        else:
            mark = "• " if line.startswith(("- ", "* ")) else ""
            words = line[2:] if mark else line.strip("*") if re.fullmatch(r"\*[^*].*[^*]\*", line) else line
            parts.append(f'<p class="d-note d-block">{mark}<span class="d-copied">{note_inline(words, refs, pages)}</span>{_flag(words) if flag_lines else ""}</p>')
    flush()
    return "".join(parts)


def _copied(value, none=""):
    """Words from a file are marked, so a test can check that they really are in that file. The page's own stand-in for a blank is not."""
    return f'<span class="d-copied">{e(str(value))}</span>' if value else e(none)


def _note_src(model):
    note = model["note"]
    when = f'last checked {data.nice_date(note["last_checked"])}' if data._real_day(note["last_checked"]) else "no last-checked date in the note"
    return f'{note["file"]}, {when}'


def company_pages(rows):
    return {r["name"]: r for r in rows}


def company_top(model):
    note = model["note"]
    bits = [("Ticker", note["ticker"], "None in the note"), ("Status in the note", note["status"], "Not stated. A status line in the note would fill it"), ("Sector", note["sector"], "Not stated. A sector line in the note would fill it")]
    cells = "".join(f'<span><span class="d-muted">{e(a)}:</span> <b>{_copied(b, none)}</b></span>' for a, b, none in bits)
    return (f'<p class="c-coach">{e(COACH_LINE)}</p><div class="c-top"><b class="c-name d-text">{e(note["name"])}</b>{cells}</div>'
            f'<p class="d-muted d-text">{e(_note_src(model))}. Read-only. This page reads files on this computer, fetches nothing and sends nothing.</p>'
            + (age_tag("company_note", note["last_checked"], model["today"]) if data._real_day(note["last_checked"]) else ""))


def on_file_table(model, now):
    """What is on file, counted from the files as read now, so every count has that date."""
    h, links = model["history"], model["links"]
    read = data.nice_date(now.date())
    rows = [("The note's sections", model["section_count"], _note_src(model)),
            ("Graph neighbors", len(links["rows"]) + len(links["only_there"]), "Typed links tables in Companies/"),
            ("Catalyst notes", len(model["catalysts"]), "Catalysts/"), ("8-K notes", len(model["filings"]), "Inbox/"),
            ("Research files", len(model["research"]), "Research/"), ("Decision files", len(h["decisions"]), "Journal/decisions/"),
            ("Journal and Lessons files naming it", len(h["mentions"]), "Journal/ and Lessons/")]
    body = [f'<tr><td>{e(a)}</td><td class="d-num">{n}</td><td class="d-muted d-src">calc., counted in {e(b)}, read {e(read)}</td></tr>' for a, n, b in rows]
    found = model.get("periodic")
    if found:
        small = f'{link(found["url"], found["form"] + ", filed " + data.nice_date(found["filed"]))}, on the SEC filing list saved {e(data.nice_date(found["retrieved"].date()))}{age_tag("periodic_filing", found["filed"], model["today"])}'
        body.append(f'<tr><td>Latest 10-Q or 10-K</td><td class="d-num">{e(data.nice_date(found["filed"]))}</td><td class="d-muted d-src">{small}</td></tr>')
    return _table(["On file", "Count", "Source and date"], body, numeric=(1,))


def missing_table(model):
    if not model["missing"]:
        return '<p class="d-text">Nothing on this list is missing.</p>'
    body = [f'<tr><td class="d-text">{e(a)}</td><td class="d-text">{e(b)}</td></tr>' for a, b in model["missing"]]
    return f'<div class="c-missing">{_table(["Missing", "What the page knows, and what would fill it"], body)}</div>'


def thesis_block(model, pages):
    """The thesis's status. The draft label is fixed, and it heads whatever draft or kill line is on file."""
    t, section = model["thesis"], model["thesis_section"]
    parts = []
    if section is None:
        parts.append('<p class="d-text">The note has no Thesis section.</p>')
    else:
        parts.append(f'<p class="d-chart-title">The note\'s Thesis section, word for word</p>{note_words(section, model["refs"], pages)}<small class="d-src">{e(_note_src(model))}</small>')
    if t["drafts"] or t["kill_file"]:  # under the note's own section, so a thesis I record there never sits under the label
        parts.append(f'<div class="c-draft">{e(DRAFT_LABEL)}</div>')
    if t["drafts"]:
        rows = [f'<tr><td class="d-src">{e(d["file"])}, written {e(data.nice_date(d["written"]))}{age_tag("research_file", d["written"], model["today"])}</td><td>{_copied(d["status"], "Not stated")}</td>'
                f'<td>{_copied(d["skeptic"], "Not stated. A skeptic review line in the file would fill it")}</td><td><span class="d-copied">{note_inline(d["remark"], {}, pages)}</span></td></tr>' for d in t["drafts"]]
        parts.append('<p class="d-chart-title">Drafts on file, each with its own words on itself</p>' + _table(["File", "Status it gives itself", "Skeptic's review, in this file's header", "Its remark at the top"], rows))
    else:
        parts.append('<p class="d-text">No thesis draft on file. The thesis skill would write one in Research/, for a company that passed triage.</p>')
    return "".join(parts)


def kill_block(model, pages):
    """Claims, kill lines and the calendar, each as written on the file's date. The page re-reads nothing, so a status here is that date's."""
    t = model["thesis"]
    if not t["kill_file"]:
        return '<p class="d-text">No claims or kill lines on file. A kill criteria file in Research/ would fill them. They come with a thesis draft.</p>'
    refs, when = t["refs"], data.nice_date(t["written"])
    caption = e(f'{t["kill_file"]}, written {when}')
    parts = [f'<div class="c-draft">{e(DRAFT_LABEL)}</div>', age_tag("research_file", t["written"], model["today"]),
             f'<p class="d-muted d-text">As written in {e(t["kill_file"])} on {e(when)}. Status there: <span class="d-copied">{e(t["kill_status"])}</span>. This page re-reads no number, so "Today" and "Status" below are that date\'s.</p>',
             '<p class="d-chart-title">Claims</p>', note_table(t["claims"]["headers"], t["claims"]["rows"], refs, pages, caption), note_words("\n".join(t["claim_words"]), refs, pages),
             '<p class="d-chart-title">Kill lines</p>', note_table(t["lines"]["headers"], t["lines"]["rows"], refs, pages),
             '<p class="d-chart-title">Calendar of checks</p>', note_words("\n".join(t["calendar_words"]), refs, pages)]
    parts += [note_table(table["headers"], table["rows"], refs, pages, caption) for table in t["calendar"]]
    return "".join(parts)


def catalysts_table(model):
    rows = model["catalysts"]
    if not rows:
        return '<p class="d-text">No catalyst note has this ticker or links this company. A note in Catalysts/ that names it would fill this.</p>'
    body = []
    for c in rows:
        checked = f'{c["file"]}, checked {data.nice_date(c["last_checked"])}' if data._real_day(c["last_checked"]) else f'{c["file"]}, no checked date in the note'
        first = f"When section's first link: {link(c['source'][1], c['source'][0])}. " if c["source"] else "No link in the When section. "
        aged = age_tag("catalyst_note", c["last_checked"], model["today"]) if data._real_day(c["last_checked"]) else ""
        trouble = f'<div class="d-problem">{e(c["problem"])}</div>' if c["problem"] else ""
        body.append(f'<tr><td>{_copied(c["title"])}{trouble}</td><td>{_copied(c["type"])}</td><td>{_copied(c["quote"], "No date given")}</td><td>{_copied(c["kind"])}</td>'
                    f'<td>{_copied(c["in_numbers"])}</td><td>{"Yes" if c["outcome"] else "No"}</td><td>{e(c["why"])}</td><td class="d-muted d-src">{first}{e(checked)}{aged}</td></tr>')
    return ('<p class="d-muted">Dates, sizes and names here are plans, targets or forecasts as the notes give them, not results. Strategic value, so none of this counts toward coverage. Earliest start first, then those with no date. A first link may not source that date.</p>'
            + _table(["Catalyst", "Type", "Date, as the note words it", "Kind of date", "In reported numbers", "Outcome written", "Why it is listed", "Source and date"], body))


def links_table(model, pages):
    """Each neighbor and how it is linked, as the note wrote it, with the evidence word kept. A link means a link exists, not that an event reaches that company."""
    name, links = model["note"]["name"], model["links"]
    if not links["rows"] and not links["only_there"]:
        return '<p class="d-text">No Typed links row names this company.</p>'

    def row(r, how):
        flag = _flag(r["what"], r["size"], r["source"])
        other = company_link(pages[r["plain"]], r["other"].replace("[[", "").replace("]]", "")) if r["plain"] in pages else e(r["other"].replace("[[", "").replace("]]", ""))
        return (f'<tr><td>{other}</td><td>{e(how)}</td><td><span class="d-copied">{e(r["chain"])}</span></td><td>{flag}<span class="d-copied">{note_inline(r["what"], {}, pages)}</span></td>'
                f'<td><span class="d-copied">{note_inline(r["size"], {}, pages)}</span></td><td><span class="d-copied">{e(r["evidence"])}</span></td><td class="d-src"><span class="d-copied">{note_inline(r["source"], {}, pages)}</span></td></tr>')

    body = [row(r, f'{name} {r["link"]} {r["plain"]}') for r in links["rows"]]
    body += [row(r, f'{r["written_in"]} {r["link"]} {name}. Written only in {r["written_in"]}\'s note') for r in links["only_there"]]
    words = '<p class="d-muted">One step out, from the Typed links tables. A link means a link exists, not that an event reaches that company. Evidence is the note\'s own word: Stated, Read together, Conditional, Reported or My reading.</p>'
    return words + _table(["Neighbor", "How it is linked", "Chain", "What", "Size", "Evidence", "Source and date"], body) + "".join(problem(p) for p in links["problems"])


def other_links_words(model, pages):
    """The note's lists under its Typed links table: links of no type, and what could not be supported."""
    return note_words(model["other_links"], model["refs"], pages, skip_tables=True)


def history_table(model):
    h = model["history"]
    rows = [f'<tr><td class="d-nowrap">{e(data.nice_date(d["date"]))}</td><td>Decision file, stage <span class="d-copied">{e(d["stage"])}</span></td><td class="d-src">{e(d["file"])}, {e(data.nice_date(d["date"]))}</td></tr>' for d in h["decisions"]]
    for m in h["mentions"]:
        day = data.nice_date(m["date"]) if m["date"] else "Undated"
        rows.append(f'<tr><td class="d-nowrap">{e(day)}</td><td>{m["lines"]} line{"" if m["lines"] == 1 else "s"} name it (calc.)</td><td class="d-src">{e(m["file"])}, {e(day)}</td></tr>')
    if not rows:
        return '<p class="d-text">No decision file, and no Journal or Lessons file names it.</p>'
    return '<p class="d-muted">A name match, not a reading. Open the file to read it. A decision file\'s system view is not shown here.</p>' + _table(["Date", "What", "File"], rows)


# ---- Ideas ----

LEAD_LABEL = "A lead to read, never a pick"
MY_WORDS_LABEL = "My own words, not a pick"
# Each stage: its name, what puts a company there, and what would fill it. Claude's reading of the files, for me to correct.
STAGE_WORDS = {
    "lead": ("Lead on the screen", "A row on the radar's market screen. Nobody has read why the line went up, and a rise can be a deal, a deposit, an acquisition, a reclassification, a season or a data slip.", "A radar run with a screen."),
    "map": ("On the map", "A note in Companies/, because it links to a company we follow. It has no gate result yet, and the hunt skips names on the map.", "A note in Companies/."),
    "tested": ("Tested by the hunt", "The monthly hunt tested it and proposes a line for the rejection log. It stays here until I add the line myself, or do not.", "A report from the monthly hunt, Research/ with Monthly hunt in its name."),
    "idea": ("Idea note", "The hunt wrote a note to Inbox/. It cleared the screen and two quick gates. It has no thesis, no skeptic's review and no Gate 3.", "A note in Inbox/ with idea in its name."),
    "watchlist": ("Watchlist", "It reached Gate 3 and did not pass. We look again on filing dates, not on a price.", "A triage row sorted Watchlist, or a ticker in the hunt's settings."),
    "research": ("Research", "It passed all three gates, and it has no thesis draft yet.", "A triage row sorted Research."),
    "thesis": ("Thesis draft", "A draft is in Research/. A draft is not a recorded thesis.", "A file in Research/ with thesis draft in its name."),
    "skeptic": ("Skeptic's review", "I have ruled on the skeptic's review, and no coach file follows it yet.", 'A line of mine under "What we decided" in the Journal.'),
    "decision": ("Decision", "A coach file in Journal/decisions/. Only my view and my own decision show here. The system's view does not.", "A coach file in Journal/decisions/."),
    "rejected": ("Rejected", "In the rejection log, with nothing newer on file. No research hours for now. It is not a view that a stock will fall.", "A row in the rejection log."),
}
STAGE_ORDER = (*data.STAGES, data.OFF_RAMP)


def _lead_label(words=LEAD_LABEL):
    return f'<small class="i-lead">{e(words)}</small>'


def _stage_count(ideas, stage):
    return len(ideas["stages"][stage])


def jump_line(waiting, read_on):
    """Where things are on this long screen. The count is what still waits on me, from the same reading as Home."""
    count = "" if waiting is None else f', {_plural(waiting, "line")} waiting'
    links = (("ideas", "Ideas"), ("rejection-log", "Rejection log"), ("alerts", f"Alerts{count}"), ("routines", "Routines"), ("guardrails", "Guardrails"), ("hunt", "The hunt's reports"), ("radar", "Catalyst radar"), ("filings", "Latest 8-Ks"), ("sources", "Source ages"))
    return sourced(f'<div class="i-jump">{"".join(f"""<a href="#{slug}">{e(words)}</a>""" for slug, words in links)}</div>', src("Journal/, calc.", read_on))


def lead_counts(ideas):
    here = sum(len(lead["lines"]) for part in ideas["steps"] for lead in part["leads"] + part["hidden"])
    return (f'<p class="d-text">{ideas["screen_rows"]} rows on the screen, the hidden ones included. {here} are here. The other {ideas["rows_elsewhere"]} belong to companies at another stage, and each of those shows this under "Also on file" (calc.).</p>'
            f'<p class="d-muted"><span class="d-copied">{e(ideas["radar"]["leads_line"])}</span></p>')


def step_counts(part):
    """A step's table leaves out companies that sit at another stage, so its own count is said."""
    here = sum(len(lead["lines"]) for lead in part["leads"])
    hidden = sum(len(lead["lines"]) for lead in part["hidden"])
    total = sum(len(lead["lines"]) for lead in part["step"]["leads"])
    return f'<p class="d-muted">{here} of its {total} rows are in this table. The rest sit at another stage. {hidden} rows are in the fold under it (calc.).</p>'


def rejection_counts(ideas):
    log = ideas["log"]["rows"]
    later = [r for r in log if r["stage"] != data.OFF_RAMP]
    tail = "".join(f' <span class="d-copied">{e(r["company"])}</span> is in the log and sits at {e(STAGE_WORDS[r["stage"]][0])}, because something newer or further is on file.' for r in later)
    return f'<p class="d-text">{len(log)} rows in the log (calc.).{tail}</p>'


def stage_strip(ideas, read_on):
    """The pipeline at a glance, from the first lead to a decision, with the way off it apart. Every stage looks the same, whatever is in it."""
    tile = lambda stage: f'<a class="i-tile{" i-off" if stage == data.OFF_RAMP else ""}" href="#{"rejection-log" if stage == data.OFF_RAMP else "stage-" + stage}"><b>{_stage_count(ideas, stage)}</b><span>{e(STAGE_WORDS[stage][0])}</span></a>'  # noqa: E731
    tiles = ['<i class="i-arrow">→</i>'.join(tile(stage) for stage in data.STAGES), tile(data.OFF_RAMP)]
    total = sum(_stage_count(ideas, stage) for stage in STAGE_ORDER)
    return sourced(f'<div class="i-flow">{"".join(tiles)}</div>', src(f"calc., {total} companies and leads, each at one stage, counted from the tables below, files read {read_on}", read_on))


def _evidence_line(ev, pages, today):
    words = "<br>".join(f'<span class="d-copied">{note_inline(w, ev["refs"], pages)}</span>' for w in ev["words"])
    source = ev["source"] or "No file named"
    date = data.nice_date(ev["day"]) if ev["day"] else f"undated, retrieved {today}"
    return f'{e(ev["says"])} {words}{src(source, date)}'


def stage_table(rows, stage, pages, today):
    """One row for each company at this stage: who, why it is here, its source and date, and what else is on file. Words copied from a file are marked."""
    body = []
    for item in rows:
        label = LEAD_LABEL
        if stage == "decision":
            label = f'{MY_WORDS_LABEL}. Paper, a lesson' if item["at"]["paper"] else MY_WORDS_LABEL
        note = pages.get(item["note"]["name"]) if item["note"] else None
        name = company_link(note, item["name"]) if note else f'<span class="d-copied">{e(item["name"])}</span>'
        ticker = f' ({e(item["ticker"])})' if item["ticker"] else ""
        also = ""
        if item["also"]:
            also = '<div class="i-also"><b>Also on file:</b>' + "".join(f'<p>{_evidence_line(ev, pages, today)}</p>' for ev in item["also"]) + "</div>"
        body.append(f'<tr><td>{name}{ticker}{_lead_label(label)}</td><td>{_evidence_line(item["at"], pages, today)}{also}</td></tr>')
    return _table(("Company", "Why it is here, with its source and date"), body)


def rejection_table(rows, caption, sits_at=True):
    """The log's rows as written, nearest month to look again first. The month is read from the look-again words, and it raises nothing."""
    if not rows:
        return '<p class="d-muted">None on file. A row in Research/Rejection log.md would fill it.</p>'
    body = []
    for row in rows:
        sits = f'<td>{e(STAGE_WORDS[row["stage"]][0])}</td>' if sits_at else ""
        body.append(f'<tr><td><span class="d-copied">{e(row["company"])}</span>{_lead_label()}</td><td class="d-nowrap"><span class="d-copied">{e(row["gate"])}</span></td>'
                    f'<td><span class="d-copied">{note_inline(row["reason"])}</span></td><td class="d-nowrap"><span class="d-copied">{e(row["date_words"])}</span></td>'
                    f'<td><span class="d-copied">{note_inline(row["look"])}</span></td><td class="d-nowrap">{e(row["month_shown"])}</td>{sits}</tr>')
    headers = ["Company", "Gate", "Why it was rejected", "Rejected on", "When to look again", "Month or year it names (calc.)"] + (["Sits at"] if sits_at else [])
    return _table(headers, body, caption=caption)


def hunt_block(report):
    """One report of the monthly hunt, as it was written."""
    day = data.nice_date(report["day"])
    caption = src_markup(e(f'{report["file"]}, {day}'))
    out = []
    if report["remark"]:
        out.append(f'<p class="d-muted"><span class="d-copied">{note_inline(report["remark"])}</span></p>')
    if report["funnel"]:
        out.append('<p class="d-chart-title">The funnel</p>' + note_table(report["funnel"]["headers"], report["funnel"]["rows"], caption=caption))
    if report["tested"]:
        out.append('<p class="d-chart-title">The tested companies</p>' + note_table(report["tested"]["headers"], report["tested"]["rows"], caption=caption))
    if report["sources"]:
        out.append(f'<p class="d-note d-block"><span class="d-copied">{note_inline(report["sources"])}</span>{src(report["file"], day)}</p>')
    return "".join(out)


def company_list_table(rows, runs):
    """Every note in Companies/, with a click to its page."""
    body = []
    for r in rows:
        if r["problem"]:
            body.append(f'<tr><td>{e(r["name"])}</td><td colspan="4">{problem(r["problem"])}</td></tr>')
            continue
        checked = data.nice_date(r["last_checked"]) if data._real_day(r["last_checked"]) else "no date"
        body.append(f'<tr><td>{company_link(r)}</td><td>{_copied(r["ticker"], "None")}</td><td>{_copied(r["status"], "Not stated. A status line in the note would fill it")}</td><td>{"Yes" if r["name"] in runs else "Not on file. A value run would fill it"}</td><td class="d-muted d-src">{e(r["file"])}, last checked {e(checked)}</td></tr>')
    return _table(["Company", "Ticker", "Status in the note", "Saved value run", "Source and date"], body)


# ---- Journal ----

JOURNAL_PARTS = ("By day", "What we decided", "What we left open", "Decisions", "Lessons", "Search")
JOURNAL_RECORD = "Word for word from the files. A figure in these lines is what the file said on its date. Nothing here is checked again, and none of it is a view on today."
LEFT_OPEN_LINE = 'The Journal has no closed mark, so every item stays listed by its date, even after a later entry closed it. Some carry the word "Closed" in their own text. Newest first.'
SEARCH_ROWS = 200


def journal_day_href(day):
    return f"/journal?day={day}" if data._real_day(day) else "/journal"


def _journal_day_link(day):
    return f'<a href="{e(journal_day_href(day), quote=True)}" target="_self">{e(data.nice_date(day))}</a>'


def _fold(title, small, inner, is_open=False):
    """A folded block as plain markup. Opening it asks nothing of the server, and its source shows while it is shut. Words inside it come from note_words, so nothing reaches a browser raw."""
    return f'<details class="j-fold d-fig"{" open" if is_open else ""}><summary>{title}{small}</summary>{inner}</details>'


def journal_day_blocks(day, pages=None):
    """One day: its top lines, then each session folded under its own heading, newest first."""
    when = data.nice_date(day["day"])
    small = src(day["file"], when)
    out = []
    for session in reversed(day["sessions"]):
        out.append(_fold(f'<span class="d-copied">{note_inline(session["heading"], day["refs"], pages)}</span>', small, note_words(session["text"], day["refs"], pages, flag_lines=False)))
    if day["top"]:
        out.append(_fold(e(data.TOP_OF_FILE), small, note_words(day["top"], day["refs"], pages, flag_lines=False), is_open=True))
    return "".join(out)


def _item_words(text, refs, pages):
    lines = text.split("\n")
    subs = "".join(f'<p class="j-sub">• <span class="d-copied">{note_inline(line.removeprefix("- ").removeprefix("* "), refs, pages)}</span></p>' for line in lines[1:])
    return f'<span class="d-copied">{note_inline(lines[0], refs, pages)}</span>{subs}'


def journal_items_table(items, pages=None):
    """Lines from many sessions, each with its day, session and file."""
    body = [f'<tr><td class="d-nowrap">{_journal_day_link(i["day"])}</td><td>{e(i["session"]) if i["session"] == data.TOP_OF_FILE else f"""<span class="d-copied">{note_inline(i["session"], i["refs"], pages)}</span>"""}</td><td>{_item_words(i["text"], i["refs"], pages)}</td>'
            f'<td class="d-src">{e(i["file"])}, {e(data.nice_date(i["day"]))}</td></tr>' for i in items]
    return _table(["Day", "Session", "Words", "File"], body)


def quiet_words(count):
    return f' Another {count} {"says" if count == 1 else "say"} only "nothing" and {"is" if count == 1 else "are"} left out here.' if count else ""


def journal_count(words, read_on):
    return sourced(f'<p class="d-muted">{e(words)}</p>', src("calc., counted from Journal/", read_on))


def decisions_table(files, pages=None):
    """Each coach file: my view and what I then decided. A decision file's system view is not shown here, and data.decision_files never reads it out."""
    body = []
    for f in files:
        name = company_link(pages[f["name"]], f["name"]) if pages and f["name"] in pages else _copied(f["name"])
        if data.is_paper_name(f["name"]):  # real and paper never mix
            name += '<div class="d-muted">Paper, made-up money</div>'
        day = data.nice_date(f["day"])
        said = "".join(f'<p class="d-note d-block"><span class="d-copied">{note_inline(line)}</span></p>' for line in f["view"]) or "My view is not in this file. A My view section in it would fill it."
        decided = f'<span class="d-copied">{note_inline(f["decided"])}</span>' if f["decided"] else 'Not said yet. My own words under "What I then decided" in the file would fill it.'
        body.append(f'<tr><td class="d-nowrap">{e(day)}</td><td>{name}</td><td>{_copied(f["stage"], "Not stated")}</td><td>{said}</td><td>{decided}</td><td class="d-src">{e(f["file"])}, {e(day)}</td></tr>')
    return _table(["Date", "Company", "Stage", "My view", "What I then decided", "File"], body)


def lesson_blocks(lessons, today, pages=None):
    """Each lesson under its title and date, folded, with its file. A browser cannot open a local file from this page, so its words are here too."""
    out = []
    for r in lessons:
        when = data.nice_date(r["day"]) if r["day"] else f"undated, retrieved {data.nice_date(today)}"
        out.append(_fold(f'<span class="d-copied">{note_inline(r["title"], r["refs"], pages)}</span>', src(r["file"], when), note_words(r["text"], r["refs"], pages, flag_lines=False)))
    return "".join(out)


def search_table(rows, today, pages=None, limit=SEARCH_ROWS):
    """Each line that holds the words, with where it sits. A Journal line links to its day. The count above it says how many are not shown."""
    body = []
    for r in rows[:limit]:
        day = data.nice_date(r["day"]) if r["day"] else f"undated, retrieved {data.nice_date(today)}"
        first = _journal_day_link(r["day"]) if r["file"].startswith("Journal/") else e(day)
        body.append(f'<tr><td class="d-nowrap">{first}</td><td><span class="d-copied">{note_inline(r["where"], r["refs"], pages)}</span></td><td><span class="d-copied">{note_inline(r["text"], r["refs"], pages)}</span></td>'
                    f'<td class="d-src">{e(r["file"])}, line {r["line"]}, {e(day)}</td></tr>')
    return _table(["Day", "Under", "Line", "File"], body)
