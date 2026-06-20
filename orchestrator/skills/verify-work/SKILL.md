---
name: verify-work
description: Use before claiming anything is done/passing — run the verification commands and confirm output first.
allowed-tools: Read Bash Grep Glob
invocation: both
subagent: false
metadata:
  author: finroot
  version: "1.0.0"
---

# Verify Work

When to use: about to say "done", "fixed", "passing", or before /merge or /ship.

Process:
1. Identify the exact acceptance commands for the claim.
2. Run them this session. Capture output.
3. Only claim success if the output proves it. If partial, say "partly" — never round up (FM-09).
4. For finance outputs, additionally verify: numbers cited, confidence labeled, no fabricated data.

Evidence before assertions. Always.
