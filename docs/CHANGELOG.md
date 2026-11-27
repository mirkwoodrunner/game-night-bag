# Changelog

## 2026-11-27

- Phase 0 feasibility. The server fetches public decks from Moxfield on Render. The EDH folder can't be read publicly, so the rotation is now every public Commander deck. See `docs/DECISIONS.md`.
- CLAUDE.md. Rewrote the Moxfield sync section for server-side fetching. Replaced `IMPORT_KEY` with `MOXFIELD_USERNAME`. Added `Deck.in_rotation`. Added a gunicorn `--timeout 180` to the start command.
- Phase 1a. App scaffold with `create_app()`, env-based config, SQLite fallback, Postgres URL normalizing, Flask-Migrate with an initial migration for the whole data model, password login with a 10-try lockout, `/healthz`, and a temporary login-only Moxfield probe page.
- Added `render.yaml`, `docs/DEPLOY.md`, `.env.example`, `.gitignore`, `requirements.txt` and a full README.
- `SCRYFALL_CONTACT` is now optional and defaults to the repo URL. No Scryfall account is needed.
- Gunicorn runs `--workers 1 --threads 4 --timeout 180`.
