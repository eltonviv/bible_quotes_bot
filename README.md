# Daily Bible Verse → Instagram Bot

Pipeline: **KJV text (cached JSON)** → **AI artwork (Pollinations, free)** →
**text overlay (Pillow)** → **push image to GitHub** → **Instagram Graph API**.
Orchestrated by Python, scheduled by GitHub Actions (free for public repos,
2,000 min/month free for private repos).

```
Bible API      AI Image Gen      Text Overlay      GitHub push      Instagram
(KJV text) ─▶  (Pollinations) ─▶ (Pillow)      ─▶  (public URL) ─▶  Graph API
                        Orchestrated by main.py, scheduled by GitHub Actions
```

## 1. Push this repo to GitHub

```bash
cd bible_quotes
git init
git add .
git commit -m "Initial pipeline"
git branch -M main
git remote add origin https://github.com/<you>/<repo>.git
git push -u origin main
```

Repo can be public or private — either works with GitHub Actions and with
`raw.githubusercontent.com`, as long as the Instagram app's server can reach
the URL (a private repo's raw URL is NOT publicly fetchable, so **use a
public repo**, or a public repo just for the `output/` images if you want
the code itself private).

## 2. Set up Instagram Graph API access (one-time, ~20–30 min)

This is the fiddly part — Meta's side, not this code.

1. Convert your Instagram account to a **Business** or **Creator** account
   (Settings → Account type).
2. Link it to a **Facebook Page** (required even if you never use the Page).
3. Go to [developers.facebook.com](https://developers.facebook.com) → create
   an app → type "Business".
4. Add the **Instagram Graph API** product to the app.
5. Under Tools → Graph API Explorer, generate a **User Access Token** with
   these permissions: `instagram_basic`, `instagram_content_publish`,
   `pages_show_list`, `pages_read_engagement`.
6. Exchange it for a **long-lived token** (lasts ~60 days):
   ```
   GET https://graph.facebook.com/v21.0/oauth/access_token
     ?grant_type=fb_exchange_token
     &client_id=<APP_ID>
     &client_secret=<APP_SECRET>
     &fb_exchange_token=<SHORT_LIVED_TOKEN>
   ```
7. Find your **Instagram Business Account ID**:
   ```
   GET https://graph.facebook.com/v21.0/me/accounts?access_token=<TOKEN>
   ```
   then, using the Page ID from that response:
   ```
   GET https://graph.facebook.com/v21.0/<PAGE_ID>?fields=instagram_business_account&access_token=<TOKEN>
   ```
8. Submit the app for **App Review** requesting `instagram_content_publish`
   (needed for anything beyond your own test account; Meta usually takes
   1–3 weeks). While in development mode, you can post to accounts added as
   Instagram Testers under Roles without waiting for review.

⚠️ **Token expiry**: long-lived tokens last ~60 days. You'll need to refresh
and update the `IG_ACCESS_TOKEN` secret periodically (or extend
`post_to_instagram.py` with an auto-refresh step — ask if you'd like that
added).

## 3. Add GitHub Secrets

Repo → Settings → Secrets and variables → Actions → New repository secret:

- `IG_USER_ID` — the Instagram Business Account ID from step 7 above
- `IG_ACCESS_TOKEN` — the long-lived token from step 6

## 4. Test locally before relying on the schedule

```bash
pip install -r requirements.txt
python main.py                 # generates today's image, prints the reference/text
# inspect output/<date>_post.jpg — check it looks right
```

To test the actual Instagram post, push the generated image to GitHub first
(so it has a real public URL), then:

```bash
IG_USER_ID=... IG_ACCESS_TOKEN=... \
  python post_to_instagram.py output/<date>_meta.json https://raw.githubusercontent.com/<you>/<repo>/main/output/<date>_post.jpg
```

## 5. Let it run

The workflow in `.github/workflows/daily-post.yml` runs daily at 08:00 UTC.
Edit the cron line to change the time. You can also trigger a run manually
from the repo's **Actions** tab (`workflow_dispatch`).

## How progress/state works

`state.json` tracks which curated verse is next (`curated_index`), so each
day continues from where the last one left off instead of repeating. It's
committed back to the repo by the workflow after each run — don't add it to
`.gitignore`.

The pipeline currently uses **Option A: a curated list** of ~208 hand-picked,
well-known verses (`data/curated_verses.json`) that already read well as
standalone quotes — no API key or billing needed. At one post/day that's
about 7 months before it repeats. To extend it, just add more
`"Book Chapter:Verse"` strings to that file; every entry is validated
against the Bible text at runtime and skipped with a warning if it doesn't
resolve, so a typo won't break a scheduled run.

Two upgrade paths exist if/when you want them, already built and ready to
swap in:
- `verse_selector.py` — scans the whole Bible sequentially with a keyword
  filter, so you're not limited to a fixed list. Free, but the filter can
  still admit a mediocre verse sometimes.
- `llm_selector.py` — has Claude judge each chapter for real quotability.
  Best quality, needs a console.anthropic.com account with billing attached
  (cost for this workload is a fraction of a cent/day).

## Files

| File | Purpose |
|---|---|
| `bible_data.py` | Downloads + caches the full public-domain KJV text |
| `curated_selector.py` | **(active)** Cycles through the curated verse list |
| `verse_selector.py` | (optional upgrade) Sequential scan + keyword filter |
| `llm_selector.py` | (optional upgrade) Claude judges verse quality — needs `ANTHROPIC_API_KEY`, `pip install anthropic` |
| `image_gen.py` | Generates mood-matched AI artwork via Pollinations (free, no key) |
| `compose_image.py` | Overlays verse text on the artwork with Pillow |
| `main.py` | Runs one full daily cycle, saves image + metadata, updates state |
| `post_to_instagram.py` | Publishes a hosted image to Instagram via Graph API |
| `.github/workflows/daily-post.yml` | Schedules the whole pipeline |

## Known limitations to be aware of

- **Pollinations.ai** is free/keyless but has no uptime SLA — if it's down,
  that day's run fails. Consider wrapping `image_gen.py` in a retry, or
  swapping in a paid provider (Stability AI, OpenAI Images) if reliability
  matters.
- The curated list repeats after ~208 days (~7 months) at one post/day.
  Expand `data/curated_verses.json` or switch to `verse_selector.py`
  (sequential + free) or `llm_selector.py` (sequential + Claude-judged) if
  you want it to run longer before repeating.
- Instagram's Graph API requires the image to already be at a public URL —
  that's why the workflow commits it to the repo before posting rather than
  uploading a file directly.
