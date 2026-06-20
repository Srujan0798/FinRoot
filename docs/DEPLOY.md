# Deploy FinRoot to Streamlit Community Cloud

FinRoot runs in **mock mode** by default — zero API keys required. Deploy to a public URL in 3 steps.

## One-click deploy

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/)

## Steps

1. **Push to GitHub**
   ```bash
   git push origin main
   ```

2. **Go to share.streamlit.io**  
   Open https://share.streamlit.io in your browser. Sign in with GitHub.

3. **Deploy**  
   Click **"New app"** → select your FinRoot repo → set **Main file path** to `streamlit_app.py` → click **Deploy**.

Streamlit Cloud auto-detects `requirements.txt` and installs all dependencies. The app starts in headless mode with the dark theme via `.streamlit/config.toml`.

## Environment variables (optional)

All optional — mock mode needs nothing:

| Variable | Default | Purpose |
|---|---|---|
| `FINROOT_LLM_PROVIDER` | `mock` | `mock`, `ollama`, `groq`, `openai` |
| `FINROOT_OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server |
| `FINROOT_OLLAMA_MODEL` | `llama3.1:8b` | Ollama model |
| `FINROOT_GROQ_API_KEY` | — | Groq API key |
| `FINROOT_OPENAI_API_KEY` | — | OpenAI API key |

To use a live LLM, set the corresponding secret in Streamlit Cloud's **Settings → Secrets**.
