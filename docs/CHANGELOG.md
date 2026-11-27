# Changelog

## 2026-11-27

- Phase 0 feasibility. The server fetches public decks from Moxfield on Render. The EDH folder can't be read publicly, so the rotation is now every public Commander deck. See `docs/DECISIONS.md`.
- CLAUDE.md. Rewrote the Moxfield sync section for server-side fetching. Replaced `IMPORT_KEY` with `MOXFIELD_USERNAME`. Added `Deck.in_rotation`. Added a gunicorn `--timeout 180` to the start command.
