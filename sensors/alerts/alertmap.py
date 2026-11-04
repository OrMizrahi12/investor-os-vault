"""The proposed alert map and the two-year test's reading of Corning's events. Data only.

Rules/alerts.md is the proposal. The levels on the events are Claude's reading, for the owner to correct.
"""

# id, signal group, signal, condition, level, who reads it today
MAP = [
 ("R1", "Kill lines", "K1 to K9", "A line is crossed, on its own wording and test date.", "Red", "A person. Sensors only say a filing came."),
 ("R2", "Thesis claims", "C1 to C8", "A dated fact contradicts a claim the thesis rests on. Claude says it appears broken. You rule.", "Red", "A person"),
 ("R3", "8-K items", "1.03, 2.04, 2.06, 3.01, 4.02, 5.01, or 1.02 with no 1.01", "Presumed Red until read. You can drop it to Orange by ruling.", "Red", "8-K watcher"),
 ("R4", "Shared exposures", "A group under the test for one thesis", "One event crosses a kill line in one position and a line or load-bearing claim in another. One alert, naming them all.", "Red", "Nothing yet. No position is on file."),
 ("O1", "Kill lines", "K3, K8, K9", "One step short of a two-quarter line: one quarter at or below K3's line, or one fall on K8 or K9, outside Q1.", "Orange", "A person"),
 ("O2", "Thesis claims", "C1 to C8", "A dated fact from a filing, release, call or customer could change a claim, a chance or a grade, in either direction.", "Orange", "A person"),
 ("O3", "8-K items and forms", "3.02, an 8.01 share program, a 424B5 for new shares", "New shares become possible. This is K6's starting point.", "Orange", "8-K watcher, radar"),
 ("O4", "Buy-below", "Close against the line", "A close falls under the buy-below. Once per crossing. It re-arms only after a close back above.", "Orange", "By hand. No sensor compares them."),
 ("O5", "Trim-above", "Close against the line", "A rise takes the close above the trim-above, on a position you hold. Once per crossing.", "Orange", "By hand. No sensor compares them."),
 ("O6", "Buy-below and trim-above", "A refresh", "A refresh moves a line across the price, with no price move.", "Orange", "A person, after a refresh"),
 ("O7", "Sizing limit", "5% hard limit", "A position or group is over 5% at a refresh. Add nothing. It never forces a sale.", "Orange", "portfolio-manager script, when run"),
 ("O8", "Cash and counts", "Rules/cash.md, rule 2", "Cash under the 5% floor at a refresh. Cash above 50% for 24 months. More than 20 positions.", "Orange", "portfolio-manager script, when run"),
 ("O9", "Method triggers", "Aaa, segments, core, restated filings", "Aaa moves a point from 6.12%. Segments are recast. Core changes. A 10-K/A or 10-Q/A. A late-filing notice.", "Orange", "A person"),
 ("O10", "SEC letters", "UPLOAD", "A staff letter opens a thread, or tells the company to change something. Later letters in a thread and a closing letter are Info.", "Orange", "Radar lists them as plain filings. Nothing reads them."),
 ("O11", "8-K items", "5.02", "CEO, CFO or COO arrives or leaves. A director change is Info after reading.", "Orange", "8-K watcher"),
 ("O12", "Ownership", "13D, Form 4", "A Schedule 13D. An officer or director buys on the open market. A holder named in a catalyst note exits.", "Orange", "Radar"),
 ("O13", "Catalyst dates", "Catalysts/", "A stated date passes with no Outcome written, or a stated date moves.", "Orange", "Radar"),
 ("O14", "Shared exposures and grades", "A group or a grade", "A dated event calls for a new group or a new grade. Claude proposes. You rule.", "Orange", "A person"),
 ("O15", "Thesis claims", "A claim with no kill line", "The same claim goes against us on three reports running. You decide if it needs a line.", "Orange", "A person"),
 ("O16", "The system itself", "Silence", "A sensor fails, or a results date is three trading days past with no reading on file.", "Orange", "Nothing yet"),
 ("I1", "8-K items", "2.02, read, no claim moved", "Results are in. Each kill line's reading is listed.", "Info", "8-K watcher, then a person"),
 ("I2", "8-K items", "Routine items", "A 7.01 conference notice, 5.07 votes, 5.03, 9.01, a routine 1.01 credit line, a director under 5.02.", "Info", "8-K watcher"),
 ("I3", "Filings", "10-Q, 10-K", "The filing came, and the refresh is done or due. Old and new base value, buy-below and trim-above.", "Info", "Radar, then the valuation skill"),
 ("I4", "Insider forms", "Forms 3, 4, 144", "One line a day: how many forms, how many sales. No line for each form.", "Info", "Radar"),
 ("I5", "Other filings", "13G, proxy, 11-K, SD, shelf, Form 25, CORRESP", "Listed once.", "Info", "EDGAR list"),
 ("I6", "Catalyst dates", "Catalysts/", "Once on entering the 90-day horizon, and again at 7 days. Not every day.", "Info", "Radar"),
 ("I7", "Radar", "Screen leads", "A count and a link. A lead is never a pick.", "Info", "Radar"),
 ("I8", "Radar", "Graph walks", "Which notes an event touches. A link does not mean the event reaches that company.", "Info", "Radar"),
 ("I9", "Buy-below and trim-above", "Where the price stands", "Last close, its date and the two lines. No change and no percent move.", "Info", "Saved close"),
 ("I10", "Sizing, cash, shared exposures", "Where the book stands", "Names against bets, cash level and room under the limit, at a refresh.", "Info", "portfolio-manager script, when run"),
 ("I11", "Kill lines", "K8, K9", "A lone Q1 fall. Readings on lines whose test is not due: K1, K4, K5.", "Info", "A person"),
 ("I12", "The system itself", "Source ages", "How old each saved source is, and which sensors ran.", "Info", "Dashboard"),
]

