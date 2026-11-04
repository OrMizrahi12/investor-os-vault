"""Ideas and alerts: every company or lead at its stage, the rejection log, and every line the routines wrote. Plan: dashboard/PLAN.md, screen 4.

It shows what the files say and compares nothing, so it raises nothing new. A lead is something to read, never a pick. The filters only choose what to show.
"""

import streamlit as st

import data
import view

now = data.now_utc()
today = now.date()
read_on = data.nice_date(today)
run_small = lambda run: view.src_markup(view.e(f'{run["report"]}, saved run of {data.nice_date(run["run_date"])}'))  # noqa: E731
trouble_now, _ = data.run_trouble_or_problem()


def say(words):
    """st.html refuses empty markup, and most of the time these lines have nothing to say."""
    if words:
        st.html(words)


st.title("Ideas and alerts")
st.html(f'<p class="d-muted d-text">{view.e(view.COACH_LINE)} Read-only. Everything here comes from files on this computer, read {view.e(read_on)}, {now:%H:%M} UTC. This page fetches nothing and sends nothing.</p>')

try:
    book = data.journal_alerts()
    alerts = data.alert_rows(book, today)
except data.PROBLEMS as err:
    book, alerts = None, None
    trouble = err
ideas = data.ideas_view()
pages = view.company_pages(ideas["pages"])
waiting = sum(r["state"] == "Waiting" for r in alerts["rows"]) if alerts else None
st.html(view.jump_line(waiting, read_on))

st.header("Ideas, from the first lead to a decision", anchor="ideas")
st.html(f'<p class="d-text"><b>{view.e(view.LEAD_LABEL)}.</b> That goes for every lead on this screen, at any stage. A stage says what is on file, not how good an idea is. A company sits at its newest dated step, and on the same day at the furthest one. This reading of the files is Claude\'s, for me to correct.</p>')
for line in ideas["problems"]:
    st.html(view.problem(line))
st.html(view.stage_strip(ideas, read_on))

for stage in data.STAGES:
    name, what, fill = view.STAGE_WORDS[stage]
    rows = ideas["stages"][stage]
    st.subheader(name, anchor=f"stage-{stage}")
    st.html(f'<p class="d-muted d-text">{view.e(what)}</p>')
    st.html(view.sourced(f'<p class="d-muted">{len(rows)} at this stage.</p>', view.src("calc., counted from the files this screen reads", read_on)))
    if stage == "lead":
        radar = ideas["radar"]
        if radar is None:
            st.html(f'<p class="d-text"><b>Not on file.</b> What would fill it: {view.e(fill)}</p>')
            continue
        say(view.age_tag("radar_run", radar["run_date"], today))
        say(view.run_trouble_lines(trouble_now, "Radar"))
        st.html(view.sourced(view.lead_counts(ideas), run_small(radar)))
        if radar["screen"]["status"] != "ok":
            st.html(view.problem(f'The screen did not finish on this run: {radar["screen"]["status"]}'))
        when = data.nice_date(radar["run_date"])
        for part in ideas["steps"]:
            st.html(view.sourced(view.radar_step_line(part["step"]) + view.step_counts(part), run_small(radar)))
            st.html(f'<div class="i-box">{view.radar_leads_table(part["leads"], when)}</div>')
            if part["hidden"]:
                with st.expander("Hidden by the radar: may not be new growth"):
                    st.html(view.sourced(f'<p class="d-muted">{len(part["hidden"])} companies, {view.e(part["step"]["earlier"])} to {view.e(part["step"]["later"])}.</p>', run_small(radar)))
                    st.html(f'<div class="i-box">{view.radar_leads_table(part["hidden"], when)}</div>')
    elif rows:
        box = "i-box" if len(rows) > 8 else ""
        st.html(f'<div class="{box}">{view.stage_table(rows, stage, pages, read_on)}</div>')
    else:
        st.html(f'<p class="d-text">None at this stage. What would put one here: {view.e(fill)}</p>')

st.header("Rejection log", anchor="rejection-log")
log = ideas["log"]
if log is None:
    st.html('<p class="d-text"><b>Not on file.</b> What would fill it: Research/Rejection log.md.</p>')
else:
    st.html(f'<p class="d-muted"><span class="d-copied">{view.note_inline(log["remark"])}</span></p>')
    st.html(view.sourced(view.rejection_counts(ideas), view.src(log["file"], data.nice_date(log["written"]))))
    st.html(view.rejection_table(log["rows"], view.src_markup(view.e(f'{log["file"]}, written {data.nice_date(log["written"])}. Rows are as written, nearest month first. Month: calc., read from the words beside it.'))))

st.subheader("Proposed by the hunt, waiting for me")
proposed = [(report, report["proposed"]) for report in ideas["reports"] if report["proposed"]]
if proposed:
    st.html('<p class="d-text">None of these is in the log. They go in only if I add them myself.</p>')
    for report, rows in proposed:
        st.html(view.rejection_table(rows, view.src_markup(view.e(f'{report["file"]}, {data.nice_date(report["day"])}. Claude\'s sort, on XBRL figures not read in print. Month: calc.')), sits_at=False))
else:
    st.html('<p class="d-text">None on file. The Monthly hunt would put any here.</p>')

st.header("Alerts", anchor="alerts")
if alerts is None:
    st.html(view.problem(f"The Journal could not be read: {trouble}"))
