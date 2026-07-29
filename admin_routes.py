"""
Admin routes for exporting participant and speaker data.

INTEGRATION:
1. Save this file as admin_routes.py in the same folder as app.py.
2. In app.py, add near the top (with your other imports):
       import admin_routes
   And near the bottom, right after `app = Flask(__name__)` is defined
   (or anywhere before app.run()):
       admin_routes.register_admin_routes(app)
3. On Render: Dashboard -> your service -> Environment -> add
       ADMIN_API_KEY = <a long random string, e.g. generate one locally with
                         python -c "import secrets; print(secrets.token_urlsafe(32))">
   Never hardcode this value in the file.
4. Access:
     https://your-app.onrender.com/admin/speakers?key=YOUR_ADMIN_API_KEY
     https://your-app.onrender.com/admin/speakers?key=YOUR_ADMIN_API_KEY&format=csv
     https://your-app.onrender.com/admin/participants?key=YOUR_ADMIN_API_KEY
     https://your-app.onrender.com/admin/participants?key=YOUR_ADMIN_API_KEY&format=csv&session_id=cv-writing-aug2026
"""

import os
import csv
import io
from flask import request, jsonify, Response

import db  # your existing db.py — reuses its query() + request-scoped connection

ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY")


def _check_auth():
    return ADMIN_API_KEY and request.args.get("key") == ADMIN_API_KEY


def _rows_to_csv_response(rows, filename):
    if not rows:
        return jsonify({"message": "No records found"}), 200
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    for row in rows:
        writer.writerow(dict(row))
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def register_admin_routes(app):

    @app.route("/admin/participants")
    def admin_get_participants():
        if not _check_auth():
            return jsonify({"error": "Unauthorized"}), 401

        session_id = request.args.get("session_id")
        output_format = request.args.get("format", "json")

        if session_id:
            rows = db.query(
                "SELECT * FROM participants WHERE session=%s ORDER BY submitted_at DESC",
                (session_id,),
            )
        else:
            rows = db.query("SELECT * FROM participants ORDER BY submitted_at DESC")

        if output_format == "csv":
            return _rows_to_csv_response(rows, "participants.csv")
        return jsonify([dict(r) for r in rows]), 200

    @app.route("/admin/speakers")
    def admin_get_speakers():
        if not _check_auth():
            return jsonify({"error": "Unauthorized"}), 401

        output_format = request.args.get("format", "json")
        rows = db.query("SELECT * FROM speakers ORDER BY submitted_at DESC")

        if output_format == "csv":
            return _rows_to_csv_response(rows, "speakers.csv")
        return jsonify([dict(r) for r in rows]), 200
