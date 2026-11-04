#!/usr/bin/env python3
"""Build graph.html from the Typed links tables in Companies/. Fails if the two sides of a link disagree."""
import json, math, re, sys, html
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; C=ROOT/"Companies"
NOTES=sorted(p.stem for p in C.glob("*.md") if p.stem!="README")

def inline(md):
    t=html.escape(md,quote=False)
    t=re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+)\)',lambda m:f'<a href="{html.escape(m.group(2))}" target="_blank" rel="noopener">{m.group(1)}</a>',t)
    t=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',t)
    t=re.sub(r'\[\[([^\]]+)\]\]',lambda m:f'<button class="nl" data-n="{html.escape(m.group(1))}">{m.group(1)}</button>' ,t)
    return t

edges={}; info={}
for n in NOTES:
    t=(C/f"{n}.md").read_text()
    m=re.search(r'^## Typed links\n(.*?)(?=^## )',t,re.S|re.M)
    if not m: sys.exit("no section "+n)
    sec=m.group(1)
    other=re.search(r'\*\*Other links, none of the four types:\*\*\n\n((?:- .*\n)+)',sec)
    bad=re.search(r'\*\*Could not support:\*\*\n\n((?:- .*\n)+)',sec)
    info[n]=dict(other=[inline(l[2:]) for l in other.group(1).splitlines()] if other else [],
                 bad=[inline(l[2:]) for l in bad.group(1).splitlines()] if bad else [])
    for line in sec.splitlines():
        if not line.startswith("| ") or line.startswith("| Link") : continue
        if not line.strip("| "): continue  # the template's blank row
        c=[x.strip() for x in line.strip("|").split(" | ")]
        if len(c)!=7: sys.exit(f"bad row in {n}: {line[:80]}")
        lab,o,ch,what,size,ev,src=[x.strip() for x in c]
        o=re.sub(r'\[\[|\]\]| \(no note\)','',o)
        if lab=="supplies": k,a,b="supplies",n,o
        elif lab=="customer of": k,a,b="supplies",o,n
        elif lab=="competes with": k,a,b=("competes",)+tuple(sorted([n,o]))
        elif lab=="partners with": k,a,b=("partners",)+tuple(sorted([n,o]))
        else: sys.exit("bad type "+lab)
        key=(k,a,b)
        rec=dict(k=k,a=a,b=b,chain=ch,what=what,size=size,ev=ev,src=src)
        if key in edges:
            if {k:v for k,v in edges[key].items() if k!="_seen"}!=rec: sys.exit(f"sides differ {key}")
            edges[key]["_seen"]+=1
        else:
            rec["_seen"]=1; edges[key]=rec
for key,e in edges.items():
    want=sum(1 for x in (e["a"],e["b"]) if x in NOTES)
    if e["_seen"]!=want: sys.exit(f"link not on both sides: {key} seen {e['_seen']} want {want}")
    if "http" not in e["src"] or not re.search(r'(19|20)\d\d|undated',e["src"]): sys.exit(f"no dated source {key}")

SHORT={("supplies","Corning","AT&T"):"more than $3B",("supplies","Corning","Verizon"):"80M+ fiber miles",("supplies","Corning","Lumen"):"10% of capacity",
 ("supplies","Corning","Meta"):"up to $6B",("supplies","Corning","Amazon"):"multibillion",("supplies","Corning","NVIDIA"):"$1.0B deposit",
 ("partners","Corning","NVIDIA"):"$500M warrants",("supplies","Corning","Apple"):"$2.5B",("partners","NVIDIA","Zayo"):"8,000+ miles, target",
 ("partners","Corning","Optiemus"):"30M units, plan"}
TYPE={}
for n in "AT&T Verizon Lumen Zayo Meta Amazon NVIDIA Broadcom Apple Suniva".split(): TYPE[n]="customer"
TYPE["T1 Energy"]="customer"
for n in ["Microsoft","Heliene","Optiemus","Shin-Etsu Handotai"]: TYPE[n]="partner"
for n in ["Amphenol","Fujikura","Sumitomo Electric","Prysmian","Furukawa Electric","YOFC","Hengtong","Heraeus","Display rivals","Specialty rivals","Automotive rivals","Life Sciences rivals"]: TYPE[n]="rival"
for n in ["Molex","STL","Linde","Umicore"]: TYPE[n]="other"
TYPE["Corning"]="hub"