# line, claim, Red, Orange one step before, or None
LINES = [
 ("K1", "C2", "Optical sales in Q4 2027 at or below $2,379M.", "None. Readings are Info until the test."),
 ("K2", "C2", "A named customer ends a deal or says it was reduced.", "A customer lowers spending and does not say so (O2)."),
 ("K3", "C3", "Optical margin at or below 17.9%, two quarters running, through Q4 2030.", "One quarter at or below 17.9%."),
 ("K4", "C4", "Q4 2028 core sales × 4 under $27,000M.", "None. Readings are Info until the test."),
 ("K5", "C5", "Deposit-out cash, 12 months to Sept. 30, 2027, under $1,505M.", "None. Readings are Info until the test."),
 ("K6", "C5", "More than zero shares sold under the $2B program, in any 10-Q or 10-K.", "A new share program or warrant (O3)."),
 ("K7", "C7", "Corning names a year after 2028 or drops 2028, or has not said it accelerated by the Q4 2028 call.", "Softer words on the timing (O2)."),
 ("K8", "C2", "Optical sales lower than the quarter before, two quarters running, through Q4 2030.", "One fall outside Q1. A lone Q1 fall is Info."),
 ("K9", "C1", "Meta, Amazon and Microsoft spending lower than the quarter before, two quarters running, through Q4 2030.", "One fall outside Q1. A lone Q1 fall is Info."),
]

# item, first pass, what reading does
ITEMS = {
 "1.01": ("Orange", "Stays for a deal, a customer or debt that changes a claim. A routine credit line drops to Info."),
 "1.02": ("Orange", "Red if no 1.01 is in the same filing. A replaced agreement stays Orange until read."),
 "1.03": ("Red", "Bankruptcy."),
 "1.05": ("Orange", "A material cyber incident. Stays if it stops plants or shipments."),
 "2.01": ("Orange", "A finished purchase or sale. Changes what the base value covers."),
 "2.02": ("Orange", "Every kill line is read here. Drops to Info if no claim moved."),
 "2.03": ("Orange", "New debt. Drops to Info if it only replaces old debt."),
 "2.04": ("Red", "Debt called early."),
 "2.05": ("Orange", "Exit costs. Stays if it touches a segment the thesis uses."),
 "2.06": ("Red", "Material impairment. Often old news after reading, so a ruling can drop it."),
 "3.01": ("Red", "Delisting or a listing moved. A plain transfer can drop by ruling."),
 "3.02": ("Orange", "New shares or warrants sold."),
 "3.03": ("Orange", "Holders' rights change."),
 "4.01": ("Orange", "Auditor change."),
 "4.02": ("Red", "The accounts cannot be relied on, so neither can base value."),
 "5.01": ("Red", "Change of control."),
 "5.02": ("Orange", "Stays for CEO, CFO or COO. A director drops to Info."),
 "5.03": ("Info", "Bylaws."),
 "5.07": ("Info", "Votes."),
 "7.01": ("Info", "Alone: Info if the first paragraph is a notice. Anything else is Orange."),
 "8.01": ("Orange", "Anything can sit here. The $2B share program did."),
 "9.01": ("Info", "Exhibits only."),
}

