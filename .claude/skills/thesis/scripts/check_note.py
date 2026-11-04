#!/usr/bin/env python3
"""Check a thesis note before it goes to the owner. Reads one file, writes nothing, uses no network.

It looks for what a person misses when tired: a figure with no label, a link with no date,
a missing section, a kill line with no threshold or date, a claim of approval, advice words.
It cannot tell whether a source is right. Exit 0 means no findings, 1 findings, 2 bad usage.
"""
import argparse
import re
import sys
from pathlib import Path

SECTIONS = [
    "Six questions",
    "What the market believes, against what the evidence shows",
    "Cash and funding evidence",
    "Kill criteria",
    "Monitoring plan",
    "What I cut",
    "How far to trust this",
    "Against the earlier draft",
]
QUESTIONS = [
    "The mechanism",
    "The value in dollars",
    "The probability",
    "The timing",
    "What today's price already implies",
    "What would prove it wrong",
]
MARKET_COLUMNS = ["claim", "status", "market", "evidence", "not know"]
CASH_COLUMNS = ["reading", "period", "figure", "source"]
STATUS_WORDS = ("supports", "mixed", "against", "unknown")
# Words that claim more than a note can show when most claims are not supported.
STRONG = re.compile(r"\b(?:real|solid|strong|sound|robust|compelling|confirmed|clearly|intact|on track)\b", re.I)
KILL_COLUMNS = ["line", "claim", "measure", "threshold", "test date", "today", "status", "set by", "source"]

# A money amount, a percent, a multiple, or a number with a business unit.
FIGURE = re.compile(
    r"(?<![\w/.-])(?:[−-]?[$€¥£]\s?\d[\d,]*(?:\.\d+)?(?:\s?(?:billion|million|trillion|[BMK]\b))?"
    r"|[−-]?\d[\d,]*(?:\.\d+)?\s?%"
    r"|\d[\d,]*(?:\.\d+)?\s?[x×](?![\w])"
    r"|\d[\d,]*(?:\.\d+)?\s?(?:billion|million|trillion)\b"
    r"|\d[\d,]*(?:\.\d+)?M\b(?:\s+\w*-?km|\s+diluted)?)"
)
DATE = re.compile(
    r"\b(?:Jan|Feb|Mar|Apr|May|June?|July?|Aug|Sept?|Oct|Nov|Dec)[a-z]*\.?\s+(?:\d{1,2},\s+)?\d{4}\b"
    r"|\b\d{4}-\d{2}-\d{2}\b|\bundated, retrieved\b"
)
LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
# Backticked vault file, with a date in the same text, counts as a source.
VAULT_REF = re.compile(r"`[^`]+\.(?:html|md|json|py|csv)`")
CALC = re.compile(r"\bcalc\b", re.I)
# Inputs given in the label itself: "(calc., $21.73 ÷ $123.20)" or "(calc., $5,081M to $6,750M)".
CALC_INPUTS = re.compile(r"\bcalc\.?,?[^)]*\d|[÷×=+]|\d\s[−-]\s\d", re.I)
POINTER = re.compile(r"\bsame (?:source|page|filing|run|filings|sources)\b|\b(?:above source|see above|above)\b", re.I)
# These cover only a figure close by, so one word cannot pass a whole sentence.
NEAR_LABEL = re.compile(r"\bmy (?:estimate|estimates|count|reading|calc|search|sum|date estimate)\b|\bassum(?:ed|es|ption|ptions)\b|\bRules/", re.I)
NEAR = 45
APPROVAL = [
    re.compile(p, re.I)
    for p in (
        r"\bthesis\s+(?:is|was|has been|now)?\s*approved\b",
        r"\bapproved\s+thesis\b",
        r"\bstatus:\s*approved\b",
        r"\bmark(?:ed|ing)?\s+(?:the\s+)?thesis\s+(?:as\s+)?approved\b",
        r"\b(?:survived|passed)\s+(?:the\s+|a\s+)?skeptic",
    )
]
NEGATED = re.compile(
    r"\b(?:not|never|no|nor|isn't|until|unless|whether|without|has not|have not|does not|did not|cannot)\b", re.I
)
ADVICE = [
    re.compile(p, re.I)
    for p in (
        r"(?<!no )(?<!not a )\bbuy recommendation\b",
        r"\b(?:we|you|i)\s+should\s+(?:buy|sell|trim|hold|add)\b",
        r"\b(?:recommend|suggest|advise)\s+(?:buying|selling|trimming|adding|holding)\b",
        r"\bstrong buy\b",
        r"\b(?:is|looks)\s+(?:overpriced|overvalued|undervalued|cheap)\b",
        r"\bwill fall\b",
        r"\bgood entry\b",
        r"\bprice target of\b",
        r"\bwait (?:for|until) (?:the price|a pullback|a dip)\b",
    )
]