# polar layout: (angle degrees clockwise from east, factor)
cx,cy,rx,ry=590,395,500,330
P={"AT&T":(-160,1),"Verizon":(-145,1),"Lumen":(-127,1),"Zayo":(-106,1.02),"NVIDIA":(-72,1.02),"Broadcom":(-54,1),"Microsoft":(-46,.6),"Heraeus":(-37,1),
 "Meta":(-22,.98),"Amazon":(-8,.98),"Prysmian":(3,.62),"Molex":(8,.98),"Amphenol":(19,.98),"Fujikura":(27,.84),"Sumitomo Electric":(41,1.06),"Furukawa Electric":(50,.74),
 "YOFC":(84,.98),"Hengtong":(70,.66),"Specialty rivals":(99,.96),"Display rivals":(113,.98),"Automotive rivals":(127,1.0),"Life Sciences rivals":(139,1.03),
 "Heliene":(157,1.02),"Suniva":(153,.68),"T1 Energy":(168,.76),"Shin-Etsu Handotai":(136,.6),"Apple":(175,1.0),"Optiemus":(-170,.7)}
nodes=[]
names={e["a"] for e in edges.values()}|{e["b"] for e in edges.values()}|set(NOTES)
for n in sorted(names):
    if n not in TYPE: sys.exit("no type "+n)
    if n=="Corning": x,y=cx,cy
    elif n in P:
        a,f=P[n]; x=cx+rx*f*math.cos(math.radians(a)); y=cy+ry*f*math.sin(math.radians(a))
    elif n in("STL","Linde","Umicore"):
        x={"STL":860,"Linde":960,"Umicore":1060}[n]; y=800
    else: sys.exit("no position "+n)
    nodes.append(dict(id=n,type=TYPE[n],note=n in NOTES,x=round(x),y=round(y),other=info.get(n,{}).get("other",[]),bad=info.get(n,{}).get("bad",[])))
E=[]
for key,e in edges.items():
    E.append(dict(k=e["k"],a=e["a"],b=e["b"],chain=e["chain"],what=html.escape(e["what"],quote=False),size=html.escape(e["size"],quote=False),ev=e["ev"],src=inline(e["src"]),short=SHORT.get(key,"")))

