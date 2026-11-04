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

## It happened again

The next line ran, and the push failed: "access denied by the git proxy: OrMizrahi12/investor-os-vault is not in this session's authorized repository set" (my report, Nov. 4, 2026). The folder had no remote, so the session seems to have been tied to no repository. That cause is Claude's reading: the [environments docs, undated, retrieved Nov. 4, 2026](https://code.claude.com/docs/en/cloud-environments) tie the proxy's API access to a session's attached repositories, and the error text itself was not found in the docs. Claude had relied on one sentence saying a bundled session can push if the GitHub connection has access.

**What changed:** the folder now has a remote, and the line on [cloud.html](../cloud.html) forces the upload. It is still unproven, and says so.
