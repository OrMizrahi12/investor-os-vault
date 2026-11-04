"""Company: one page for any note in Companies/, with its own address, /company?company=GLW. Plan: dashboard/PLAN.md, screen 2.

It shows what is on file and says what is not. It compares no close to a line, and it gives no action, size, grade or score.
"""

import streamlit as st

import data
import health
import view

theme = st.context.theme.type or "light"
now = data.now_utc()
st.title("Company")

rows = data.company_list()
pages = view.company_pages(rows)
names = [r["name"] for r in rows]
wanted = st.query_params.get("company")
row = data.find_company(wanted, rows)
choice = st.selectbox("Company", names, index=names.index(row["name"]) if row else None, placeholder="Choose a company", label_visibility="collapsed")
if choice and (not row or choice != row["name"]):
    st.query_params["company"] = data.company_slug(pages[choice])
    st.rerun()


def chart(title, spec, small, words=""):
    """A chart never comes without its source. A test counts these against the charts drawn."""
    st.html(view.chart_head(title, small, words))
    st.altair_chart(spec, width="stretch", theme="streamlit")


if row is None:
    if wanted:
        st.html(view.problem(f"No note in Companies/ has the name or ticker {wanted}. Nothing is shown in its place."))
    st.html(f'<p class="d-muted d-text">{view.e(view.COACH_LINE)} One page for each note in Companies/. Files read {view.e(data.nice_date(now.date()))}, {now:%H:%M} UTC.</p>')
    values = data.latest_valuations()
    st.html(view.company_list_table(rows, {r["company"] for r in values["rows"]}))
    st.header("Watchlist")
    st.html('<p class="d-muted">What the sensors follow.</p>')
    try:
        st.html(view.watchlist_table(data.watchlist_rows(), now))
    except data.PROBLEMS as err:
        st.html(view.problem(err))
    st.stop()

if row["problem"]:
    st.html(view.problem(f'{row["file"]} could not be read: {row["problem"]}'))
    st.stop()

model = data.company_view(row, now.date())
name = row["name"]
trouble = model["problems"]
st.html(view.company_top(model))

st.header("What is missing, and what is on file")
st.html(view.missing_table(model))
st.html(view.on_file_table(model, now))

st.header("Thesis status")
if trouble["research"]:
    st.html(view.problem(f'The files in Research/ could not be read: {trouble["research"]}'))
st.html(view.thesis_block(model, pages))
st.html(view.kill_block(model, pages))

st.header("Price against value")
for line in [trouble["value"], *model["value"]["problems"]]:
    if line:
        st.html(view.problem(f"The saved valuation run could not be read: {line}"))
valued = model["value"]["run"]
if trouble["close"]:
    st.html(view.problem(f'The saved close could not be read: {trouble["close"]}'))
if valued is None:
    st.html(f'<p class="d-text"><b>Not on file.</b> No base value, strategic value, buy-below, trim-above or price zone exists for this company on the board, and none is worked out here. See the list above for what would fill it.</p>')
