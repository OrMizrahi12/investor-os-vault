#!/usr/bin/env python3
"""Build a professional relationship map from two CSV files and report what it suggests.

nodes.csv columns: id,name,org,role,group
    group is one of: company, customer, supplier, adviser, competitor, other
edges.csv columns: source,target,type,detail,strength
    type examples: prior_employer, education, board, deal, commercial, association, opinion
    strength: 1 (weak, e.g. same school) or 2 (strong, e.g. same class or same team at the same time)

Output (Markdown): a Mermaid diagram, hubs, cross-organization links, shared-history leads
(possible acquirers or competitive threats), and people with no known links.
Use professional information only: no home addresses, family details or private-life data.
Standard-library Python 3 only.
"""
import argparse
import csv
import re
import sys
from collections import defaultdict

HISTORY_TYPES = {"prior_employer", "education", "board", "deal", "association"}
GROUPS = ["company", "customer", "supplier", "adviser", "competitor", "other"]


def load(nodes_path, edges_path):
    with open(nodes_path, newline="") as fh:
        nodes = {r["id"].strip(): {k: (v or "").strip() for k, v in r.items()} for r in csv.DictReader(fh)}
    edges = []
    with open(edges_path, newline="") as fh:
        for r in csv.DictReader(fh):
            r = {k: (v or "").strip() for k, v in r.items()}
            if r["source"] not in nodes or r["target"] not in nodes:
                print(f"warning: edge {r['source']}->{r['target']} refers to an unknown node; skipped",
                      file=sys.stderr)
                continue
            try:
                r["strength"] = int(r.get("strength") or 1)
            except ValueError:
                r["strength"] = 1
            edges.append(r)
    return nodes, edges


def mid(s):
    return "n_" + re.sub(r"[^A-Za-z0-9_]", "_", s)


def label(s):
    return s.replace('"', "'")


def mermaid(nodes, edges):
    lines = ["```mermaid", "flowchart LR"]
    by_org = defaultdict(list)
    for nid, n in nodes.items():
        by_org[n.get("org") or "unaffiliated"].append(nid)
    for i, (org, ids) in enumerate(sorted(by_org.items())):
        lines.append(f'  subgraph g{i}["{label(org)}"]')
        for nid in ids:
            n = nodes[nid]
            text = n.get("name") or nid
            if n.get("role"):
                text += f"<br/>{n['role']}"
            lines.append(f'    {mid(nid)}["{label(text)}"]')
        lines.append("  end")
    for e in edges:
        arrow = "===" if e["strength"] >= 2 else "---"
        lines.append(f'  {mid(e["source"])} {arrow}|{label(e.get("type") or "link")}| {mid(e["target"])}')
    lines.append("```")
    return "\n".join(lines)


def report(nodes, edges, focus):
    def grp(nid):
        n = nodes[nid]
        if focus and n.get("org") == focus:
            return "company"
        return n.get("group") or "other"

    degree = defaultdict(int)
    for e in edges:
        degree[e["source"]] += e["strength"]
        degree[e["target"]] += e["strength"]

    out = []
    out.append("## Hubs (weighted links)")
    hubs = sorted(degree.items(), key=lambda kv: kv[1], reverse=True)[:10]
    for nid, d in hubs:
        n = nodes[nid]
        out.append(f"- {n.get('name') or nid} ({n.get('role')}, {n.get('org')}): {d}")

    out.append("\n## Cross-organization links")
    cross = [e for e in edges if nodes[e["source"]].get("org") != nodes[e["target"]].get("org")]
    for e in cross:
        a, b = nodes[e["source"]], nodes[e["target"]]
        out.append(f"- {a.get('name')} ({a.get('org')}) - {b.get('name')} ({b.get('org')}):"
                   f" {e.get('type')} {('- ' + e['detail']) if e.get('detail') else ''}"
                   f"{' [strong]' if e['strength'] >= 2 else ''}")
    if not cross:
        out.append("- none recorded")

    out.append("\n## Leads from shared history")
    leads = []
    for e in edges:
        if (e.get("type") or "") not in HISTORY_TYPES:
            continue
        ga, gb = grp(e["source"]), grp(e["target"])
        pair = {ga, gb}
        a, b = nodes[e["source"]], nodes[e["target"]]
        desc = f"{a.get('name')} ({a.get('org')}) & {b.get('name')} ({b.get('org')}): {e.get('type')}" \
               f"{(' - ' + e['detail']) if e.get('detail') else ''}"
        if pair == {"company", "competitor"} or pair == {"company", "other"}:
            leads.append(("possible acquirer or partner tie", e["strength"], desc))
        elif pair == {"competitor", "customer"}:
            leads.append(("competitive threat: rival close to a customer's buyer", e["strength"], desc))
        elif pair == {"company", "customer"}:
            leads.append(("relationship that supports the company's sales", e["strength"], desc))
        elif "adviser" in pair and ("company" in pair or "competitor" in pair):
            leads.append(("adviser connection (deal or restructuring relevance)", e["strength"], desc))
    for kind, strength, desc in sorted(leads, key=lambda t: (t[0], -t[1])):
        out.append(f"- {kind}{' [strong]' if strength >= 2 else ''}: {desc}")
    if not leads:
        out.append("- none recorded")

    out.append("\n## People with no known links (research gaps)")
    isolated = [nid for nid in nodes if degree[nid] == 0]
    for nid in isolated:
        n = nodes[nid]
        out.append(f"- {n.get('name') or nid} ({n.get('role')}, {n.get('org')})")
    if not isolated:
        out.append("- none")

    counts = defaultdict(int)
    for nid in nodes:
        counts[grp(nid)] += 1
    out.append("\n## Coverage by group")
    for g in GROUPS:
        if counts[g]:
            out.append(f"- {g}: {counts[g]}")
    out.append("\nEach lead is a hypothesis: confirm with independent evidence before acting.")
    return "\n".join(out)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("nodes")
    p.add_argument("edges")
    p.add_argument("--focus", help="org name of the company being researched (else nodes in group 'company')")
    p.add_argument("--out", help="write Markdown to this file instead of stdout")
    args = p.parse_args(argv)
    nodes, edges = load(args.nodes, args.edges)
    text = "# Relationship map\n\n" + mermaid(nodes, edges) + "\n\n" + report(nodes, edges, args.focus) + "\n"
    if args.out:
        with open(args.out, "w") as fh:
            fh.write(text)
        print(f"wrote {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