def strip_frontmatter(lines):
    """Return (frontmatter lines, index of first body line)."""
    if lines and lines[0].strip() == "---":
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "---":
                return lines[1:i], i + 1
    return [], 0


def split_row(line):
    """Split a markdown table row, keeping pipes inside link URLs out of it."""
    return [c.strip() for c in line.strip().strip("|").split("|")]


def is_rule(line):
    return bool(re.fullmatch(r"\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*", line.strip()))


def tables(lines, start):
    """Yield (line number, header cells, rows) with each row as (line number, cells)."""
    i = start
    while i < len(lines):
        if lines[i].lstrip().startswith("|") and i + 1 < len(lines) and is_rule(lines[i + 1]):
            head = split_row(lines[i])
            rows = []
            j = i + 2
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                rows.append((j + 1, split_row(lines[j])))
                j += 1
            yield i + 1, head, rows
            i = j
        else:
            i += 1


def has_source(text):
    """True if this text holds a dated link or a dated vault reference."""
    if any(DATE.search(label) for label, _url in LINK.findall(text)):
        return True
    return bool(VAULT_REF.search(text) and DATE.search(LINK.sub("", text)))


def clean(text):
    """Text without link URLs or code spans, so their digits are not read as figures."""
    return re.sub(r"`[^`]*`", "", re.sub(r"\]\([^)]*\)", "]", text))


def figures_in(text):
    return FIGURE.findall(clean(text))


def calc_covers(text, context):
    """A calc. label counts only with its inputs: a source here, numbers named, or a pointer to a source."""
    if not CALC.search(text):
        return False
    if has_source(text) or CALC_INPUTS.search(clean(text)):
        return True
    return bool(POINTER.search(text) and has_source(context))


def uncovered(text, context=None):
    """Figures in the text that nothing labels. Context is the line or table row around it."""
    context = text if context is None else context
    if has_source(text) or calc_covers(text, context):
        return []
    if POINTER.search(text) and has_source(context):
        return []
    plain = clean(text)
    return [
        m.group(0)
        for m in FIGURE.finditer(plain)
        if not NEAR_LABEL.search(plain[max(0, m.start() - NEAR) : m.end() + NEAR])
    ]


def sentences(text):
    """Split prose into sentences, keeping 'Oct. 29, 2026' and '$1.5' whole."""
    protected = re.sub(r"\[[^\]]*\]\([^)]*\)", lambda m: m.group(0).replace(". ", ". "), text)
    protected = re.sub(
        r"\b(Jan|Feb|Mar|Apr|Aug|Sept?|Oct|Nov|Dec|No|vs|approx|Inc|Corp|Co)\.\s", lambda m: m.group(0).replace(" ", " "), protected
    )
    parts = re.split(r"(?<=[.!?:])\s+(?=[A-Z\[*`\"$])", protected)
    return [p.replace(" ", " ") for p in parts if p.strip()]


def check_figures(lines, start, allowed):
    findings = []
    table_lines = set()
    for head_no, _head, rows in tables(lines, start):
        table_lines.update([head_no, head_no + 1])
        table_lines.update(no for no, _ in rows)
    # A short line right under a table can cover the whole table.
    for head_no, head, rows in tables(lines, start):
        end = rows[-1][0] if rows else head_no + 1
        below = " ".join(lines[end : end + 3])
        covered = bool(CALC.search(below)) and has_source(below)
        head_lower = [h.lower() for h in head]
        for no, cells in rows:
            row_text = " | ".join(cells)
            row_source = any(has_source(c) for h, c in zip(head_lower, cells) if "source" in h)
            for h, cell in zip(head_lower, cells):
                if row_source or covered or not uncovered(cell, row_text):
                    continue
                if any(a in cell for a in allowed):
                    continue
                findings.append(f"line {no}: figure with no source or label in column '{h}': {cell[:90]}")
    in_code = False
    for idx in range(start, len(lines)):
        line = lines[idx]
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code or idx + 1 in table_lines or line.lstrip().startswith("#"):
            continue
        for sentence in sentences(line):
            figs = uncovered(sentence, line)
            if figs and not any(a in sentence for a in allowed):
                findings.append(f"line {idx + 1}: figure with no source or label ({', '.join(figs[:3])}): {sentence.strip()[:90]}")
    return findings


def check_links(lines, start):
    findings = []
    for idx in range(start, len(lines)):
        for label, url in LINK.findall(lines[idx]):
            if url.startswith("http") and not DATE.search(label):
                findings.append(f"line {idx + 1}: link with no date in its text: [{label[:70]}]")
    return findings


