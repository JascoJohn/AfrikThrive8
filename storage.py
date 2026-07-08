"""
Supabase Storage layer — replaces saving headshots to static/uploads/headshots.

Uploads the file bytes to a Supabase Storage bucket and returns a public URL,
which is what gets stored in speakers.headshot_path and rendered directly by
the dashboard (<img src="{{ that URL }}">).

Required environment variables (see .env.example):
    SUPABASE_URL          e.g. https://xxxxxxxx.supabase.co
    SUPABASE_SERVICE_KEY   the "service_role" key (Project Settings -> API)
                            — NOT the anon/public key, because uploads need
                            write access; keep this secret, server-side only.
    SUPABASE_BUCKET        defaults to "headshots" if not set

One-time setup in the Supabase dashboard:
    1. Storage -> New bucket -> name it "headshots" -> toggle "Public bucket" ON
       (public, because headshots are meant to be shown on flyers/dashboard)
    2. Copy Project URL and service_role key from Project Settings -> API
       into your .env file (see .env.example)
"""

import os
import uuid
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
SUPABASE_BUCKET = os.environ.get("SUPABASE_BUCKET", "headshots")

_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

ALLOWED_IMAGE_EXT = {"png", "jpg", "jpeg", "webp"}


def allowed_image(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXT


def upload_headshot(file_storage):
    """
    file_storage: a Werkzeug FileStorage object from request.files.get('headshot').
    Returns the public URL string, or None if no valid file was provided.
    """
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_image(file_storage.filename):
        return None

    ext = file_storage.filename.rsplit(".", 1)[1].lower()
    object_path = f"{uuid.uuid4().hex}.{ext}"
    file_bytes = file_storage.read()
    content_type = file_storage.mimetype or "image/jpeg"

    _client.storage.from_(SUPABASE_BUCKET).upload(
        object_path,
        file_bytes,
        {"content-type": content_type},
    )
    public_url = _client.storage.from_(SUPABASE_BUCKET).get_public_url(object_path)
    return public_url
