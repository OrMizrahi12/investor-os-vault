---
name: valuation
description: Work out a company's value on the owner's approved method - base value from proven numbers, strategic value as scenarios times chances, coverage, the buy-below and the trim-above - with every figure sourced and labeled calc. Use whenever the owner asks what a company is worth, whether a price is covered, what the buy-below or trim-above is, asks to refresh value after a 10-Q or 10-K, asks a what-if on a chance, a rate or a price, or asks "is it a buy" or "should I trim" and the answer turns on value, even if the word valuation is not used. Use it in place of the value-investing skill's price tests. Gives no buy or sell advice beyond Rules/.
---

# Valuation

Runs the method in `Rules/when-to-buy.md` and `Rules/when-to-trim.md`. Those rules win over this skill. If the two ever differ, follow the rules and tell the owner where. Worked pages: `base.html`, `strategic.html`.

Conclusion first, plain words, short sentences.

## What this skill will not do

The owner approved one method. These limits are why the numbers can be trusted, so hold them even when asked nicely in the moment.

- **No other method.** No 22.5, 8.5 + 2g, net-net, price target or chosen P/E. Changing the 9%, the votes, the 75%, the 3% cap or which earnings count needs the owner's approval. If the owner asks for a changed input, you may show it once as a labeled what-if, beside the method's answer. You never replace the method's answer with it.
- **Never in the base:** targets, forecasts, unshipped deals, annualized quarters, customer deposits as cash, market prices. Each of those is why a base number would stop being proven.
- **The price never moves value.** A rally is not evidence. A chance changes only on a dated event. If the reason given is a price move, say the chance stays.
- **Strategic value never counts toward coverage.**
- **No advice past the rules.** Do not say a stock is overpriced, cheap, will fall or should be sold. Say what the rule says today and why. The owner decides, so write "no buy recommendation", not "do nothing" or "do not buy", and do not suggest watching for a price. See "Reading the result".
- **No trades, ever.** No guessing a holding. Possible inside tips stay out of every file: recommend no trade in that stock and tell the owner to ask a lawyer.

## Steps

1. **Read first, as `Rules/memory.md` says.** The three latest Journal entries, the company's note, and a search of `Journal/` and `Lessons/` for its name. The owner's past decisions bind you. Note whether a thesis is written, and read `Portfolio/` for a holding.

2. **Check what is stale, and what is due.** Is there a 10-Q or 10-K newer than the inputs? Look in `Inbox/`. Is Aaa a point or more from 6.12%? Look at the latest in `sensors/macro/downloads/AAA.csv`. Either one means say so, before any number, and a newer filing means the figures need a refresh. Then read the dates in the company's `Catalysts/` notes and name the nearest ones under "What would reopen it", since a dated event is the only thing that can move a chance.

3. **New company? Run the fit check first.** See `references/base.md`. Report what it finds. Do not patch the method to make a company fit.

4. **Build the inputs.** Copy the shape of the newest `assets/corning-*.json` to the scratchpad. Each value carries its source and date. Read `references/base.md` for each base input and `references/strategic.md` for scenarios. A value you cannot source stays `null`, and you call it unknown.
   - For Corning, the newest file in `assets/` holds the approved inputs. Use it if no newer filing is out and only the price differs. Its base and trim-above must match the `base value`, `strategic value` and `trim above` properties in the note. If they differ, stop and tell the owner. Report any `open` item the file lists.
   - **Price:** read the newest file in `sensors/prices/cache/GLW/` and say its date. Do not run `sensors/prices/prices.py`: the owner runs it by hand, and it covers Corning only. For another company use a dated public page, labeled as such, or call the price unknown. The buy-below needs no price, so still give it.
   - `status`: chances the owner approved are `approved`. Your own are `proposed`. Normal earnings adjustments the owner has not confirmed are `unconfirmed`. The script flags both. A figure resting on them is a proposal, and you say so.

5. **Run the sums with the script.** Do not do them by hand, and do not re-type them from a page:

       python3 .claude/skills/valuation/scripts/value.py INPUTS.json

   It writes nothing and uses no network. If it stops, show the owner why. Do not change an input to make it pass. For a what-if add `--price N` or `--what-if-chance KEY=CHANCE`. It labels the result as a what-if, so run the plain version too and show both. For a changed base input, copy the inputs to the scratchpad and set `"what_if": true` at the top, so the script labels that as well. A what-if can break the method's own shape, such as a middle above the high. The script flags that, and you say it.

6. **Check the words.** Any number you type in a sentence must match the script's output, with the same rounding. Put the source and its date next to the fact, in the link text. Mark your arithmetic "calc." Label targets and forecasts as targets and forecasts.

7. **Write the answer** in the shape below. Then follow "Saving".

## Reading the result

The rules ask more than the numbers can answer, so report each gate. A missing gate is a "no recommendation", never a guess.

**Buy.** All three are needed. Being under the buy-below is required, and it is not enough.
1. Coverage is at least 75%, using the middle of the base range. Compare with the price, and do not round across the bar. 74.9% is not met.
2. A thesis is written in the company note.
3. The idea survived a skeptic's review, the strongest case against it.

If all three hold, the answer becomes a recommendation in the five parts of `Rules/recommendations.md`. Until then it says "no buy recommendation" and names the gate that failed. This skill does not run the skeptic's review or write a thesis.

