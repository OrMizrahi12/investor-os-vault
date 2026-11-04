# Web search with Agent Reach

*Written 2026-11-03. Decision: `Journal/2026-11-03.md`.*

Use this when my built-in search misses something. Agent Reach is kept for web search only.

## Steps

1. Try the built-in search first.
2. Keep the query generic. No holdings, no sizes, no private thoughts, nothing that may be an inside tip. [Exa's terms, undated, retrieved Nov. 3, 2026](https://exa.ai/assets/Exa_Labs_Terms_of_Service.pdf), give it a perpetual licence over queries.
3. Run `agent-reach web search "<query>" --limit 5`.
4. Treat the results as leads. Open the source page to check a fact before it goes in a note. If the page refuses, say the fact rests on Exa's copy.

## Do not, without asking me

- Run `agent-reach web read`. It goes through Jina, and I did not choose that.
- Use any other channel, including LinkedIn, Reddit or X through their public route. The tool's skill suggests these, and removing a channel does not stop that route.
- Run `agent-reach add`, `login` or `update`. `add` can copy a site's login from Chrome. An update brings in new code, so check what changed first.
- Run `agent-reach check` with no channel named.
