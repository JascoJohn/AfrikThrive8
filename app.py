"""
AfrikThrive8 Foundation — Forms + Dashboard backend
=====================================================
PostgreSQL for data, Supabase Storage for speaker headshots.

Run locally:
    cp .env.example .env      # fill in your real values
    pip install -r requirements.txt
    python app.py
Then open:
    http://localhost:5000/speaker
    http://localhost:5000/participant?session=cv-writing-aug2026&topic=CV%2FResume+Writing
    http://localhost:5000/dashboard
    http://localhost:5000/new-session   <- builds shareable links for a new session, no editing needed
"""

import os
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
load_dotenv()  # reads .env in local dev; in production set real env vars on the host

from flask import Flask, request, render_template, redirect, url_for, jsonify

import db
import storage

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8MB upload cap
app.teardown_appcontext(db.close_db)


def slugify(text):
    return "".join(c.lower() if c.isalnum() else "-" for c in (text or "")).strip("-") or "general"


def now():
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Home
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    return render_template("home.html")


# ---------------------------------------------------------------------------
# Form pages
# ---------------------------------------------------------------------------

@app.route("/speaker", methods=["GET"])
def speaker_form():
    # Optional ?topic=... to prefill for a session-specific call for speakers
    prefill_topic = request.args.get("topic", "")
    return render_template("speaker_form.html", prefill_topic=prefill_topic)


@app.route("/speaker/submit", methods=["POST"])
def speaker_submit():
    f = request.form
    headshot_url = storage.upload_headshot(request.files.get("headshot"))

    db.query(
        """INSERT INTO speakers
           (id, full_name, marital_status, age, country, title, organization, bio,
            headshot_path, email, x_handle, linkedin, topic, experience, consent, submitted_at)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (
            uuid.uuid4().hex, f.get("fullNames"), f.get("marital"), f.get("age"),
            f.get("country"), f.get("title"), f.get("org"), f.get("bio"),
            headshot_url, f.get("email"), f.get("xhandle"), f.get("linkedin"),
            f.get("topic"), f.get("experience"), 1 if f.get("consent") else 0,
            now(),
        ),
        fetch=None,
    )
    return redirect(url_for("speaker_thanks"))


@app.route("/speaker/thanks")
def speaker_thanks():
    return render_template("thanks.html",
        heading="Thank you for applying!",
        message="Our team will review your application and contact you by email or X with next steps, including your speaking slot and time allocation.")


@app.route("/participant", methods=["GET"])
def participant_form():
    session_slug = request.args.get("session", "general")
    topic = request.args.get("topic", "AfrikThrive8 Master Talk")
    date = request.args.get("date", "TBC")
    platform = request.args.get("platform", "X Space")
    return render_template("participant_form.html",
        session_slug=session_slug, topic=topic, date=date, platform=platform)


@app.route("/participant/submit", methods=["POST"])
def participant_submit():
    f = request.form
    db.query(
        """INSERT INTO participants
           (id, session, session_label, full_name, email, phone, country,
            age_group, gender, status, goal, source, submitted_at)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (
            uuid.uuid4().hex, f.get("session", "general"), f.get("session_label"),
            f.get("fullName"), f.get("email"), f.get("phone"), f.get("country"),
            f.get("age"), f.get("gender"), f.get("status"), f.get("goal"),
            f.get("source"), now(),
        ),
        fetch=None,
    )
    return redirect(url_for("participant_thanks"))


@app.route("/participant/thanks")
def participant_thanks():
    return render_template("thanks.html",
        heading="You're registered!",
        message="Check your email for the session link. Follow us on X so you don't miss the Space when it goes live.")


@app.route("/evaluate", methods=["GET"])
def evaluate_form():
    return render_template("evaluate_form.html")


@app.route("/evaluate/submit", methods=["POST"])
def evaluate_submit():
    f = request.form
    db.query(
        """INSERT INTO evaluations
           (id, session, session_label, speaker_name, topic, knowledge, communication,
            engagement, time_management, professionalism, invite_again, strengths,
            improve, evaluated_by, submitted_at)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (
            uuid.uuid4().hex, slugify(f.get("session_label")), f.get("session_label"),
            f.get("speaker_name"), f.get("topic"),
            int(f.get("knowledge") or 0), int(f.get("communication") or 0),
            int(f.get("engagement") or 0), int(f.get("time_management") or 0),
            int(f.get("professionalism") or 0), f.get("invite_again"),
            f.get("strengths"), f.get("improve"), f.get("evaluated_by"),
            now(),
        ),
        fetch=None,
    )
    return redirect(url_for("evaluate_form"))


# ---------------------------------------------------------------------------
# New Session link builder (answers "how do I set up another session?")
# ---------------------------------------------------------------------------

@app.route("/new-session")
def new_session_builder():
    return render_template("new_session.html")


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/api/sessions")
def api_sessions():
    rows = db.query(
        """SELECT session, COALESCE(MAX(session_label), session) AS label, COUNT(*) AS n,
                  MAX(submitted_at) AS last_activity
           FROM participants GROUP BY session ORDER BY last_activity DESC"""
    )
    return jsonify([dict(r) for r in rows])


@app.route("/api/dashboard-data/<session>")
def api_dashboard_data(session):
    total_row = db.query("SELECT COUNT(*) c FROM participants WHERE session=%s", (session,), fetch="one")
    total = total_row["c"] if total_row else 0

    def breakdown(col):
        rows = db.query(
            f"SELECT COALESCE(NULLIF({col},''),'Not stated') AS k, COUNT(*) c "
            f"FROM participants WHERE session=%s GROUP BY k ORDER BY c DESC", (session,)
        )
        return {r["k"]: r["c"] for r in rows}

    timeline = db.query(
        """SELECT TO_CHAR(submitted_at, 'YYYY-MM-DD') AS day, COUNT(*) c FROM participants
           WHERE session=%s GROUP BY day ORDER BY day""", (session,)
    )

    return jsonify({
        "total": total,
        "age_group": breakdown("age_group"),
        "gender": breakdown("gender"),
        "country": breakdown("country"),
        "status": breakdown("status"),
        "source": breakdown("source"),
        "timeline": {r["day"]: r["c"] for r in timeline},
    })


@app.route("/api/speakers")
def api_speakers():
    speakers = db.query("SELECT * FROM speakers ORDER BY submitted_at DESC")
    out = []
    for s in speakers:
        s = dict(s)
        evals = db.query(
            "SELECT * FROM evaluations WHERE speaker_name=%s ORDER BY submitted_at DESC",
            (s["full_name"],),
        )
        if evals:
            n = len(evals)
            avg = lambda col: round(sum((e[col] or 0) for e in evals) / n, 1)
            s["eval_count"] = n
            s["avg_knowledge"] = avg("knowledge")
            s["avg_communication"] = avg("communication")
            s["avg_engagement"] = avg("engagement")
            s["avg_time_management"] = avg("time_management")
            s["avg_professionalism"] = avg("professionalism")
            s["avg_overall"] = round(
                (s["avg_knowledge"] + s["avg_communication"] + s["avg_engagement"]
                 + s["avg_time_management"] + s["avg_professionalism"]) / 5, 1)
            yes = sum(1 for e in evals if (e["invite_again"] or "").lower() == "yes")
            s["invite_again_pct"] = round(100 * yes / n)
        else:
            s["eval_count"] = 0
            s["avg_overall"] = None
            s["invite_again_pct"] = None
        out.append(s)
    return jsonify(out)


if __name__ == "__main__":
    db.init_db()
    print("Postgres tables ready.")
    app.run(debug=False, port=5000)