EDGAR = "https://www.sec.gov/Archives/edgar/data/24741/"
Q3R = EDGAR + "000002474126000273/glw-20261027xex99xq32026.htm"
Q2R = EDGAR + "000002474126000253/glw-20260728xex99xq22026.htm"
Q1R = EDGAR + "000002474126000198/glw-20260328xex991xq12026.htm"
Q4R = EDGAR + "000002474126000034/glw-20251231xex99xq42025.htm"
Q325 = EDGAR + "000002474125000109/glw-20251028xex99.htm"
Q225 = EDGAR + "000162828025036303/glw-20250729xex99.htm"
Q125 = EDGAR + "000162828025020470/glw-20250429xex991.htm"
Q424 = EDGAR + "000162828025002912/glw-20241231xex99xq42024.htm"
K10 = EDGAR + "000002474126000124/glw-20251231.htm"
Q10 = EDGAR + "000002474126000279/glw-20260930.htm"

# Quarter: optical sales, optical net income, core sales, operating cash, capex, deposits line, source
QUARTERS = [
 ("Q1 2024", None, None, 3258, 96, 252, -25, ("Q1 release, Apr. 29, 2025", Q125)),
 ("Q2 2024", None, None, 3604, 521, 242, 7, ("Q2 release, July 29, 2025", Q225)),
 ("Q3 2024", 1246, 175, 3733, 699, 217, 66, ("Q4 release, Jan. 29, 2025", Q424)),
 ("Q4 2024", 1368, 194, 3874, 623, 254, -54, ("Q4 release, Jan. 29, 2025", Q424)),
 ("Q1 2025", 1355, 201, 3679, 151, 208, -16, ("Q1 release, Apr. 28, 2026", Q1R)),
 ("Q2 2025", 1566, 247, 4045, 708, 308, 59, ("Q2 release, July 28, 2026", Q2R)),
 ("Q3 2025", 1652, 295, 4272, 784, 334, -92, ("Q3 release, Oct. 27, 2026", Q3R)),
 ("Q4 2025", 1701, 305, 4412, 1052, 432, 317, ("Q1 release, Apr. 28, 2026", Q1R)),
 ("Q1 2026", 1846, 387, 4345, 362, 332, -171, ("Q1 release, Apr. 28, 2026", Q1R)),
 ("Q2 2026", 2072, 438, 4738, 1717, 422, 880, ("Q2 release, July 28, 2026", Q2R)),
 ("Q3 2026", 2379, 532, 5081, 1061, 545, -70, ("Q3 release, Oct. 27, 2026", Q3R)),
]
REPORTED = {"Q4 2024": "2025-01-29", "Q1 2025": "2025-04-29", "Q2 2025": "2025-07-29", "Q3 2025": "2025-10-28",
            "Q4 2025": "2026-01-28", "Q1 2026": "2026-04-28", "Q2 2026": "2026-07-28", "Q3 2026": "2026-10-27"}

