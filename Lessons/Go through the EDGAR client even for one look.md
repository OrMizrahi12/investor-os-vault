---
ticker: GLW
status: no buy
sector: Information Technology
base value: not defined yet
last checked: "2026-11-03"
sources: []
---

# Go through the EDGAR client even for one look

*Written 2026-11-03.*

## What happened

Claude caught this during the alert test. To see a Form 25, Claude sent one plain `curl` to sec.gov with a made-up client name. `sensors/README.md` says all SEC requests go through the EDGAR client, which declares the contact address and keeps to the rate. The output was thrown away and nothing used it. Claude then read the form through the client.

## What it taught us

A quick look is still a request. The client is a few lines to call, so there is no shortcut worth taking.

## What changed

No rule or code. Nothing in `Rules/alerts.md` or `alerts.html` rests on that request.