else:
    rows = alerts["rows"]
    st.html(view.alerts_summary(rows, book["days_read"], read_on))
    for line in alerts["problems"]:
        st.html(view.problem(line))
    level, rule, routine, state, first, last = st.columns((1, 1, 1.4, 1.2, 1, 1))
    levels = level.multiselect("Level", list(view.ALERT_LEVELS), placeholder="All")
    rules = rule.multiselect("Rule", sorted({r["rule"] for r in rows if r["rule"]}, key=lambda rule: (rule[0], int(rule[1:]))), placeholder="All")
    routines = routine.multiselect("Routine", list(data.ROUTINES), placeholder="All")
    states = state.multiselect("Ruled or waiting", list(data.ALERT_STATES), placeholder="All")
    since = first.date_input("From", value=None, format="YYYY-MM-DD")
    until = last.date_input("To", value=None, format="YYYY-MM-DD")
    shown = data.filter_alerts(rows, levels, rules, routines, states, since, until)
    st.html(view.alert_filter_line(shown, rows))
    if shown or not rows:
        st.html(view.alerts_table(shown))
    else:
        st.html('<p class="d-text">No line fits these filters.</p>')

    st.subheader("When each routine last left a record", anchor="routines")
    st.html('<p class="d-muted d-text">A routine that did not run leaves no line. Nothing notices that for me (O16). This table only shows the last record.</p>')
    st.html(view.routine_table(book, read_on, today))
    st.subheader("Guardrails", anchor="guardrails")
    try:
        guarded = data.guard_events()
    except data.PROBLEMS as err:
        st.html(view.problem(f"The guardrail record could not be read: {err}"))
    else:
        st.html(view.sourced(view.guard_summary(guarded), view.src(".claude/guardrails/blocked.jsonl, calc.", read_on)))
        st.html(view.guard_table(guarded, view.src_markup(view.e(f".claude/guardrails/blocked.jsonl, read {read_on}"))))

st.header("The hunt's reports", anchor="hunt")
if ideas["reports"]:
    for report in ideas["reports"]:
        with st.expander(f'{report["file"]}'):
            st.html(view.hunt_block(report))
else:
    st.html('<p class="d-text">No run on file. The Monthly hunt\'s first run would fill it, with a report in Research/ with Monthly hunt in its name.</p>')
if ideas["triage_files"]:
    st.html(f'<p class="d-note d-text">Earlier triage by hand: {view.e(", ".join(ideas["triage_files"]))}.</p>')

st.header("Catalyst radar", anchor="radar")
radar = ideas["radar"]
if radar is None:
    st.html('<p class="d-text">No radar run on file. This page does not start one. The next Daily run, or the radar by hand, would fill it.</p>')
else:
    small = run_small(radar)
    say(view.age_tag("radar_run", radar["run_date"], today))
    say(view.run_trouble_lines(trouble_now, "Radar"))
    caption = small.replace("<small", "<span").replace("</small>", "</span>")
    st.html(view.sourced(view.radar_summary(radar), small))
    for line in radar["problems"]:
        st.html(view.problem(line))
    st.subheader("Dates due or opening within the radar's horizon")
    st.html(view.sourced(f'<p class="d-muted">The horizon is {radar["horizon_days"]} days.</p>', small))
    st.html(view.radar_dates_table(radar["dates"]["soon"], caption))
    st.subheader("Dates passed, Outcome not written")
    st.html(view.radar_dates_table(radar["dates"]["passed"], caption))
    with st.expander("Wide windows"):
        st.html(view.sourced(f'<p class="d-muted">{len(radar["dates"]["wide"])} catalysts.</p>', small))
        st.html(view.radar_dates_table(radar["dates"]["wide"], caption))
    st.html(view.sourced(f'<p class="d-muted">Also {radar["dates"]["later_count"]} with dates further out and {radar["dates"]["no_date_count"]} with no date given.</p>', small))
    st.subheader("New events")
    st.html(view.radar_events_table(radar["events"], caption))
    hidden = radar.get("hidden") or {}
    if hidden.get("grants"):
        with st.expander("Hidden: director stock grants"):
            st.html(view.sourced(f'<p class="d-muted">{hidden["grant_count"]} grants.</p>', small))
            st.html(view.radar_events_table(hidden["grants"], caption))
    st.subheader("Graph walk")
    st.html('<p class="d-muted">A link means a link exists in the Typed links tables, not that the event reaches that company. A walk started only by a screen lead goes one step. Every row shown here is in the report.</p>')
    st.html(view.radar_walks(radar["walks"], caption))
    if hidden.get("step2_count"):
        with st.expander("Hidden: second-step links"):
            st.html(view.sourced(f'<p class="d-muted">{hidden["step2_count"]} links.</p>', small))
            st.html(view.radar_hidden_links(radar["walks"], caption))

st.header("Latest 8-Ks", anchor="filings")
say(view.run_trouble_lines(trouble_now, "8-K watcher"))
try:
    notes = data.read_inbox()
except data.PROBLEMS as err:
    st.html(view.problem(err))
else:
    st.html(view.sourced(f'<p class="d-muted">{len(notes)} notes in Inbox, newest first. Attention is how much a filing changes the facts. It is not a view on value.</p>', view.src("Inbox/, calc.", read_on)))
    st.html(view.filings_table(notes))

st.header("How old each source is", anchor="sources")
st.html('<p class="d-muted d-text">Age of copy is how long ago we saved it. Age of data is how old the newest figure inside it is. A monthly figure counts from the end of its month. The last column says it in words when a source is past my limit. It is a display, and it raises nothing.</p>')
try:
    st.html(view.sources_table(data.source_rows(now), now))
except data.PROBLEMS as err:
    st.html(view.problem(err))
