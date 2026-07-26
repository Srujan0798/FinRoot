# HANDOFF — Current State

> Replaced 2026-07-26T06:12Z — hostile stranger-verification loop, round 5 (this session).

## Snapshot
- **Honest blended score:** **~97-98%** — **not 100%, not frozen**
- **FRB @ `30e2ed9`:** mean **0.9114** · pass@1 **1.0000** · lift **+168.85%** vs RAG
- **Evidence:** `docs/SCOREBOARD.md` §E-F (full list of 21 bugs found + fixed this session, plus 2 clean-audit confirmations)
- **Plan:** `work/ETERNAL_FINAL_PLAN.md` · **Scoreboard:** `docs/SCOREBOARD.md`

## Round 5 additions
1. **Audit-trail tail-truncation now detected** — an already-documented known gap (test had
   a TODO) was actually fixed rather than left: `verify_chain_detailed()` now compares the
   highest seq seen on disk against the in-process instance's own tracked `_last_seq`,
   catching deletion of the LAST event(s), the one tamper scenario that wasn't caught.
   Field-edits, mid-chain deletion, and partial-hash-patch-without-cascade were all already
   correctly detected (re-verified adversarially, not just structurally).
2. **`WorkingMemory` confirmed dead code in the live path** — implemented and unit-tested,
   but `add_turn()` is never called from `orchestrator.py`/`workflows/`/`interface/`;
   `answer()` builds a fresh empty `MemoryManager` every call with no session-ID concept in
   the API. Confirmed live: a coherent follow-up question got a totally unrelated generic
   response. `docs/SUBMISSION.md:15` overclaimed "retains context across turns" — corrected;
   tracked as a real architectural item in BACKLOG.md (not attempted as a rushed fix).

## Round 4 additions (on top of rounds 1-3)
1. **Truncated golden-path chip labels** (`chat.py:132`) had no accessible fallback — added
   `help=chip` tooltip. Rest of accessibility audit clean (contrast, headings, keyboard nav,
   mobile viewport).
2. **Self-Critic and prompt-injection resistance independently verified, not assumed** — the
   critic correctly failed 2 freshly-constructed bad recommendations (0.285, 0.47, both
   below threshold with correct diagnostics); 4 injection-style queries produced zero
   compliance (no leakage, no forced confidence, no dropped disclaimers). One cosmetic-only
   artifact (all-caps injection words misparsed as ticker candidates) fixed via denylist
   even though confirmed harmless.

## Trajectory
| Stage | % | pass@1 |
|---|---:|---:|
| Audit | 68 | 0.46 |
| Phase 1 GP | 83 | — |
| Domain FRB | 91 | 0.63 |
| Conf soft + tax HIGH | ~94.5 | 0.87 |
| Tax residual | ~95.5 | 1.00 |
| Mean + judge dry-run | ~96 | 1.00 |
| Hostile stranger-verify round 1 | ~97-98 | 1.00 |
| Round 2 — remaining GP paraphrase + deps | ~97-98 | 1.00 |
| **Now (round 3 — remaining FRB domains + dead-code fix)** | **~97-98** | **1.00** |

## This loop — genuine hostile/cold verification, not trusting prior reports
Ran real `git clone` + fresh venv (**4 independent times across 3 rounds**) and followed the
documented judge path verbatim, rather than trusting any prior "100%"/"96% done" self-report.
Found and fixed **18 real bugs** a stranger/judge would have hit — full list in
`docs/SCOREBOARD.md` §E-F. Round 3 additions:
1. **Structural bug**: `detect_domain()`'s GENERAL-intent fallback returned
   `_INTENT_TO_DOMAIN[Intent.GENERAL]` before the broader `_DOMAIN_KEYWORDS` sweep ever ran —
   that entire keyword dict was permanently dead code for any GENERAL-intent query, affecting
   even the baseline scripted cashflow gold question, not just a paraphrase. Reordered.
2. **4 more FRB domains brittle under paraphrase** (of 7 stress-tested; credit + insurance
   held up robust): **estate_planning** (worst break found — a paraphrase using "provident
   fund"/"nominee" instead of "epf"/"nomination" returned a completely generic greeting,
   zero engagement with the actual question), **international** (spelled-out "Liberalised
   Remittance Scheme"/"American equities" misrouted to `tax`), **behavioral** ("ride the
   trend"/"shifting my entire" misrouted to `risk`), **general/portfolio** ("how should I
   split my investments" misrouted to generic `risk` boilerplate). All fixed with targeted
   keyword additions; all originals + paraphrases re-verified; full suite green.
3. **Undocumented API cold-start**: first request after boot measured ~3x slower than
   steady-state (0.96s vs 0.32s), not documented anywhere a judge would see it before
   testing. Added a one-line note to JUDGE_QUICKSTART.md.

**Architectural note carried forward**: the keyword-override domain-routing architecture is
structurally paraphrase-fragile by design — every fix across rounds 1-3 has been reactive
(found via stress-testing), not preventive. A durable fix needs semantic domain
classification (e.g. embedding-similarity against domain exemplars), which is a real
follow-up worth a dedicated wave, not something this session is pretending is fully closed.

Round 1 (9 fixes) + round 2 (GP-1/GP-2 paraphrase + dependency CVE disclosure) — see
`docs/SCOREBOARD.md` §E-F or prior HANDOFF revisions in git history for full detail.

## Prove green
```bash
make smoke
bash scripts/judge_dry_run.sh
PYTHONPATH=src python3 scripts/run_evals.py --mock --k 1
# expect pass@1=1.0000 mean≈0.9114
docker-compose up -d && sleep 30 && docker-compose ps   # expect (healthy)
docker-compose down
```
All of the above were re-verified on **6 independent fresh `git clone`s**, not just the local
working tree, after every fix landed — most recently confirmed at HEAD `dc92f07` before the
final housekeeping regen to `30e2ed9`.

## Still open for freeze
1. **Human freeze bet** — the one thing this session cannot self-certify. Everything
   mechanical (clean commit, true cold-clone ×4, docker, security review + honest CVE
   disclosure, CI) is done.
2. **Dependency version-ceiling upgrade** (see docs/SCOREBOARD.md §F) — real, disclosed,
   deliberately deferred rather than rushed. Needs a dedicated wave with full regression.
3. **Domain-routing architecture** (see above / HALL_OF_SHAME Pattern 11) — keyword-override
   is inherently paraphrase-fragile; every round finds more breaks. A semantic-classification
   rewrite is the durable fix, flagged not hidden.
4. Continued hostile-audit surface may still exist — every audit pass dispatched this session
   found something real (3 rounds, ~12 subagents); there is no guarantee the surface is now
   exhausted, only that everything found so far is fixed, disclosed, or explicitly deferred
   with reasoning.

**Do not claim submission 100% — that requires the human freeze bet.**
