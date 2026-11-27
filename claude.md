# Game Night Bag

Personal web app for one user (Chris). Tracks which Commander decks are packed for game night, which tokens those decks need, and game results per deck.

## Stack

- Python 3.12, Flask, Jinja templates, small vanilla JS. No frontend framework.
- SQLAlchemy 2.x with Flask-Migrate (Alembic) for schema changes.
- Postgres on Neon in production (`DATABASE_URL`, pooled `-pooler` host, `sslmode=require`).
- SQLite file for local dev when `DATABASE_URL` is unset (`sqlite:///instance/local.db`). Do not use Postgres-only features. Use SQLAlchemy `JSON` columns, not `JSONB`.
- `psycopg[binary]` v3 driver. Normalize `postgres://` and `postgresql://` URLs to `postgresql+psycopg://`.
- gunicorn on Render free tier. Expect cold starts of 30 to 60 seconds.
- pytest for tests. Network calls are always mocked in tests.

## Environment variables

| Name | Purpose |
|---|---|
| `DATABASE_URL` | Neon pooled connection string. Unset locally to use SQLite. |
| `SECRET_KEY` | Flask session signing. Long random string. |
| `APP_PASSWORD` | The single login password. |
| `SCRYFALL_CONTACT` | Email used in the Scryfall User-Agent header. |
| `IMPORT_KEY` | Shared secret the Moxfield sync bookmarklet sends to the import endpoint. |

Never commit secrets. Keep `.env` in `.gitignore`. Provide `.env.example` with placeholder values.

## Auth

Single user. One login page that checks `APP_PASSWORD` with `hmac.compare_digest`. Store a signed session flag. Every route except `/login` and `/healthz` requires login. Add a simple lockout after 10 failed attempts in 15 minutes (in-memory is fine).

## Data model

- `Deck` id, name, commander (text), moxfield_id (nullable, unique), moxfield_url (nullable), last_synced_at (nullable), decklist_text, created_at, updated_at
- `DeckCard` id, deck_id, name, quantity, oracle_id (nullable until resolved), is_commander
- `Card` oracle_id (pk), name, type_line, related_tokens (JSON list of token oracle_ids), fetched_at. Cache of Scryfall lookups.
- `Token` oracle_id (pk), label (readable, like "1/1 white Soldier"), name, type_line, power, toughness, colors, oracle_text, image_url
- `DeckToken` deck_id, token_oracle_id, source_cards (JSON list of card names), manual (bool), hidden (bool)
- `BagSession` id, date, notes, is_active. Only one active session at a time.
- `BagDeck` session_id, deck_id
- `BagTokenPacked` session_id, token_oracle_id
- `Game` id, date, deck_id, session_id (nullable), result (win, loss, draw), pod_size, turn_count (nullable), winner_note, notes, created_at

## Scryfall rules

- Base URL `https://api.scryfall.com`. Send `User-Agent: GameNightBag/0.1 ({SCRYFALL_CONTACT})` and `Accept: application/json` on every request.
- Resolve deck cards with `POST /cards/collection`, at most 75 identifiers per request, and wait at least 100 ms between requests.
- Cache results in `Card` and `Token`. Only refetch a card older than 30 days.
- Token extraction comes from each card's `all_parts`. Include a part when `component == "token"`, or when its `type_line` contains "Emblem", or when it is a helper card such as The Monarch, The Initiative, The Ring, Day // Night, or a Dungeon. Verify these rules against real responses saved as test fixtures before relying on them. If a rule is wrong, fix it here and in DECISIONS.md.
- Group identical tokens by token `oracle_id`. Build the label from power/toughness, colors and name, and include short ability text when two tokens share a label.
- Users can add manual tokens and hide wrong ones per deck. A re-lookup never removes manual tokens or unhides hidden ones.

## Decklist parsing

Accept Moxfield plain text and MTGO export. Handle these:
- `1 Sol Ring`, `1x Sol Ring`
- Set and collector info, like `1 Sol Ring (CMM) 400 *F*`
- Split and double-faced names like `Fable of the Mirror-Breaker // Reflection of Kiki-Jiki`
- Section headers like `Commander`, `COMMANDER:`, `SIDEBOARD:`, and blank lines between sections. Cards under a commander header get `is_commander = true`.
- Report unresolved names to the user instead of dropping them silently.

## Moxfield folder sync (critical feature)

This is the most important feature. Feasibility is proven in phase 0 before other work. If a later change could break the sync, say so before making it.

Goal: pull every deck in Chris's private Moxfield folder "EDH" (folder id `4QVN9`, taken from the `selectedFolderId` in his personal decks URL) into the app, and keep it in sync.

Approach: a bookmarklet (or userscript) that Chris runs on moxfield.com while logged in.
1. Running in his browser, it reads the folder's deck list and each deck's cards using his existing Moxfield session, the same requests moxfield.com itself makes.
2. It POSTs the result to `POST /api/import/moxfield` on this app.
3. The app upserts decks by Moxfield public id, replaces their card lists, re-runs token lookup, and reports added, updated and unchanged decks. Decks removed from the folder are flagged for Chris to confirm, never deleted automatically.

Rules:
- Moxfield has no official public API. The requests the site makes are undocumented and may change. Discover them by inspecting moxfield.com network traffic in a logged-in browser, and document what you find in DECISIONS.md.
- The server never logs in to Moxfield, never calls Moxfield, and never stores Moxfield passwords, cookies or tokens.
- The import endpoint takes an `IMPORT_KEY` env var sent as a header. Allow CORS only from `https://moxfield.com` and `https://www.moxfield.com`, only on that endpoint.
- Keep Moxfield parsing in `app/importers/moxfield.py`. If the payload shape changes, fail with a clear message, and pasted decklists still work.
- Throttle requests in the bookmarklet (at least 500 ms between deck fetches).
- If any step would require getting around Cloudflare or bot protection, stop and ask Chris.
- Store each deck's Moxfield URL and `last_synced_at`.

## UI

- Phone-first. 44 px tap targets, 16 px inputs, works one-handed at a game table.
- Pages: Bag (active session, packed decks, token checklist grouped with the decks that need each token), Decks (list, add, edit, re-lookup tokens), Deck detail (cards, tokens, record), Games (log form, history, records per deck).
- Add a web app manifest so the site can be added to a phone home screen.

## Commands

```
pip install -r requirements.txt
flask --app app db upgrade
flask --app app run --debug
pytest
```

## Deployment (Render)

- `render.yaml` defines one free web service.
- Build: `pip install -r requirements.txt`
- Start: `flask --app app db upgrade && gunicorn "app:create_app()"`. Check whether Render's pre-deploy command works on the free tier. If it does, move the migration there.
- `/healthz` returns 200 without touching the database.

## Documentation rules

At the end of every task, before reporting done:
1. Update this CLAUDE.md if the stack, data model, commands, env vars or rules changed.
2. Add an entry to `docs/CHANGELOG.md` with the date and what changed.
3. Record any non-obvious choice in `docs/DECISIONS.md` with the reason and the alternatives considered.
4. Keep `README.md` setup and deploy steps accurate for a beginner-to-intermediate developer.
5. Run `pytest` and report the result.

## Working style

- Flag risks and unknowns before starting a phase.
- Keep solutions simple. Don't add features that weren't asked for.
- Give complete files or clear diffs with a short explanation of each change.
