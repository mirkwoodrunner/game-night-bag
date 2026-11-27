# Deploy checklist

Everything here works from a phone browser, though a computer is easier. It takes about 20 minutes. You need a GitHub login.

## 1. Get the code on `main`

Render deploys from a branch. The code is on `claude/game-night-bag-planning-4c98v7` until it is merged into `main` with a pull request. Either merge first, or pick that branch in step 3.

## 2. Create the Neon database

1. Go to https://neon.tech and sign up with GitHub. The free plan is enough.
2. Create a project.
   - Name `game-night-bag`
   - Region **AWS US West 2 (Oregon)**, close to Render's default region
3. On the project dashboard, tap **Connect**.
4. Turn **Connection pooling** on. The host name should now contain `-pooler`.
5. Copy the connection string. It looks like `postgresql://neondb_owner:...@ep-...-pooler.us-west-2.aws.neon.tech/neondb?sslmode=require`.

This string contains the database password. Treat it like one. Don't paste it into chats or commit it.

## 3. Create the Render service

1. Go to https://render.com and sign in with GitHub.
2. Tap **New**, then **Blueprint**.
3. Connect the `mirkwoodrunner/game-night-bag` repository. Pick the branch from step 1.
4. Render reads `render.yaml` and asks for two values.
   - `DATABASE_URL` is the Neon string from step 2.
   - `APP_PASSWORD` is the password you'll log in with. Use something long, since the site is public.
   - `SECRET_KEY` is generated for you. `MOXFIELD_USERNAME` is already set.
5. Tap **Apply**. The first deploy takes a few minutes.

## 4. Check the first migration

1. Open the service's **Logs** in Render.
2. Look for `Running upgrade  -> 6089f3ab3064, initial schema` and then `Listening at`.
3. Later deploys print nothing for the migration unless a new one was added.

If the deploy fails, the log's last lines say why. The most common cause is a mistyped `DATABASE_URL`.

## 5. Smoke test

Your URL is shown at the top of the Render service page, like `https://game-night-bag.onrender.com`.

1. Open `/healthz`. It should show `{"status": "ok"}`. The first visit after 15 idle minutes can take up to a minute while Render wakes up.
2. Open the site on your phone and log in.
3. The home page should say **Database connected**.
4. Optional. In Safari tap Share, then **Add to Home Screen**.

## 6. Moxfield probe (temporary)

1. Log in and tap **Moxfield probe**.
2. Tap **1. Try deck list URLs**. Wait about 10 seconds. Note which result shows **200** and `application/json`.
3. Paste one EDH deck link into box 2 and tap **Fetch deck**.
4. Report the status codes back in the chat.

## Free tier notes

- Render free services sleep after 15 minutes without traffic. The first request after that takes 30 to 60 seconds.
- Neon free databases pause when idle and wake in about a second. Unlike Render's free Postgres, they aren't deleted after 90 days.
