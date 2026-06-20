# Report wave-8/04 — 7-Minute Demo Script + Demo Capture Tool

## Result
DONE

## What I built
- `docs/business/7_minute_demo_script.md` — timed beats (0:00–7:00) with click-by-click narration, fallback notes per beat, and quick-reference table mapping to scoring axes.
- `scripts/capture_demo.py` — runs `interface.core.answer()` on 4 showcase queries (portfolio, tax with number, news_impact, trap question) in Mock mode, writes formatted markdown transcripts to `docs/demo/transcript_*.md`.

## Acceptance evidence (real output, this session)
```
$ PYTHONPATH=src python3 scripts/capture_demo.py
[1/4] Running answer() for: 'What is my current portfolio allocation and risk level?' ...
  -> docs/demo/transcript_1_portfolio.md
[2/4] Running answer() for: 'How much tax will I owe if I sell my equity holdings this year?' ...
  -> docs/demo/transcript_2_tax_with_number.md
[3/4] Running answer() for: 'What is the impact of recent RBI policy changes on my debt fund holdings?' ...
  -> docs/demo/transcript_3_news_impact.md
[4/4] Running answer() for: 'I want to put my entire emergency fund into a high-growth small-cap stock.' ...
  -> docs/demo/transcript_4_trap_question.md

Done. 4 transcript(s) written:
  docs/demo/transcript_1_portfolio.md
  docs/demo/transcript_2_tax_with_number.md
  docs/demo/transcript_3_news_impact.md
  docs/demo/transcript_4_trap_question.md

$ ls docs/demo/transcript_*.md
docs/demo/transcript_1_portfolio.md
docs/demo/transcript_2_tax_with_number.md
docs/demo/transcript_3_news_impact.md
docs/demo/transcript_4_trap_question.md

$ test -f docs/business/7_minute_demo_script.md && grep -qE "[0-9]:[0-9][0-9]" docs/business/7_minute_demo_script.md && echo "timed script present"
timed script present
```

## Tests
- No dedicated test file added (scripts are not in `tests/` convention; acceptance commands serve as verification).
- `ruff check` passes on both files.

## Decisions / deviations
- Added both `_ROOT` and `_SRC` to `sys.path` in `capture_demo.py` (mirics `smoke_test.py` pattern) because `interface.core` imports `config` from the project root.
- The trap question transcript (transcript_4) correctly shows `Compliant: False` and `Confidence: LOW` with the prudence verifier flagging "Emergency fund first" — confirms the verifier works as demo script describes.
- Each beat in the demo script includes a "Reliability note" with a specific fallback action per the task requirement.

## Surprises / gotchas
- None. No gotchas file needed.

## Follow-ups (for orchestrator triage — do NOT build now)
- Consider adding a `--user-id` CLI arg to `capture_demo.py` to support different twin profiles.
- The transcript tables could be truncated for very long tool outputs (currently capped at 120 chars in trace, full in citations).

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13)
- [x] No fabricated numbers; tool outputs cited (FM-11)
- [x] No bare excepts / silent fallbacks
- [x] ruff clean, tests green (output above)
- [x] No secrets committed (FM-07)
