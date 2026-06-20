# Rule — TypeScript / Frontend (applies only if a JS/TS UI is added)

> FinRoot's default UI is Streamlit (Python). This rule applies only if a TS frontend is added later
> (currently OUT of scope — see SCOPE_GUARD). Kept for completeness.

- Strict TypeScript (`strict: true`). No `any` without a written reason.
- Zod (or equivalent) at API boundaries, mirroring the Pydantic contracts.
- ESLint + Prettier; CI-enforced. Components small and typed.
- Never duplicate financial logic on the client — it lives in the Python core; the UI only renders.