def check_structure(lines, start):
    findings = []
    heads = {l.lstrip("# ").strip().rstrip(".") for l in lines[start:] if l.startswith("#")}
    for section in SECTIONS:
        if section not in heads:
            findings.append(f"missing section: {section}")
    for n, question in enumerate(QUESTIONS, 1):
        if not any(h.rstrip(".") == f"{n}. {question}" for h in heads):
            findings.append(f"missing question {n}: {question}")
    return findings


def section_range(lines, start, name):
    begin = None
    for idx in range(start, len(lines)):
        if lines[idx].startswith("## "):
            if begin is not None:
                return begin, idx
            if lines[idx][3:].strip() == name:
                begin = idx + 1
    return (begin, len(lines)) if begin is not None else (None, None)


def check_tables(lines, start):
    findings = []
    begin, end = section_range(lines, start, "What the market believes, against what the evidence shows")
    if begin is not None:
        found = [t for t in tables(lines[:end], begin)]
        if not found:
            findings.append("market section has no table")
        else:
            _no, head, rows = found[0]
            low = " | ".join(head).lower()
            for column in MARKET_COLUMNS:
                if column not in low:
                    findings.append(f"market table lacks a column with '{column}'")
            for no, cells in rows:
                if any(not c.strip() for c in cells):
                    findings.append(f"line {no}: market table has an empty cell")
    begin, end = section_range(lines, start, "Cash and funding evidence")
    if begin is not None:
        found = [t for t in tables(lines[:end], begin)]
        if not found:
            findings.append("cash and funding section has no table")
        else:
            _no, head, rows = found[0]
            low = " | ".join(head).lower()
            for column in CASH_COLUMNS:
                if column not in low:
                    findings.append(f"cash table lacks a column with '{column}'")
            if len(rows) < 2:
                findings.append("cash table needs at least two readings")
    begin, end = section_range(lines, start, "Kill criteria")
    if begin is not None:
        found = [t for t in tables(lines[:end], begin)]
        if not found:
            findings.append("kill criteria section has no table")
        else:
            _no, head, rows = found[0]
            low = [h.lower() for h in head]
            for column in KILL_COLUMNS:
                if not any(column in h for h in low):
                    findings.append(f"kill table lacks a column with '{column}'")
            if not rows:
                findings.append("kill table has no lines")
            for no, cells in rows:
                row = dict(zip(low, cells))
                threshold = next((v for k, v in row.items() if "threshold" in k), "")
                date = next((v for k, v in row.items() if "test date" in k), "")
                set_by = next((v for k, v in row.items() if "set by" in k), "")
                if not re.search(r"\d|\bevent\b|\bone\b|\byes\b|\bany\b|\bnames?\b", threshold, re.I):
                    findings.append(f"line {no}: kill line has no number or event in its threshold: {threshold[:70]}")
                if not re.search(r"\b(?:19|20)\d{2}\b", date) and not re.search(r"each (?:10|quarter|results|call)|any time", date, re.I):
                    findings.append(f"line {no}: kill line has no date: {date[:70]}")
                if not re.search(r"owner|proposed", set_by, re.I):
                    findings.append(f"line {no}: kill line does not say who set it: {set_by[:70]}")
    return findings


def market_rows(lines, start):
    """Rows of the market table as (line number, claim cell, status cell)."""
    begin, end = section_range(lines, start, "What the market believes, against what the evidence shows")
    if begin is None:
        return []
    found = [t for t in tables(lines[:end], begin)]
    if not found:
        return []
    _no, head, rows = found[0]
    low = [h.lower() for h in head]
    if "status" not in low or "claim" not in low:
        return []
    return [(no, cells[low.index("claim")], cells[low.index("status")]) for no, cells in rows]


def check_claims(lines, start):
    """Status words, the count under the headline, and the headline against that count."""
    findings = []
    rows = market_rows(lines, start)
    counts = dict.fromkeys(STATUS_WORDS, 0)
    for no, _claim, status in rows:
        word = status.replace("*", "").strip().split(",")[0].strip().lower()
        if word in counts:
            counts[word] += 1
        else:
            findings.append(f"line {no}: status must start with {', '.join(STATUS_WORDS)}: {status[:60]}")
    first_section = next((i for i in range(start, len(lines)) if lines[i].startswith("## ")), len(lines))
    intro = lines[start:first_section]
    count_line = next((l for l in intro if l.lower().startswith("**claim count")), None)
    if count_line is None:
        findings.append("no claim count under the headline")
    elif rows:
        total = re.search(r"(\d+) claims?", count_line)
        if not total or int(total.group(1)) != len(rows):
            findings.append(f"claim count says {total.group(1) if total else '?'}, the table has {len(rows)}")
        for word, n in counts.items():
            said = re.search(rf"(\d+) {word}", count_line)
            if not said or int(said.group(1)) != n:
                findings.append(f"claim count for {word} differs from the table, which has {n}")
    headline = next((l for l in intro if l.startswith("**") and not l.lower().startswith("**claim count")), "")
    if rows and counts["supports"] * 2 <= len(rows):
        strong = STRONG.search(headline)
        if strong:
            findings.append(
                f"headline says '{strong.group(0)}', but only {counts['supports']} of {len(rows)} claims support it"
            )
    if not re.search(r"\bcover(?:s|age)\b", " ".join(intro), re.I):
        findings.append("coverage is not stated above the first section")
    return findings


