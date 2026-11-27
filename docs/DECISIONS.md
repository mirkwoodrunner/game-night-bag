# Decisions

Non-obvious choices, with the reason and the alternatives considered. Newest first.

## 2026-11-27 Phase 0. Moxfield sync approach

### Finding 1. The server can fetch public decks from Render

- Chris's mtg-collection-tracker app (Node, on Render) calls `GET https://api.moxfield.com/v2/decks/all/{publicId}` anonymously with a simple `User-Agent`. Chris confirmed its sync still works on 2026-11-27.
- From the Claude Code cloud container, every Moxfield API request (`api.moxfield.com`, `api2.moxfield.com`) returns Cloudflare's "Attention Required" 403 page, whatever the `User-Agent`. So Cloudflare treats datacenter IPs differently, and Render is currently allowed.
- Consequence. Moxfield can only be tested against from Render. Tests rely on responses captured there.

### Finding 2. Folders are not public

- Viewed logged out, `https://moxfield.com/users/mirkwoodrunner` shows decks but no folders. The EDH folder (`4QVN9`) can only be read with Chris's login.
- Two guessed public list URLs (`api2.moxfield.com/v2/users/{user}/decks` and `api2.moxfield.com/v3/decks/search?authorUserNames={user}`) gave a 0 KB download in a phone browser. Inconclusive. Either the URLs are wrong or Moxfield returns nothing to a plain tab. The profile page proves some public list endpoint exists.

### Decision. Server-side fetch, rotation = public Commander decks

Chris keeps rotation decks public and sets retired and league decks to unlisted or private. The server lists `mirkwoodrunner`'s public decks, keeps Commander format, and fetches each deck. Sync is a button in the app, usable from a phone.

Why. Chris does not want to depend on running a script on a desktop. This option is fully automatic, works from the phone and stores no credentials.

Alternatives considered:
- **Browser script on moxfield.com sends everything (original CLAUDE.md plan).** Reads the real folder and avoids depending on Render getting past Cloudflare. Rejected because every sync needs a desktop browser.
- **Browser script sends only folder ids, server fetches decks.** Uses the real folder, and the script only runs when membership changes. On iPhone it needs the Safari "Userscripts" extension, and the folder endpoint and login token access are unknown. Kept as the next option if the visibility signal proves awkward.
- **Store Chris's Moxfield login token on the server.** Rejected. A leaked token gives control of the Moxfield account, tokens expire, and it is the most likely to break Moxfield's terms.
- **Server logs in with a headless browser.** Rejected. Stores a password, means fighting Cloudflare, and breaks the project rule.
- **Filter by Commander format alone.** Rejected. Chris has Commander decks in a retired folder and league decks outside his rotation.
- **Paste each deck's link into the app.** Proven, but not automatic. Kept as the fallback for adding or refreshing one deck.

### Open items

- Find the public deck list endpoint. Plan is a temporary, login-protected probe route on Render that fetches candidate URLs and shows status and the first part of each body. Remove it once the endpoint is recorded here.
- Capture one real deck JSON and the deck list JSON from Render as test fixtures.
- Decide the token source. Moxfield's deck JSON has a `tokens` field (the old app used it, and needed a filter for non-token cards). Scryfall `all_parts` is the current plan. Compare both on decks with Queen Marchesa, an Initiative card, Elspeth, Sun's Champion and Bitterblossom before building Phase 1 step 3.
- Scryfall is also blocked from this container by the network allowlist, not Cloudflare. Allowing `api.scryfall.com` in the cloud environment is needed to save Scryfall fixtures.
- Risks. If Moxfield starts blocking Render, sync stops with no fix on our side. Pasted decklists keep working. Moxfield's terms have not been reviewed yet (the site was unreachable from here).
