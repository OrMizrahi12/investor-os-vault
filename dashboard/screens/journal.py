"""Journal: what we did, decided and left open, by day and across days, the coach files, the Lessons and a search. Plan: dashboard/PLAN.md, screen 5.

It shows the files word for word and judges nothing. A coach file's system view never reaches this screen, in any part. Only one part is drawn at a time, because the files are long.
"""

import streamlit as st

import data
import view

now, today = data.now_utc(), data.local_today()
read_on = data.nice_date(today)

st.title("Journal")
st.html(f'<p class="d-muted d-text">{view.e(view.COACH_LINE)} Read-only. Everything here comes from files on this computer, read {view.e(read_on)}, {now:%H:%M} UTC. This page fetches nothing and sends nothing. {view.e(view.JOURNAL_RECORD)}</p>')

pages = view.company_pages(data.company_list())
wanted_day = st.query_params.get("day")
part = st.radio("Part", view.JOURNAL_PARTS, horizontal=True, label_visibility="collapsed")
st.header(part)


def say_problems(lines):
    for line in lines:
        st.html(view.problem(line))


if part == "Lessons":
    lessons = data.lesson_files()
    say_problems(lessons["problems"])
    if lessons["lessons"]:
        st.html(view.journal_count(f'{view._plural(len(lessons["lessons"]), "lesson")}, newest first. Open one to read it.', read_on))
        st.html(view.lesson_blocks(lessons["lessons"], today, pages))
    else:
        st.html(view.missing("a lesson.", "a correction written to Lessons/, as Rules/memory.md asks."))

elif part == "Decisions":
    try:
        files = data.decision_files()
    except data.PROBLEMS as err:
        files = []
        st.html(view.problem(f"The coach files could not be read: {err}. Putting the file right would fill it."))
    st.html('<p class="d-muted d-text">My view and what I then decided, from each coach file. A decision file\'s system view is not shown here. Open the file to read it.</p>')
    if files:
        st.html(view.decisions_table(files, pages))
    else:
        st.html(view.missing("a coach file.", "a decision run through the coach, which writes one in Journal/decisions/."))

elif part == "Search":
    words = st.text_input("Search the Journal and Lessons", max_chars=200, placeholder="Plain words, any case")
    st.html('<p class="d-muted d-text">Plain text across the daily Journal files and Lessons, line by line. A coach file is left out, because it holds the system\'s view.</p>')
    if words.strip():
        found = data.search_journal(words)
        say_problems(found["problems"])
        shown = min(len(found["rows"]), view.SEARCH_ROWS)
        st.html(view.journal_count(f'Showing {shown} of {view._plural(len(found["rows"]), "line")}, newest day first. Lessons follow.', read_on))
        if found["rows"]:
            st.html(view.search_table(found["rows"], today, pages))

else:
    journal = data.journal_view()
    say_problems(journal["problems"])
    if part == "By day":
        days = journal["days"]
        if days:
            names = [d["day"] for d in days]
            if wanted_day and wanted_day not in names:
                st.html(view.problem("That address names no day in Journal/, so this shows the newest one."))
            chosen = st.selectbox("Day", names, index=names.index(wanted_day) if wanted_day in names else 0, format_func=data.nice_date)
            day = next(d for d in days if d["day"] == chosen)
            st.html(view.journal_count(f'{view._plural(len(day["sessions"]) + bool(day["top"]), "block")} on this day, newest first. "Above" or "below" in a line means the file\'s own order. Open one to read it.', read_on))
            st.html(view.journal_day_blocks(day, pages))
        else:
            st.html(view.missing("a day in Journal/.", "a working session, which writes one as Rules/memory.md asks."))
    elif part == "What we decided":
        items = journal["decided"]
        st.html(view.journal_count(f'{view._plural(len(items), "line")} across {view._plural(len(journal["days"]), "day")}, newest first.{view.quiet_words(journal["quiet"]["decided"])}', read_on))
        if items:
            st.html(view.journal_items_table(items, pages))
    else:
        only_mine = st.checkbox('Only lines that start "For me"')
        items = [i for i in journal["left_open"] if i["for_me"]] if only_mine else journal["left_open"]
        st.html(f'<p class="d-muted d-text">{view.e(view.LEFT_OPEN_LINE)}</p>')
        st.html(view.journal_count(f'{view._plural(len(items), "line")} across {view._plural(len(journal["days"]), "day")}.{view.quiet_words(journal["quiet"]["left_open"])}', read_on))
        if items:
            st.html(view.journal_items_table(items, pages))