# What reading does to each 8-K in the window. accession: (final level, map id, claim, what it said)
READ_8K = {
 "0001628280-25-002912": ("Info", "I1", "", "Q4 2024 results. No claim moved, on my reading. Display price rises were already a known line."),
 "0001206774-25-000133": ("Info", "I2", "", "Notice of the Mar. 18, 2025 investor event."),
 "0001628280-25-020470": ("Orange", "O9", "C4", "Q1 2025 results. Yen rate behind core moved from ¥107 to ¥120, and Automotive Glass Solutions moved segment."),
 "0001206774-25-000335": ("Orange", "O11", "", "President and COO retires. A new COO is named."),
 "0001206774-25-000340": ("Info", "I2", "", "Three directors retire, plus votes."),
 "0001206774-25-000358": ("Info", "I2", "", "Notice: the CEO speaks at a J.P. Morgan conference."),
 "0001628280-25-036303": ("Info", "I1", "", "Q2 2025 results. Records and a forecast. No claim moved, on my reading."),
 "0001206774-25-000489": ("Info", "I2", "", "A $1.5B credit line replaces an equal one. Item 1.02 with 1.01, so no Red."),
 "0001206774-25-000651": ("Info", "I2", "", "Notice: the CFO speaks at a Citi conference."),
 "0001206774-25-000710": ("Info", "I2", "", "A new director."),
 "0000024741-25-000109": ("Orange", "O2", "C4, C6", "Q3 2025 results. The 20% margin target a year early. Apple's $2.5B commitment is in a release."),
 "0000024741-26-000034": ("Orange", "O2", "C2, C4", "Q4 2025 results. Plan upgraded. First filing to name Meta."),
 "0001206774-26-000108": ("Info", "I2", "", "Notice: the CFO speaks at a Morgan Stanley conference."),
 "0000024741-26-000198": ("Orange", "O2", "C2, C6", "Q1 2026 results. Two more long deals. Segments recast. Core changes Apr. 1."),
 "0001206774-26-000266": ("Info", "I2", "", "Notice of the May 6 investor event."),
 "0001206774-26-000265": ("Info", "I2", "", "Annual meeting votes."),
 "0001206774-26-000273": ("Orange", "O3", "C2, C5", "NVIDIA partnership. Warrants on up to 18M shares sold for $500M."),
 "0001206774-26-000285": ("Info", "I2", "", "Notice: the CFO and COO speak at a J.P. Morgan conference."),
 "0000024741-26-000253": ("Orange", "O2", "C2, C4, C6", "Q2 2026 results. First filing to name Amazon. Run-rate targets. A wafer plant shutdown."),
 "0001206774-26-000517": ("Info", "I2", "", "Notice: the CFO speaks at a Citi conference."),
 "0001193125-26-389321": ("Orange", "O3", "C5", "Up to $2B of new shares through Goldman Sachs. The 424B5 the same day counts as the same event."),
 "0000024741-26-000273": ("Orange", "O2", "C2, C6", "Q3 2026 results. Four long deals. Solar ramp slower than anticipated."),
}

