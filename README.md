# AfrikThrive8 Foundation — Forms + Live Dashboard

Python (Flask) backend, PostgreSQL for data, Supabase Storage for speaker headshots.

## What's inside

```
afrikthrive8_app/
├── app.py                  ← routes (forms, submissions, dashboard API)
├── db.py                   ← PostgreSQL connection + queries
├── storage.py               ← Supabase Storage upload (speaker headshots)
├── requirements.txt
├── .env.example             ← copy to .env and fill in real values
├── Procfile                 ← for deployment (Render/Railway)
├── templates/
│   ├── speaker_form.html        (linked to the Info Pack PDF; accepts ?topic= prefill)
│   ├── participant_form.html    (reads ?session=&topic=&date=&platform= from the URL)
│   ├── evaluate_form.html       (internal — feeds the dashboard live)
│   ├── new_session.html         (generates shareable links for a new session — no editing needed)
│   ├── dashboard.html           (tabs auto-generated from your data)
│   └── thanks.html
└── static/
    ├── logo.png, brand.css, AfrikThrive8_Speakers_Information_Pack.pdf
```

## One-time setup: Supabase (free tier covers everything here)

Supabase gives you a free Postgres database *and* file storage in one project —
this app uses both, so you only need one account.

1. Go to supabase.com → New project. Note the database password you set.
2. **Database:** Project Settings → Database → Connection string → URI (choose
   "Session pooler"). Copy it into `DATABASE_URL` in your `.env`.
3. **Storage:** left sidebar → Storage → New bucket → name it `headshots` →
   toggle **Public bucket ON** (headshots are meant to appear on flyers and the
   dashboard, so public is correct — no private participant data lives here).
4. **API keys:** Project Settings → API. Copy the **Project URL** into
   `SUPABASE_URL`, and the **service_role** key (not the `anon` key — the
   service_role key is what's allowed to upload) into `SUPABASE_SERVICE_KEY`.
5. Copy `.env.example` to `.env` and paste in the four values above.

## Run it locally

```bash
cd afrikthrive8_app
pip install -r requirements.txt
cp .env.example .env      # then fill in your real Supabase values
python app.py
```

First run creates the Postgres tables automatically. Then open:
- **Speaker form:** http://localhost:5000/speaker
- **Participant form:** http://localhost:5000/participant?session=cv-writing-aug2026&topic=CV+Writing&date=15+Aug+2026&platform=X+Space
- **Internal evaluation form:** http://localhost:5000/evaluate
- **New Session link builder:** http://localhost:5000/new-session
- **Dashboard:** http://localhost:5000/dashboard

## Setting up a new session (no file editing required)

Open `/new-session` in your browser, fill in the topic, date and platform, and
click **Generate Links**. You get back two ready-to-share links:

- A **participant link** — the moment the first person registers through it,
  that session appears as a new tab on `/dashboard`.
- A **speaker link** — same speaker form, but with the Topic of Interest field
  pre-filled with this session's topic, so it's obvious to speakers which
  session they're applying to.

You can also build the links by hand if you prefer:

```
/participant?session=<unique-slug>&topic=<Session Name>&date=<Date>&platform=<X Space>
/speaker?topic=<Session Name>
```

## Editing the placeholder heading you saw before

The old static HTML file had a hardcoded bracket placeholder. In this app,
`templates/participant_form.html` no longer hardcodes anything — its `<h1>`
is `{{ topic }}`, filled in from the `topic=` value in the link (see above).
**Set the real session name in the link, not in the file.** If you ever want
one permanently fixed form instead of a link-per-session, open
`app.py`, find `participant_form()`, and change the default:

```python
topic = request.args.get("topic", "AfrikThrive8 Master Talk")   # change this fallback text
```

## Deploying so the links work from anywhere

Render's free web-service tier no longer includes a persistent disk — but this
app no longer needs one, since both the database (Postgres, on Supabase) and
the file storage (Supabase Storage) now live outside the web server. That
means you can deploy on Render's free tier with **no disk at all**:

1. Push this folder to a GitHub repository.
2. render.com → New → Web Service → connect the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Environment → add the four variables from your `.env` (`DATABASE_URL`,
   `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SUPABASE_BUCKET`) as Render
   environment variables — do not commit `.env` itself.
6. Deploy. You'll get a URL like `https://afrikthrive8.onrender.com`. Every
   link works from there exactly as it does locally.

Railway.app works the same way, if you prefer it.

## Notes

- Uploaded headshots are capped at 8MB and must be .png/.jpg/.jpeg/.webp.
- The dashboard auto-refreshes every 15 seconds while open.
- Speaker headshot URLs are now full public Supabase URLs, stored directly
  in the database — the dashboard renders them as-is.
- The Speakers Pool tab is not tied to one session — it's your whole speaker
  pipeline, with live average evaluation scores as `/evaluate` submissions
  come in.
