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
| `MOXFIELD_USERNAME` | Moxfield user whose public Commander decks are synced (`mirkwoodrunner`). |

Never commit secrets. Keep `.env` in `.gitignore`. Provide `.env.example` with placeholder values.

## Auth

Single user. One login page that checks `APP_PASSWORD` with `hmac.compare_digest`. Store a signed session flag. Every route except `/login` and `/healthz` requires login. Add a simple lockout after 10 failed attempts in 15 minutes (in-memory is fine).

## Data model

- `Deck` id, name, commander (text), moxfield_id (nullable, unique), moxfield_url (nullable), last_synced_at (nullable), in_rotation (bool, default true), decklist_text, created_at, updated_at
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

## Moxfield deck sync (critical feature)

This is the most important feature. If a later change could break the sync, say so before making it. Phase 0 findings and alternatives are in `docs/DECISIONS.md`.

Goal: keep every Commander deck in Chris's rotation in the app, fetched from Moxfield by the server, with no script to run and no login stored.

Rotation signal: **public visibility**. Moxfield folders are not visible without logging in, so the EDH folder cannot be read. Instead, Chris keeps rotation decks **public** and sets retired and league decks to **unlisted** or **private**. Every public Commander-format deck by `MOXFIELD_USERNAME` is in rotation.

Approach:
1. A "Sync decks" button on the Decks page. Sync runs on demand, never on a schedule.
2. The server fetches the user's public deck list from Moxfield and keeps the Commander-format decks. The exact endpoint is not yet known. It must be found from Render (see Rules) and recorded in `docs/DECISIONS.md`.
3. For each deck, the server fetches `GET https://api.moxfield.com/v2/decks/all/{publicId}`. This endpoint is proven by Chris's mtg-collection-tracker app, which still syncs from Render as of 2026-11-27.
4. Upsert decks by Moxfield public id, replace their card lists, re-run token lookup, and report added, updated and unchanged decks. A deck that is no longer in the public list gets `in_rotation = false` and is flagged for Chris to confirm. Never delete a deck automatically, because its game history must survive.
5. Fallback: add or refresh a single deck by pasting its Moxfield link. Pasted decklists still work if Moxfield is unreachable.

Rules:
- Moxfield has no official public API. These endpoints are undocumented and may change. Treat every response shape as untrusted and fail with a clear message if it changes.
- Only anonymous GET requests for public data. Never log in to Moxfield, never store Moxfield passwords, cookies or tokens.
- One request at a time, at least 1 second apart. Never parallelize. Send a plain `User-Agent: GameNightBag/0.1`.
- Cloudflare blocks Moxfield requests from the Claude Code cloud container (and likely other datacenter IPs) but allows Render. If any step would require getting around Cloudflare or bot protection, stop and ask Chris.
- Because Moxfield is unreachable from the dev container, tests use real responses captured from Render and saved under `tests/fixtures/moxfield/`. Network calls stay mocked in tests.
- All Moxfield code lives in `app/importers/moxfield.py`. No other file talks to Moxfield.
- Known deck JSON quirks (from mtg-collection-tracker): `mainboard`, `sideboard` and `commanders` are objects keyed by id, each entry `{quantity, card}`. `card.type` can be a numeric code, not text. Some entries have no `card`. The `tokens` field comes as an array, an object of flat cards, or an object of `{card}` entries, and can include non-token cards.
- A sync of N decks takes at least N seconds. Make sure the gunicorn timeout allows it (see Deployment).
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
- Start: `flask --app app db upgrade && gunicorn --timeout 180 "app:create_app()"`. The long timeout lets a full Moxfield sync finish in one request. Check whether Render's pre-deploy command works on the free tier. If it does, move the migration there.
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
