# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

All four build stages in `PROMPTS.md` (skeleton → features → UI → Playwright review) are done, and the bugs from the review are fixed and re-verified. The code is committed on `main` (git initialized locally, no remote yet). Next step: push to GitHub and deploy to Streamlit Community Cloud. `gh` CLI is not installed, so the user creates the GitHub repo and does the Streamlit Cloud setup in the browser.

`PRD.md` is the source of truth. Its feature IDs `F-01`…`F-12` are used to track implementation and test results. When reviewing, report bugs first and fix them only after the user approves.

## What it is

A Streamlit web app that translates user-entered text into English / Japanese / Russian (`en`, `ja`, `ru`) via the OpenAI API (default model `gpt-6-astra`). The UI and all user-facing messages are in Korean.

## Commands

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
# headless, for Playwright testing:
streamlit run app.py --server.headless true --server.port 8501
```

There is no test suite or linter. Verification options:
- Playwright against the running app.
- `streamlit.testing.v1.AppTest` for quick headless checks of `app.py`. Pass an absolute path to `AppTest.from_file`, because relative paths resolve against the calling script. It makes real API calls.
- Error paths: start extra instances with `OPENAI_API_KEY=` (no key) or `OPENAI_MODEL=<bogus>` (bad model) on other ports. `load_dotenv()` does not override variables that are already set.

## Architecture

- `app.py` holds the Streamlit UI only; `translator.py` holds the OpenAI call logic only. Keep this separation.
- **Config:** `get_config()` reads `st.secrets` first (Streamlit Cloud), then `.env` / env vars (local). Empty values fall back to defaults. `OPENAI_MODEL` must stay configurable.
- **One API call per translation:** all selected languages are requested together in JSON response mode, returning `{"source_language": "<Korean language name>", "translations": {code: text}}`. The call retries once if the JSON fails to parse. Timeout is 60s and `max_retries=1`.
- **Errors:** `translator.py` raises `TranslationError(kind)`, and `app.py` maps `kind` to Korean messages in `ERROR_MESSAGES`. Add any new failure mode in both files.
- **State:** the last result is kept in `st.session_state.current` so it survives reruns, such as the one a download-button click triggers. History (max 10) is in `st.session_state.history`. An entry identical to the most recent one (same text, tone, and translations) is not added again.
- **Caching:** `cached_translate` uses `st.cache_data` keyed on (text, targets tuple, tone).

## Gotchas

- Don't use `st.text_area(max_chars=...)`: it silently rejects an over-limit paste, with no warning. The 5,000-char counter and warning are custom-built. The counter updates only when the text area commits (on blur or button click).
- Don't use flag emoji in labels: Windows renders them as "US/JP/RU". Labels come from `language_label()`, e.g. `영어 · EN`.
- `st.code` results are switched to the body font via CSS in `st.html`. The default monospace font spaces Japanese full-width punctuation oddly. The same CSS shrinks the `h1` on mobile.
- On Streamlit 1.64, use `width="stretch"`, not the deprecated `use_container_width`.
- In Playwright MCP, clicking the download button closes the tab. Verify download content with `AppTest` / `build_download_text` instead. Screenshots can only be saved under the project directory (`.playwright-mcp/`, git-ignored).

## Deployment

Target is Streamlit Community Cloud: branch `main`, main file `app.py`, Python 3.12 (the code needs 3.10+). Secrets go in the app's Secrets settings as TOML, not in `.env`. `.env` and `.streamlit/secrets.toml` must stay git-ignored. `.streamlit/config.toml` (the theme, with `[theme.light]`/`[theme.dark]`) is committed.