else:
    st.html(view.value_layers(valued))
    st.subheader("Price zones and the last close")
    st.html(view.price_zones(valued, model["close"], model["today"]))
    st.html(view.value_summary(valued))
    worked = view.src_markup(view.e(f'Close: {valued["price"]["source"]}, through {data.nice_date(valued["price"]["date"])}. Lines: calc., {valued["run_file"]}, worked out {data.nice_date(valued["worked_out"])}'))
    chart(f'{valued.get("ticker") or name} close against the values worked out {data.nice_date(valued["worked_out"])}', view.value_chart(valued, theme), worked,
          "The band and the two lines are one date's values, drawn flat so the price can be read against them. They are not what value was in earlier years. Close, not adjusted for dividends.")
    st.html(view.value_table(valued))
    st.html(view.value_no_vote(valued))
    with st.expander("Every input and its source"):
        st.html(view.value_inputs_table(valued))
    st.subheader("What changes the base value and the two lines most")
    st.html(view.what_if_lead(valued))
    what_if = view.src_markup(view.e(f'What-if, calc., {valued["run_file"]}, worked out {data.nice_date(valued["worked_out"])}'))
    left, right = st.columns(2)
    with left:
        chart(f'Base middle, {view._money(valued["base"]["mid"])} by the method', view.what_if_chart(valued, "base", theme), what_if)
    with right:
        chart(f'Buy-below, {view._money(valued["buy_below"])} by the method', view.what_if_chart(valued, "buy", theme), what_if)
    chart(f'Trim-above, {view._money(valued["trim_above"])} by the method, the {view.TOP_ROWS} widest', view.what_if_chart(valued, "trim", theme), what_if)
    with st.expander("Every what-if, with its basis"):
        st.html(view.what_if_table(valued))
        for line in valued["what_if"]["not_run"]:
            st.html(view.sourced(f'<p class="d-muted">Not run: <span class="d-runtext">{view.e(line)}</span></p>', what_if))
    with st.expander("The slope of each input, one step at a time"):
        st.html(view.what_if_slopes(valued))

st.header("Catalysts")
st.html(view.problem(f'Catalysts/ could not be read: {trouble["catalysts"]}') if trouble["catalysts"] else view.catalysts_table(model))

st.header("Graph neighbors")
if trouble["links"]:
    st.html(view.problem(f'The Typed links tables could not be read: {trouble["links"]}'))
else:
    st.html(view.links_table(model, pages))
    words = view.other_links_words(model, pages)
    if words:
        with st.expander("Other links, and what could not be supported"):
            st.html(f'<p class="d-muted d-text">Word for word from {view.e(view._note_src(model))}.</p>{words}')

st.header("Latest 8-Ks")
trouble_now, _ = data.run_trouble_or_problem()
for words in filter(None, [view.run_trouble_lines(trouble_now, "8-K watcher"), view.age_tag("sec_copy", model["periodic"]["retrieved"], model["today"]) if model["periodic"] else ""]):
    st.html(words)
if trouble["filings"]:
    st.html(view.problem(f'Inbox/ could not be read: {trouble["filings"]}'))
elif model["filings"]:
    st.html('<p class="d-muted">Attention is how much a filing changes the facts. It is not a view on value.</p>')
    st.html(view.filings_table(model["filings"]))
else:
    st.html('<p class="d-text">No 8-K note on file for this company. The 8-K watcher follows only the watchlist, so adding it to sensors/8k-watch/watchlist.toml would fill this.</p>')

