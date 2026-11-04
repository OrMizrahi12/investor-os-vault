"""Portfolio and cash. Plan: dashboard/PLAN.md, screen 3.

Real comes first and paper always carries its label, so the two never mix. Stocks count at the last saved close, as Rules/cash.md says.
A position with no saved close is Unknown, and so is everything that depends on it. Nothing falls back to cost. It gives no action, size or grade.
"""

import streamlit as st

import data
import view

now, today = data.now_utc(), data.local_today()
st.title("Portfolio and cash")
st.html(f'<p class="d-muted d-text">{view.e(view.COACH_LINE)} Read-only. Everything here comes from files on this computer, read {view.e(data.nice_date(today))}, {now:%H:%M} UTC. This page fetches nothing and sends nothing. '
        '"Last saved close" is the newest close saved by hand, and it may not be today\'s. Each one shows its date.</p>')

rows = data.company_list()
pages = {r["ticker"]: r for r in rows if r["ticker"]}
books = data.position_notes()
for line in books["problems"]:
    st.html(view.problem(f"This note in Portfolio/ could not be read, so nothing from it is shown: {line}. Marking it kind: real or kind: paper, with cash, last checked and a five-column Positions table, would fill it."))

st.header("Real", anchor="real")
if books["real"]:
    for book in books["real"]:
        st.subheader(book["file"])
        st.html(view.book_block(book, pages, today))
else:
    st.html(view.missing(*view.REAL_MISSING))

st.header("Paper, made-up money", anchor="paper")
if books["paper"]:
    for book in books["paper"]:
        st.html(f'<div class="c-draft">{view.e(view.PAPER_LABEL)}</div>')
        st.html(view.book_block(book, pages, today))
else:
    st.html(view.missing("a paper portfolio.", "a note in Portfolio/ marked kind: paper."))

st.header("Room under the limit, names against bets", anchor="limit")
st.html(view.missing(*view.LIMIT_MISSING))