U=lambda lab,u:f'<a href="{u}" target="_blank" rel="noopener">{lab}</a>'
L=dict(
 k8=U("8-K, May 6, 2026","https://www.sec.gov/Archives/edgar/data/24741/000120677426000273/glw4631061-8k.htm"),
 q=U("10-Q, filed Oct. 29, 2026","https://www.sec.gov/Archives/edgar/data/24741/000002474126000279/glw-20260930.htm"),
 ttv=U("joint release on TelecomTV, Aug. 21, 2026","https://www.telecomtv.com/content/next-gen-telco-infra/zayo-stays-ahead-of-ai-infrastructure-demand-through-long-term-fibre-supply-agreement-with-corning-56118/"),
 ac=U("AT&T Q3 call, Oct. 21, 2026, third-party transcript","https://www.earningswhispers.com/transcript/T/Q32026"),
 meta=U("Meta post, Jan. 27, 2026","https://about.fb.com/news/2026/01/meta-6-billion-agreement-corning-support-us-manufacturing/"),
 pry=U("Prysmian Q3 call, Oct. 29, 2026, third-party transcript","https://stockanalysis.com/quote/bit/PRY/transcripts/659713-q3-2026/"),
 fuj=U("Fujikura mid-term plan, May 19, 2026","https://www.fujikura.co.jp/newsrelease/management/__icsFiles/afieldfile/2026/05/19/260519_en.pdf"),
 kaxe=U("KAXE, Aug. 6, 2026","https://www.kaxe.org/local-news/2026-08-06/heliene-layoffs-93-workers-mountain-iron-solar-panel-factory"),
 t1=U("T1 release, Aug. 12, 2026","https://www.stocktitan.net/news/TE/t1-energy-reports-second-quarter-2026-ja67zotmn79k.html"),
 gc=U("Corning Q3 call, Oct. 27, 2026, third-party transcript","https://www.fool.com/earnings/call-transcripts/2026/10/27/corning-glw-q3-2026-earnings-call-transcript/"),
 fast=U("Fastmarkets, Nov. 11, 2025","https://fastmarkets.com/insights/china-suspends-export-prohibition-on-superhard-materials-us"),
 um=U("Umicore fibre page, undated, search copy, page now redirects","https://eom.umicore.com/en/germanium-solutions/markets/telecom-optical-fibre/"),
 k=U("10-K, filed Feb. 12, 2026","https://www.sec.gov/Archives/edgar/data/24741/000002474126000124/glw-20251231.htm"),
 tnw=U("The Next Web, June 9, 2026","https://thenextweb.com/news/fujikura-fibre-optic-cable-price-hike-data-centres"),
 stl=U("STL Q2 FY27 call, published Oct. 23, 2026, third-party transcript","https://www.investing.com/news/transcripts/earnings-call-transcript-sterlite-technologies-posts-record-q2-2026-results-93CH-4969071"),
 aph=U("Amphenol Q3 call, Oct. 28, 2026, third-party transcript","https://www.fool.com/earnings/call-transcripts/2026/10/28/amphenol-aph-q3-2026-earnings-call-transcript/"),
 ls=U("SDxCentral, Feb. 5, 2026","https://www.sdxcentral.com/news/lumen-slashes-debt-downplays-ai-bubble-concerns/"),
 q1=U("Q1 release, Apr. 28, 2026","https://www.sec.gov/Archives/edgar/data/24741/000002474126000198/glw-20260328xex991xq12026.htm"),
 q3=U("Q3 release, Oct. 27, 2026","https://www.sec.gov/Archives/edgar/data/0000024741/000002474126000273/glw-20261027xex99xq32026.htm"),
 lr=U("Light Reading, Mar. 26, 2026","https://www.lightreading.com/fttx/bead-winners-fret-over-fiber-costs-lead-times"),
 mj=U("job post, Feb. 20, 2026, Exa's copy, page not opened","https://jdpreferred.com/job/commercial-sourcing-manager-data-center-connectivity-c296c9/"),
 sd=U("13G/A, filed Sept. 10, 2025","https://www.sec.gov/Archives/edgar/data/24741/000095017025113900/0000950170-25-113900.txt"),
)
EVENTS=[
 dict(id="nvidia-ends",at="NVIDIA",title="The partnership agreement with Corning ends",status="Hypothetical. No source says this is likely",chain="fiber",
  src=f"The warrant term is in the {L['k8']}. The deposit is in the {L['q']}.",
  direct={"Corning":"Corning holds a $1.0B deposit under a supply agreement through Dec. 31, 2029. The $180 warrant can end with the partnership, with exceptions. What happens to the deposit is unknown.",
          "Zayo":"More than 8,000 of Zayo's planned 15,000 new route miles are \"in collaboration with NVIDIA\". That is a target, so the plan may need rework."},
  roles={"customer":"Shares Corning's fiber capacity. The plants NVIDIA backs could slip, which hurts, or NVIDIA's volume could free up, which helps. Direction unknown.",
         "partner":"Its fiber is also made at Corning's North Carolina sites. Whether this reaches hollow-core fiber is unknown.",
         "rival":"NVIDIA's demand might go elsewhere, or Corning's added capacity might not arrive. Either could help a rival. No source says so."},
  off=""),
 dict(id="att-capex",at="AT&T",title="Annual capital spending planned about $1B lower",status="Happened, Oct. 21, 2026. $300M to $400M of it is Mexico",chain="fiber",
  src=f"{L['ac']}.",
  direct={"Corning":"AT&T's deal is more than $3B. If the cut reduces fiber volumes, the deal may run below its headline. The call does not say that it does. AT&T keeps its goal of 60 million locations."},
  roles={"customer":"Any fiber AT&T does not take could free supply for other Corning buyers. Only if the cut touches fiber.","partner":"Unknown. The link is on one fiber type.","rival":"Less pull on the market would ease pressure on prices. Too small to tell from what was read."},
  off=f"AT&T also bought Lumen's consumer fiber business ({L['ls']}). That is none of the four link types, so the walk does not travel it."),
 dict(id="meta-less",at="Meta",title="Meta takes far less than the \"up to $6B\" ceiling",status=f"Hypothetical. The figure is a ceiling, and impact starts in 2027",chain="fiber",
  src=f"{L['meta']}. ISP reports: {L['lr']}. Meta's job post: {L['mj']}.",
  direct={"Corning":"Hickory would lose volume from its anchor customer. The sales effect is unknown, because Meta's share is not disclosed."},
  roles={"customer":"More Corning capacity could be open to them. Some small ISPs tied cancellations to the Meta deal, through unnamed sources.","partner":"Unknown.","rival":"A large buyer taking less, or buying elsewhere. Meta's sourcing job post shows that it runs bids. Direction unknown."},off=""),
 dict(id="prysmian-deals",at="Prysmian",title="Two more hyperscaler deals, hoped for \"by December or January\"",status="Forecast by its CEO",chain="fiber",
  src=f"{L['pry']}.",
  direct={"Corning":"A named rival locks in more data center demand on take-or-pay terms. The customers are not named, so overlap with Corning's is unknown.",
          "Molex":"Prysmian's other take-or-pay buyer. More deals compete for the same planned capacity, due from H2 2028."},
  roles={"customer":"If it is their deal, they gain a second source. A Corning deal does not mean a sole supplier.","partner":"Unknown.","rival":"Rival's rival. Weak: the link only says both compete with Corning."},
  off="Amazon is reached only through Corning. Its direct link to Prysmian is for low carbon aluminum cables, not fiber, so the fiber walk does not use it. Turn on all chains and Amazon moves to one step."),
 dict(id="fujikura-capacity",at="Fujikura",title="Largest capacity step, about 4x on FY2022, in phases from 2030",status="A plan",chain="fiber",
  src=f"{L['fuj']}.",
  direct={"Corning":"Rival supply that arrives late. The vault's open question is a turn after 2028, and Corning's price terms are unknown.",
          "Sumitomo Electric":"Named with Fujikura in the high-end segment. Whether they meet head to head is my reading.",
          "Furukawa Electric":"Named with Fujikura in the high-end segment. Whether they meet head to head is my reading."},
  roles={"customer":"More supply later could ease lead times and price. Which of them Fujikura sells to is not named.","partner":"Unknown.","rival":"More world supply from 2030. Applies to any fiber maker, so this says little."},off=""),
 dict(id="heliene-layoffs",at="Heliene",title="93 layoffs noticed at Mountain Iron",status="Happened, Aug. 6, 2026",chain="solar",
  src=f"{L['kaxe']}. The article does not mention Corning, so any effect on the deal is unknown. Solar sales: {L['q3']}.",
  direct={"Suniva":"Supplies the cells for Heliene's modules, under their sourcing deal. The most directly exposed company on this map, though the size is unknown.",
          "Corning":"The plant is named in the three-way solar chain. Solar sales were $436M in Q3 2026, and the effect is unknown."},
  roles={"customer":"Shares Corning's wafers and polysilicon. Weak: fewer modules at Heliene might free wafers.","partner":"Hemlock's other owner. Weak."},off=""),
 dict(id="t1-cells",at="T1 Energy",title="First cell production moved to Q1 2027",status="Happened, stated Aug. 12, 2026. The Q1 2027 date is a forecast",chain="solar",
  src=f"{L['t1']}. Corning's ramp: {L['q3']}.",
  direct={"Corning":"T1's plant cannot use Corning wafers before then (my reading). Corning's own ramp ran slower than expected too. These are two delays, not one."},
  roles={"customer":"Same wafer lines at Corning. Weak.","partner":"Hemlock polysilicon goes into these wafers. Weak."},off=""),
 dict(id="apple-kentucky",at="Apple",title="All iPhone and Apple Watch cover glass made in Kentucky by the end of 2026",status="Forecast by Corning's CFO",chain="cover glass",
  src=f"{L['gc']}. Glass Innovations sales: {L['q3']}.",
  direct={"Corning":"A whole plant tied to one customer, under a $2.5B commitment. Glass Innovations sales fell in Q3 2026."},
  roles={"partner":"Cover-glass finishing in India, for the local phone market. No source links it to Apple."},off=""),
 dict(id="germanium",at="Umicore",title="China's germanium export suspension ends, unless extended",status="Dated Nov. 27, 2026. Forecast",chain="fiber",
  src=f"{L['fast']}. Umicore's claim on fiber makers is its own: {L['um']}.",
  direct={},roles={},off=f"Nothing lights up, and that is the finding. No source ties Umicore to Corning or to any fiber maker by name, and Corning names no fiber input supplier ({L['k']}). The event may matter. The vault cannot show it."),
]
CANNOT=[
 ("Input suppliers",f"Linde, Umicore and Air Products to Corning. They sell to the industry, and Corning names no fiber input supplier ({L['k']}). A germanium or helium event cannot be walked."),
 ("STL as a rival",f"Its call names only unnamed \"global peers\" ({L['stl']}). Corning's list leaves it out. It makes the same product, and I did not draw a link on that alone."),
 ("Which hyperscalers buy from rivals",f"Fujikura says \"almost all US hyperscalers\" and names none ({L['tnw']}). Prysmian names none for fiber ({L['pry']}). So no rival-to-Meta, Amazon or Microsoft fiber link."),
 ("Rival against rival",f"Corning's list of Amphenol, Fujikura, Sumitomo and Prysmian ({L['k']}) does not show that they compete with each other. Only the three Japanese makers and the two Chinese makers have a source that puts them together, and those links are marked as my reading."),
 ("Customer against customer","AT&T, Verizon, Lumen and Zayo. Meta, Amazon and Microsoft. NVIDIA and Broadcom. T1, Suniva and Heliene. No source in the vault says they compete. Sharing a sector is not a source, and I did not fill this in from memory."),
 ("Amphenol sells to NVIDIA",f"An analyst asked about NVIDIA designs. Its CEO said \"I do not discuss specific customers\" ({L['aph']})."),
 ("STL sells to AT&T, NVIDIA or Amazon",f"Its call lists them as backers of fiber, and does not say they buy from STL ({L['stl']})."),
 ("Display and Automotive customers",f"Three customers are 59% and three are 61% of those sales, unnamed ({L['k']}). Samsung Display is a 7.94% holder ({L['sd']}). No source read calls it a customer, and a catalyst note that did was corrected."),
 ("Unnamed deals",f"Two hyperscalers ({L['q1']}) and the unnamed Q3 deals ({L['q3']}). No name, so no link, and they may overlap with named deals."),
 ("Sizes not known","Zayo, Microsoft, Broadcom, T1, Suniva, Heliene, Prysmian to Amazon, and every joint venture but Optiemus's plan. No dollar figure for Verizon, Amazon or Lumen. NVIDIA's contract value. Do not add the sizes shown: the deals may overlap."),
 ("Not in the four types","AT&T's purchase of Lumen's consumer fiber, Amphenol's of CommScope's connectivity business, Samsung Display's holding, two board links, and the joint statement by Corning, Prysmian, Lightera and AFL. Each is written in the notes, and none is drawn."),
]
stats=dict(links=len(E),notes=len(NOTES),strong=sum(e["ev"] in("Stated","Read together") for e in E),
  weak=sum(e["ev"] not in("Stated","Read together") for e in E),off=sum("Corning" not in (e["a"],e["b"]) for e in E),
  dollar=sum(bool(re.search(r'[$€]',e["size"])) for e in E),nodes=len(nodes),isolated=sum(1 for n in nodes if not any(n["id"] in(e["a"],e["b"]) for e in E)))
print(stats)
data=dict(nodes=nodes,edges=E,events=EVENTS,stats=stats)
J=json.dumps(data,ensure_ascii=False).replace("</","<\\/")
tpl=Path(__file__).with_name("graph.tpl.html").read_text()
cant="".join(f"<li><b>{a}.</b> {b}</li>" for a,b in CANNOT)
out=tpl.replace("/*DATA*/",J).replace("<!--CANNOT-->",cant)
for k,v in stats.items(): out=out.replace("{{%s}}"%k,str(v))
(ROOT/"graph.html").write_text(out)
print("written",len(out))