def check_kill_note(lines, start, kill_text):
    """Claim words and set lines must match the kill criteria note exactly."""
    findings = []
    kill_lines = kill_text.splitlines()
    claims, set_lines = {}, {}
    for _no, head, rows in tables(kill_lines, 0):
        low = [h.lower() for h in head]
        if low[:2] == ["claim", "words"]:
            claims = {c[0].strip(): c[1].strip() for _n, c in rows}
        if "threshold" in low and "number or event" in low:
            for _n, cells in rows:
                name = cells[0].replace("*", "").strip()
                set_lines[name] = (cells[low.index("number or event")], cells[low.index("threshold")])
    for no, claim, _status in market_rows(lines, start):
        plain = claim.replace("*", "").strip()
        match = re.match(r"(C\d+)\.?\s*(.*)", plain)
        if not match:
            findings.append(f"line {no}: claim has no number: {plain[:60]}")
            continue
        number, words = match.groups()
        if number in claims and not words.startswith(claims[number].rstrip(".")):
            findings.append(f"line {no}: {number} differs from the kill note, which says: {claims[number]}")
    begin, end = section_range(lines, start, "Kill criteria")
    found = [t for t in tables(lines[:end], begin)] if begin is not None else []
    if found:
        _no, head, rows = found[0]
        low = [h.lower() for h in head]
        got = {}
        if "measure" in low and "threshold" in low:
            got = {c[0].replace("*", "").strip(): (c[low.index("measure")], c[low.index("threshold")]) for _n, c in rows}
        for name, wanted in set_lines.items():
            if got.get(name) != wanted:
                findings.append(f"{name} is not copied exactly from the kill note")
    return findings


def check_status(front, lines, start):
    findings = []
    status = next((l.split(":", 1)[1].strip().strip('"') for l in front if l.startswith("status:")), None)
    if status is None:
        findings.append("frontmatter has no status")
    elif "draft" not in status.lower() or "not approved" not in status.lower():
        findings.append(f"status must say draft, not approved: {status}")
    if not any(l.startswith("triage:") and l.split(":", 1)[1].strip() for l in front):
        findings.append("frontmatter has no triage status")
    skeptic = next((l.split(":", 1)[1].strip() for l in front if l.startswith("skeptic review:")), None)
    if skeptic is None:
        findings.append("frontmatter has no skeptic review line")
    elif skeptic.lower() != "not run":
        findings.append(f"skeptic review must say not run: {skeptic}")
    for idx in range(start, len(lines)):
        for sentence in sentences(lines[idx]):
            for pattern in APPROVAL:
                match = pattern.search(sentence)
                if match and not NEGATED.search(sentence[: match.start()]):
                    findings.append(f"line {idx + 1}: reads as a claim of approval: {sentence.strip()[:90]}")
            for pattern in ADVICE:
                match = pattern.search(sentence)
                if match and not NEGATED.search(sentence[: match.start()]):
                    findings.append(f"line {idx + 1}: reads as advice: {sentence.strip()[:90]}")
    text = "\n".join(lines[start:]).lower()
    if "coverage" not in text:
        findings.append("the note never states coverage")
    return findings


def check(text, allowed=(), kill_text=None):
    lines = text.splitlines()
    front, start = strip_frontmatter(lines)
    return (
        check_status(front, lines, start)
        + check_structure(lines, start)
        + check_tables(lines, start)
        + check_claims(lines, start)
        + (check_kill_note(lines, start, kill_text) if kill_text else [])
        + check_links(lines, start)
        + check_figures(lines, start, allowed)
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("note", type=Path)
    parser.add_argument("--allow", action="append", default=[], help="text that marks a figure line as fine; say why to the owner")
    parser.add_argument("--kill-note", type=Path, help="kill criteria note whose claims and set lines must match exactly")
    args = parser.parse_args()
    if not args.note.is_file():
        print(f"no such file: {args.note}", file=sys.stderr)
        return 2
    kill_text = None
    if args.kill_note:
        if not args.kill_note.is_file():
            print(f"no such file: {args.kill_note}", file=sys.stderr)
            return 2
        kill_text = args.kill_note.read_text(encoding="utf-8")
    findings = check(args.note.read_text(encoding="utf-8"), args.allow, kill_text)
    for finding in findings:
        print(finding)
    print(f"{len(findings)} finding(s). This does not check that any source is right.")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
