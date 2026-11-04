# Relationship mapping and the investigation room

## Contents
1. Why map relationships
2. What goes on the map (professional information only)
3. Building the map step by step
4. Link types and coding
5. Using the map
6. The script
7. The investigation room
8. Tips and cautions

---

## 1. Why map relationships

Filings show an organization chart; reality is a web of relationships: who knows whom, who worked together before, who trusts or resents whom, who buys from whom. Drawing that web on one display (a) gives helpers a shared picture they can discuss and update, and (b) often produces sudden insight when separate facts connect. It is the investor's version of the link charts analysts use to understand any complex organization.

A partial map of the main players is enough for most purposes. A comprehensive one is worth building when you are investigating a specific pending event (a takeover, a large contract, a restructuring).

## 2. What goes on the map (professional information only)

Include: names (when public), roles, organizations, tenure, education, prior employers and roles, board seats, deal histories, professional associations, public statements, stock ownership, professional reputation (others' opinions of their work), declared ambitions, and how they are connected.

Exclude: home addresses, family members, children's schools, health, relationships, private habits, and anything obtained by covert observation. These add privacy harm and legal risk while rarely adding investment value; professional links answer the useful questions.

## 3. Building the map step by step

1. **Center:** the company.
2. **Inner ring:** key people inside: executives, key designers and engineers, top salespeople, directors, and large holders with a say in strategy. For each: age range, education, career, shares owned, function, a public photo if helpful for recognition at events.
3. **Gathering places:** where the company's people meet professionally (industry associations, conferences, user groups, the clubs or venues that appear in public company materials). Keep it to professional settings.
4. **Customers:** the major customer organizations (and distributors), with the individuals who evaluate, use and pay. This is "following the money" and usually the hardest, most valuable part.
5. **Links company ↔ customers:** shared employers, schools, professional bodies, past deals.
6. **Suppliers, bankers, auditors, lawyers, advisers** with their links.
7. **Competitors** in the margins: their key people, suppliers and advisers.
8. **Sticky notes** for each link to verify.

Do not overdo social links: people act mainly on business needs, and staff move on. Senior people tend to stay; learn them well.

## 4. Link types and coding

Use colors or line styles (or the `type` column in the CSV):

| Link type | Weak form | Strong form |
|---|---|---|
| Education | Same school | Same school and same years / same program |
| Prior employer | Same company | Same department at the same time |
| Boards and associations | Same association | Served on the same board |
| Deals | Same industry deals | Worked on the same transaction |
| Commercial | Buys from / sells to | Primary decision maker on the account |
| Opinion | Third-party view of the person | Several consistent views |

## 5. Using the map

- **Who might acquire the company?** Some deals start as bankers' ideas, but most happen between companies whose people already know each other, and those deals go more smoothly. Scan the prior-employer and deal links between the target's people and people at plausible buyers; then look for confirming evidence (public appearances together, corporate-development activity, adviser engagements).
- **Is a competitive threat building?** Example: a company's key customers' buyers share a professional background and a hobby community with the company's head of sales, while a struggling rival's salespeople do not fit in. The rival then hires a new head of sales from the same background and community. The risk of customer defections just rose, before the market sees it. Confirm by asking customers casually what they think of the new person: enthusiasm is a reason to dig further or to trim.
- **Who are the hubs?** People with links to many parts of the map are good sources to approach (legitimately) and key-person risks.
- **Where are the blind spots?** Important roles with no known links show where research is thin.
- **Preparing calls:** knowing a contact's professional background lets you talk about what matters to them.

## 6. The script

`python3 scripts/relationship_map.py nodes.csv edges.csv [--out map.md] [--focus "Company A"]`

- `nodes.csv` columns: `id,name,org,role,group` (group: company, customer, supplier, adviser, competitor, other).
- `edges.csv` columns: `source,target,type,detail,strength` (strength: 1 weak, 2 strong).
- Output: a Mermaid diagram, a hub ranking, cross-organization links, shared-history links between the company and competitors or other companies (acquirer and threat leads), and nodes with no links.
- Examples: `assets/map_nodes_example.csv`, `assets/map_edges_example.csv`.

## 7. The investigation room

When a project grows (a big, uncertain event; a large potential position), dedicate a lockable room or a private digital workspace: the map, the production flow map, photos of sites and of public vantage points, clippings, a whiteboard of open questions and a task list. Everyone making calls should see it. The aim resembles a team anticipating a planned event rather than reconstructing a past one.

## 8. Tips and cautions

1. Treat analysis as an investigation of a future event, not as bookkeeping: learn everything relevant about the actors, their motives and skills.
2. Build the room only for promising stocks where a future event is genuinely in doubt; it is time-consuming and pulls attention from other holdings. Start with partial maps until experienced.
3. Record past employers, education, affiliations, community roles, declared ambitions and, often most useful, other people's professional opinions of each participant.
4. With enough detail, the story starts to feel alive and hunches appear: follow them up with evidence. If instead a strong sense of "no deal here" appears, disengage.
5. Keep the map confidential and secure; log who changed what and when. Respect privacy: discretion earns more trust and more information over time.