if row["ticker"] == data.CORNING:
    st.header("Corning financial health")
    try:
        note = health.read_note()
        result = health.checks(note)
    except data.PROBLEMS as err:
        st.html(view.problem(f"The financial health panel could not be read: {err}"))
    else:
        from_note = f'Companies/Corning.md, last checked {data.nice_date(note["last_checked"])}'
        tenk = result["tenk"]
        filings = lambda items: view.src_markup(f'{view.e(from_note)}. Filings: {view.link(items[-1]["url"], items[-1]["filing"])} to {view.link(items[0]["url"], items[0]["filing"])}')  # noqa: E731
        span = f'FY{min(y["year"] for y in note["years"])} to FY{max(y["year"] for y in note["years"])}'
        st.html('<p class="d-muted">From the "Financial health summary" and the tables under it in Companies/Corning.md. These numbers are not base value.</p>')
        st.html(view.health_summary(note, result["rows"]))
        left, right = st.columns(2)
        with left:
            chart(f'Margins, {span}', view.margins_chart(note, theme), filings(note["years"]),
                  "FY2016 net margin includes a $2.7 billion non-taxable gain. FY2017 includes the Tax Act charges. Each year is from the latest 10-K that reports it.")
        with right:
            chart("GAAP against core net income, last 8 quarters", view.gaap_core_chart(note, theme), filings(note["quarters"]),
                  "Each quarter as first reported in its own release. Core's method changed twice with no restatement.")
        left, right = st.columns(2)
        with left:
            chart(f'Free cash flow, {span}', view.fcf_chart(note, theme), filings(note["years"]),
                  "Operating cash flow minus capex. Deposits are not taken out here, because filings before FY2024 were not read for them.")
        with right:
            chart("Free cash flow with and without stated deposits", view.deposit_chart(note, theme), filings(note["watch"]),
                  "Two full years, then two nine-month periods, so compare like with like. FY2024's amounts were \"not material\". No deposit is stated for nine months of 2025. The 2026 deposit is printed only as $1.0 billion, so the split in that bar is approximate.")
            st.html('<p class="d-chart-title">Second reading: without the whole filed line</p>')
            st.html(view.deposit_line_table(note))
            st.html('<p class="d-muted">The chart takes out only deposits received, so repayments of older deposits stay in. This table takes out the whole line, "Customer deposits and government incentives". The filing does not split that line, so neither reading is clean.</p>')
            st.html('<p class="d-chart-title">Third reading, an estimate: both sides of the deposits out</p>')
            st.html(view.deposit_estimate_table(note))
            st.html('<p class="d-muted">An estimate, not a filed figure. It assumes all older deposits applied ran through the filed line, which the filing does not say.</p>')
        left, right = st.columns(2)
        with left:
            chart("Debt ladder, as of Dec. 31, 2025", view.ladder_chart(note, theme), view.src_markup(f'{view.e(from_note)}. Filing: {view.link(tenk["url"], f"10-K, filed {data.nice_date(tenk["filed"])}")}'),
                  "The latest schedule filed. The 10-Q gives none. In 2026 Corning repaid some of this, and yuan loans grew.")
        with right:
            st.html(view.scoreboard_html(health.scoreboard(note), view.src_markup(view.e(f'{from_note}. Counted on value-tests.html and flags.html'))))
        st.subheader("Check against the latest 10-K")
        for words in filter(None, [view.age_tag("tenk", tenk["filed"], model["today"])]):
            st.html(words)
        st.html(view.check_headline(result))
        caption = f'Our number: {view.e(from_note)}. 10-K number: {view.link(tenk["url"], f"10-K, filed {data.nice_date(tenk["filed"])}")}. Other numbers: the filing named in the row.'
        st.html(view.check_table([r for r in result["rows"] if r["group"] == "Summary"], caption))
        with st.expander("Every number behind the charts"):
            st.html(view.check_table([r for r in result["rows"] if r["group"] != "Summary"], caption))

    st.header("Corning earnings yield against Aaa")
    try:
        yld = data.yield_view()
    except data.PROBLEMS as err:
        st.html(view.problem(err))
    else:
        for words in filter(None, [view.age_tag("fred_monthly", data.month_end(yld["aaa_month"]), model["today"])]):
            st.html(words)
        st.html(view.yield_summary(yld))
        chart("Corning earnings yield against Moody's Aaa", view.yield_chart(yld, theme),
              view.src_markup(f'Yield: calc., {view.link(yld["step"]["url"], f"{yld["step"]["form"]}, filed {data.nice_date(yld["step"]["filed"])}")}, and the close from Yahoo through yfinance, fetched {view.e(data.nice_date(yld["fetched"].date()))}. Aaa: {view.link(yld["aaa_url"], f"FRED AAA, downloaded {data.nice_date(yld["aaa_downloaded"].date())}")}'))
        with st.expander("Every month as a table"):
            st.html(view.month_rows_table(yld))
    st.html(f'<p class="d-muted">{view.e(view.NO_VIEW_LINE)}</p>')

st.header("The note's other sections")
if model["left"]:
    st.html(f'<p class="d-muted d-text">Word for word from {view.e(view._note_src(model))}. A line with a figure and no dated source says so, because this page cannot supply one.</p>')
    for section in model["left"]:
        with st.expander(section["title"]):
            st.html(view.note_words(section["text"], model["refs"], pages))
else:
    st.html('<p class="d-text">None in the note.</p>')

st.header("History")
st.html(view.problem(f'The history could not be read: {trouble["history"]}') if trouble["history"] else view.history_table(model))