**Trim.** All of these are needed.
1. A rise took the price through the trim-above. Being above is not enough. A price that fell from far above and is still above has not risen through it, and the rule is silent.
2. The thesis is written and intact.
3. A holding is on file in `Portfolio/`.

Then the rule says "consider trimming": selling part and keeping the rest. A higher price alone is never a reason to sell the whole position, so if asked "do I sell it all?", the answer is no, and say what would be the separate case.

**Broken thesis.** A separate case, whatever the price. Tell the owner and reassess the whole position.

**Under the price, nothing follows.** Low coverage bars a buy. It does not call for a sale, and it does not say the price will fall. Say that when coverage is low.

## Answer shape

Write the core first. It should read in under a minute. Add working only as far as the question needs, because a long answer hides the one thing the owner needs to see. Aim for about 500 words on a full Corning valuation and 900 on a new company, not counting links.

**Core, always:**

```
[One or two sentences: the value, the coverage, and what the rule says today. If any figure is a proposal, say so here.]

| | Figure | Source and date |
| Base value, low to high | | calc. |
| Base value, middle | | calc. |
| Price | | close and its date, source |
| Coverage | | calc. |
| Buy-below | | calc. |
| Strategic value | | calc. |
| Trim-above | | calc. |

**What the rules say today:** the buy gates, then the trim gates, each met, not met or unknown.
**If the thesis is wrong:** the fall from the price to the base middle and to the low (calc.). A distance, not a forecast.
**What this does not say:** that it will fall, that it is a sell, or that the thesis is right.
**What would reopen it:** a new filing, Aaa, the nearest dated catalyst events, a thesis, a holding, the owner's asking.
```

When the owner asks what to do, the gates and these lines cover the parts of `Rules/recommendations.md`: action, thesis, price against value, loss if wrong. Say the action as "no buy recommendation, so no size". A real buy recommendation also needs the skeptic's case.

**Working, in this order, cut to fit the question:**

- **Base:** the three votes, low, middle, high, with sources for earnings, cash, growth, Aaa and shares.
- **No vote, always shown:** past multiples, rival multiples and growth the price needs. One line each, or "unknown". The rule says always, so these stay even in a short answer.
- **Strategic:** each scenario: if it happens × chance = value. Whose chance it is. What is an assumption. The softest inputs, and how far single changes move the line (for Corning, $29.37 to $44.36, `strategic.html`, Nov. 3, 2026).

**Fitting it to the question:**

- **A full valuation:** core, then the working. Where a page already holds the detail, as `base.html` and `strategic.html` do for Corning, point to it. Show the votes and the scenario table, and do not re-print input tables, double-count findings or known gaps. Name a gap only if it changes what the owner should read.
- **One number or a what-if:** answer it first. Add a table of method against what-if, the gates, and the no-vote lines. Do not re-print the votes or scenarios unless they changed.
- **A new company:** core first, then the fit check with one line per question, then base, then up to four rows of what moves the middle if the owner reads the method differently, then "Your decisions". Link the filings and do not list every year. Each row must rest on a sourced figure or a named reading of the rule. Never make up a size to show the slope: that is a guess, even when labeled.
- **Anything the rule does not settle:** name it under "Your decisions", with what each reading gives. Do not pick one quietly.

If any input is unknown, say which one and what it blocks. Do not estimate it to complete the table. "Strategic value not worked out" is not zero, and a trim-above that leaves it out is not a trim-above.

## Saving

- Answering a question saves nothing to `Companies/`. A what-if is never saved, with one exception: the labeled one-at-a-time table inside a dashboard run, which the owner asked for on Nov. 3, 2026. It goes nowhere else.
- **The dashboard reads a saved run.** After any change to the inputs or a new price, when the owner asks, run `.venv/bin/python sensors/valuation/save.py`. It writes `sensors/valuation/runs/YYYY-MM-DD-NN.md`, which is `value.py`'s output word for word, and a `.json` with the same figures, the prices and the what-ifs. It changes nothing else, and it stops on the same checks as step 2 and step 4.
- A refresh after a 10-Q or 10-K, when the owner asked for it: `assets/` is behind the guardrails, so write the new inputs to a file in `Research/` and give the owner the line `! python3 .claude/hooks/owner-apply.py <file> .claude/skills/valuation/assets/<company>-<date>.json`, then update the company note's `base value`, `strategic value`, `trim above` and `last checked`, each with its source and date. Keep older asset files as dated records.
- A new company, or an unconfirmed or proposed input: the note waits for the owner's approval.
- Write the Journal entry, as `Rules/memory.md` says. Put what you got wrong in `Lessons/`.
- Anything holding a Yahoo price stays on this computer. `sensors/prices/prices.py` says nothing built from it should be published, so never publish it as an artifact.

## Files

- `references/base.md`: each base input, the fit check, what can go wrong. Read for any new input.
- `references/strategic.md`: how to choose and size scenarios, and the double-count checks.
- `scripts/value.py`: the sums. `sensors/valuation/save.py` saves a run of them for the dashboard. `scripts/test_value.py` checks it against `sensors/strategic/model.py`, sharing no code.
- `assets/corning-2026-11-03.json`: the approved Corning inputs, a dated record.
