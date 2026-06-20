---
name: next
description: Decide and start the next best action given current state.
allowed-tools: Read Grep Glob
invocation: both
---

# /next

Steps:
1. Run the `/status` logic.
2. Pick the next action by priority:
   reviews pending → `/review`; wave fully merged → `/ship`; wave shipped → `/plan` next wave;
   wave planned → `/dispatch`; nothing in flight → `/plan` the active wave.
3. State the choice and why in one line, then begin it.