SEC = "https://www.sec.gov/Archives/edgar/data/24741/"
# Events no 8-K carried. date, what, map id, level, claim, seen by, source label, url
OTHER = [
 ("2025-06-09", "SEC staff open a comment letter on the Q1 2025 10-Q. Public only after the review closed.", "O10", "Orange", "", "radar", "SEC staff letter, June 9, 2025", SEC + "000000000025006045/filename1.pdf"),
 ("2026-02-26", "SEC staff tell Corning to remove the adjustment behind most of the gap to core. Public only after the review closed.", "O10", "Orange", "", "radar", "SEC staff letter, Feb. 26, 2026", SEC + "000000000026002022/filename1.pdf"),
 ("2026-08-31", "Lumen's two-year reservation ends about now (calc.). No Outcome is written.", "O13", "Orange", "C2", "radar", "Cabling Install, Aug. 1, 2024", "https://cablinginstall.com/data-center/press-release/55130261/lumen-secures-corning-fiber-optic-cable-to-connect-ai-enabled-data-centers"),
 ("2025-03-18", "Investor event updates the Springboard plan. Only the notice was filed the day before. A later 8-K calls it a \"recent upgrade\".", "O2", "Orange", "C4", "person", "8-K, filed May 13, 2025", SEC + "000120677425000358/glw4484671-8k.htm"),
 ("2025-08-06", "Apple commits $2.5B to Kentucky cover glass.", "O2", "Orange", "C6", "person", "WBKO, Aug. 6, 2025", "https://www.wbko.com/2025/08/06/apple-corning-manufacture-100-iphone-apple-watch-cover-glass-kentucky"),
 ("2025-09-04", "China puts anti-dumping duties on US fiber.", "O2", "Orange", "C1", "person", "Bloomberg Law, Sept. 4, 2025, excerpt", "https://news.bloomberglaw.com/international-trade/china-hits-us-optical-fiber-imports-with-anti-dumping-tariffs"),
 ("2025-11-05", "China announces the end of that duty. Sources differ on whether it is a suspension.", "O2", "Orange", "C1", "person", "Digitimes, Nov. 6, 2025, first paragraph only", "https://www.digitimes.com/news/a20251106PD225.html"),
 ("2026-01-27", "Meta deal of up to $6B. In a Corning filing one day later.", "O2", "Orange", "C2", "person", "Meta post, Jan. 27, 2026", "https://about.fb.com/news/2026/01/meta-6-billion-agreement-corning-support-us-manufacturing/"),
 ("2026-05-19", "Fujikura's plan adds rival capacity, its largest step from 2030.", "O2", "Orange", "C1, C3", "person", "Fujikura mid-term plan, May 19, 2026", "https://www.fujikura.co.jp/newsrelease/management/__icsFiles/afieldfile/2026/05/19/260519_en.pdf"),
 ("2026-06-08", "Amazon deal. In a Corning filing 50 days later.", "O2", "Orange", "C2", "person", "Telecompetitor, June 8, 2026", "https://www.telecompetitor.com/amazon-strikes-multibillion-dollar-fiber-deal-with-corning/"),
 ("2026-08-04", "Furukawa adds rival capacity from the second half of its FY2028.", "O2", "Orange", "C1, C3", "person", "Furukawa notice, Aug. 4, 2026", "https://finance-frontend-pc-dist.west.edge.storage-yahoo.jp/disclosure/20260804/20260804507869.pdf"),
 ("2026-08-06", "Polysilicon tariff proclaimed, bearing on Solar.", "O2", "Orange", "C6", "person", "Proclamation, Aug. 6, 2026", "https://www.whitehouse.gov/presidential-actions/2026/08/adjusting-imports-of-polysilicon-and-its-derivatives-into-the-united-states/"),
 ("2026-08-12", "T1 says its wafer contract covers Phase 1 only.", "O2", "Orange", "C6", "person", "T1 Q2 call, Aug. 12, 2026, third-party transcript", "https://www.webull.com/news/15429873268204544"),
 ("2026-08-20", "Zayo deal. No Corning filing names it through Nov. 2, 2026.", "O2", "Orange", "C2", "person", "Broadband Breakfast, Aug. 20, 2026", "https://broadbandbreakfast.com/zayo-reaches-fiber-reserve-deal-with-corning/"),
 ("2026-09-08", "Verizon deal. In a Corning filing 49 days later.", "O2", "Orange", "C2", "person", "Verizon release, Sept. 8, 2026", "https://www.verizon.com/about/news/verizon-corning-broadband-ai-fiber-agreement"),
 ("2026-09-29", "AT&T deal of more than $3B. In a Corning filing 28 days later.", "O2", "Orange", "C2", "person", "AT&T and Corning release, Sept. 29, 2026", "https://www.prnewswire.com/news-releases/att-and-corning-team-up-to-engineer-the-connected-world-with-fiber-302892879.html"),
 ("2026-10-20", "Hengtong's CTO warns of a turn after 2028.", "O2", "Orange", "C1, C3", "person", "Eastmoney, Oct. 20, 2026", "https://finance.eastmoney.com/a/202610203900316315.html"),
 ("2026-10-21", "AT&T says capital spending runs \"roughly $1 billion lower\". It does not say the deal shrank, so K2 stays uncrossed.", "O2", "Orange", "C1, C2", "person", "AT&T Q3 call, Oct. 21, 2026, third-party transcript", "https://www.earningswhispers.com/transcript/T/Q32026"),
 # read and dropped: the noise a news watch brings
 ("2025-03-11", "Suniva and Heliene join a US solar chain. No size given.", "I5", "Info", "C6", "person", "Manufacturing Dive, Mar. 11, 2025", "https://www.manufacturingdive.com/news/corning-suniva-heliene-hemlock-semiconductor-form-us-solar-supply-chain/742039/"),
 ("2025-05-13", "Broadcom collaboration. No size given.", "I5", "Info", "C7", "person", "Corning release, May 13, 2025", "https://investor.corning.com/news-and-events/news/news-details/2025/Corning-Collaborates-with-Broadcom-To-Accelerate-AI-Data-Center-Processing-Capacity/default.aspx"),
 ("2025-07-18", "EU accepts cover glass commitments. No finding of infringement.", "I5", "Info", "C6", "person", "Commission release, July 18, 2025", "https://ec.europa.eu/commission/presscorner/api/files/document/print/es/ip_25_1868/IP_25_1868_EN.pdf"),
 ("2025-08-15", "T1 Energy agreements on polysilicon and wafers, subject to conditions.", "I5", "Info", "C6", "person", "T1 Energy 8-K, Aug. 15, 2025", "https://www.sec.gov/Archives/edgar/data/1992243/000121390025077036/ea0253426-8k_t1energy.htm"),
 ("2025-09-24", "Corning to make Microsoft's hollow-core fiber. No size given.", "I5", "Info", "C8", "person", "Fierce Network, Sept. 24, 2025", "https://www.fierce-network.com/broadband/microsoft-strikes-new-deal-corning-boost-its-hollow-core-fiber"),
 ("2025-11-11", "China suspends a germanium export ban until Nov. 27, 2026.", "I6", "Info", "C3", "person", "Fastmarkets, Nov. 11, 2025", "https://fastmarkets.com/insights/china-suspends-export-prohibition-on-superhard-materials-us"),
 ("2026-02-05", "Lumen's CEO says it expanded the partnership, terms unknown.", "I5", "Info", "C2", "person", "SDxCentral, Feb. 5, 2026", "https://www.sdxcentral.com/news/lumen-slashes-debt-downplays-ai-bubble-concerns/"),
 ("2026-03-26", "Small ISPs report long fiber lead times and higher costs.", "I5", "Info", "C3", "person", "Light Reading, Mar. 26, 2026", "https://www.lightreading.com/fttx/bead-winners-fret-over-fiber-costs-lead-times"),
 ("2026-04-09", "Poland plant plan.", "I5", "Info", "C5", "person", "Corning release, Apr. 9, 2026", "https://www.corning.com/optical-communications/worldwide/en/home/news-and-events/news-releases/2026/04/corning-expands-poland-manufacturing-for-ai-data-centers.html"),
 ("2026-10-21", "Wilmington expansion of $585M.", "I5", "Info", "C5", "person", "WECT, Oct. 21, 2026", "https://www.wect.com/2026/10/21/corning-invest-585m-add-414-jobs-wilmington-expansion/"),
]

