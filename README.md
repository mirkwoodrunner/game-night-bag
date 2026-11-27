# Game Night Bag

A personal Flask app for one user. It tracks which Commander decks are packed for game night, which tokens they need, and game results per deck. Decks come from Moxfield. See `CLAUDE.md` for the full spec.

## Status

Phase 1a. Login, `/healthz`, the database schema and a temporary Moxfield probe page. Deck pages, the bag and game logging come later.

## Run it locally

You need Python 3.12 or newer.

```
python -m venv .venv
. .venv/bin/activate            # on Windows use .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then set APP_PASSWORD in .env
flask --app app db upgrade      # creates instance/local.db (SQLite)
flask --app app run --debug
```

Open http://127.0.0.1:5000 and log in with your `APP_PASSWORD`.

Without `DATABASE_URL` the app uses a local SQLite file. Set `DATABASE_URL` to a Postgres URL to use Postgres instead.

## Tests

```
pytest
```

Tests never call Moxfield or Scryfall. They use saved responses in `tests/fixtures/`.

## Changing the database

After editing `app/models.py`:

```
flask --app app db migrate -m "describe the change"
flask --app app db upgrade
```

Commit the new file in `migrations/versions/`. Render applies it on the next deploy.

## Deploy

Render (free web service) with Neon (free Postgres). Step-by-step checklist in [`docs/DEPLOY.md`](docs/DEPLOY.md).

## Moxfield note

Moxfield has no official API. The app uses the same undocumented endpoints Moxfield's site uses, only for public decks, from the Render server. Moxfield's Cloudflare blocks most cloud servers but currently allows Render. If that changes, sync stops and pasted decklists still work. Details in `docs/DECISIONS.md`.
