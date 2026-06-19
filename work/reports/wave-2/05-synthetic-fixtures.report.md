# Report wave-2/05 — Synthetic Digital Twin Fixtures & Sample Data

## Result
DONE

## What I built
- `data/samples/twin_profiles.json` — 3 sample DigitalTwin profiles (conservative/moderate/aggressive archetypes)
- `data/samples/README.md` — documentation for fixture files
- `data/synthetic/sample_conversation.json` — 10-turn portfolio review conversation for Rahul Mehta

## Acceptance evidence (real output, this session)
```
$ python3 -c "
import json
profiles = json.load(open('data/samples/twin_profiles.json'))
assert len(profiles) == 3
for p in profiles:
    assert 'user_id' in p and 'name' in p and 'holdings' in p
conv = json.load(open('data/synthetic/sample_conversation.json'))
assert len(conv) == 10
print('fixtures OK')
"
fixtures OK
```

## Tests
- No unit tests (data-only task); validated via inline Python assertions

## Decisions / deviations
- Original nemotron-free dispatch timed out twice (idle timeout). Orchestrator completed the missing `sample_conversation.json` file directly.
- Conversation uses Indian financial context (STCG/LTCG tax rules, Nifty, INR values) matching the FinRoot domain.

## Surprises / gotchas
- nemotron-3-ultra-free model consistently times out on tasks requiring multiple file writes — not recommended for data-heavy tasks

## Follow-ups (for orchestrator triage — do NOT build now)
- Add more conversation fixtures for other profiles (Priya conservative, Ananya aggressive) in wave-6 eval tasks

## Self-check
- [x] Only touched Writes set (data/samples/, data/synthetic/)
- [x] No fabricated data that affects agent logic (FM-11 n/a — fixtures are test data)
- [x] No bare excepts / silent fallbacks
- [x] All 3 fixture files present and valid JSON
- [x] No secrets committed (FM-07)