# The largest one-day moves: what the record shows. A test of misses only. A price move never raises an alert.
MOVE_READ = {
 "2026-06-29": ("none", "No company news, per one article, which blames an index change.", "TIKR, updated July 9, 2026", "https://www.tikr.com/blog/corning-stock-soared-16-in-a-day-to-256-heres-where-it-could-go-in-2026"),
 "2026-01-27": ("news", "Meta deal, the same day. Only a news watch would catch it.", "Meta post, Jan. 27, 2026", "https://about.fb.com/news/2026/01/meta-6-billion-agreement-corning-support-us-manufacturing/"),
 "2026-09-14": ("filing", "First session after the Sept. 11 8-K on the share program. Peers fell too.", "24/7 Wall St., Sept. 14, 2026", "https://247wallst.com/investing/2026/09/14/corning-tumbles-12-on-2b-at-the-market-equity-offering-coherent-sinks-11-lumentum-drops-9-fabrinet-slides-6/"),
 "2026-07-28": ("filing", "Q2 results, the same day.", "Q2 release, July 28, 2026", Q2R),
 "2026-05-06": ("filing", "NVIDIA 8-K, the same day.", "8-K, May 6, 2026", SEC + "000120677426000273/glw4631061-8k.htm"),
 "2025-07-29": ("filing", "Q2 results, the same day.", "Q2 release, July 29, 2025", Q225),
 "2026-07-01": ("unknown", "Nothing on file. One search found no cause for this date.", "", ""),
 "2026-07-02": ("none", "\"No guidance cut, no lost contract\", per one article.", "TIKR, updated July 4, 2026", "https://www.tikr.com/blog/corning-stock-fell-11-in-a-day-after-a-391-run-is-glw-finally-worth-a-look-near-200"),
}
