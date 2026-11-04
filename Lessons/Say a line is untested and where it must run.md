---
ticker:
status:
sector:
last checked: "2026-11-04"
sources: []
---

# Say a line is untested and where it must run

*Written 2026-11-04.*

## What happened

I caught this by typing it. Claude gave me a line starting with `!`, for this session's prompt, to send this folder to a cloud session. It failed with: "--cloud requires an interactive terminal." The `!` prefix runs a command with no terminal attached. The session's own guidance suggests `!` for commands I run myself, and Claude applied that here without checking this command. The cloud docs Claude read did not say this. Nothing was sent, and no file changed.

## What it taught us

A command that opens its own screen cannot run through `!`. When Claude hands me a line it cannot try first, it says so at the point of handing it over, and says where to type it.

## What changed

The line on [cloud.html](../cloud.html) now goes in a separate terminal, with a `cd` first and no `!`. No rule changed.
