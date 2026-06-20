# Wave 9 Polish — Gotchas

## 01 — UI Screenshots

1. **`[data-testid="stChatInput"]` is a `<div>`, not `<input>`/`<textarea>`.**  
   Playwright's `.fill()` requires a text-input element. The actual input is
   `[data-testid="stChatInput"] textarea` — must use the child selector.

2. **Streamlit page HTML is JS-rendered.**  
   `urllib.request.urlopen()` returns only the static shell. Full DOM inspection
   requires Playwright (or another headless browser).

3. **Tab labels contain emoji prefixes.**  
   `page.get_by_role("tab").filter(has_text="Chat")` matches successfully because
   `has_text` does substring matching on the element's text ("💬 Chat").
