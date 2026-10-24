"""REST API for keeping short notes from a DevOps lab."""

import os

import psycopg
from flask import Flask, jsonify, request
from psycopg.rows import dict_row


app = Flask(__name__)
DATABASE_URL = os.environ.get("DATABASE_URL")


def connect_db():
    """Open a PostgreSQL connection using the URL supplied by the environment."""
    if not DATABASE_URL:
        raise RuntimeError("Set the DATABASE_URL environment variable")
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def init_db():
    """Create the notes table the first time the API starts."""
    with connect_db() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                title VARCHAR(120) NOT NULL,
                body TEXT NOT NULL DEFAULT '',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )


def validate_note(payload):
    """Return cleaned note fields, or a short validation error."""
    if not isinstance(payload, dict):
        return None, "Send a JSON object"

    title = payload.get("title")
    body = payload.get("body", "")
    if not isinstance(title, str) or not title.strip():
        return None, "title must be a non-empty string"
    if len(title.strip()) > 120:
        return None, "title must be at most 120 characters"
    if not isinstance(body, str):
        return None, "body must be a string"

    return {"title": title.strip(), "body": body.strip()}, None


@app.get("/healthz")
def health_check():
    """Check that both the API process and its database are reachable."""
    with connect_db() as connection:
        connection.execute("SELECT 1")
    return jsonify({"status": "ok", "database": "connected"})


@app.get("/api/notes")
def list_notes():
    with connect_db() as connection:
        rows = connection.execute(
            "SELECT id, title, body, created_at FROM notes ORDER BY id"
        ).fetchall()
    return jsonify(rows)


@app.post("/api/notes")
def create_note():
    note, error = validate_note(request.get_json(silent=True))
    if error:
        return jsonify({"error": error}), 400

    with connect_db() as connection:
        row = connection.execute(
            """
            INSERT INTO notes (title, body)
            VALUES (%s, %s)
            RETURNING id, title, body, created_at
            """,
            (note["title"], note["body"]),
        ).fetchone()
    return jsonify(row), 201


@app.get("/api/notes/<int:note_id>")
def get_note(note_id):
    with connect_db() as connection:
        row = connection.execute(
            "SELECT id, title, body, created_at FROM notes WHERE id = %s",
            (note_id,),
        ).fetchone()
    if row is None:
        return jsonify({"error": "note not found"}), 404
    return jsonify(row)


@app.put("/api/notes/<int:note_id>")
def update_note(note_id):
    note, error = validate_note(request.get_json(silent=True))
    if error:
        return jsonify({"error": error}), 400

    with connect_db() as connection:
        row = connection.execute(
            """
            UPDATE notes SET title = %s, body = %s
            WHERE id = %s
            RETURNING id, title, body, created_at
            """,
            (note["title"], note["body"], note_id),
        ).fetchone()
    if row is None:
        return jsonify({"error": "note not found"}), 404
    return jsonify(row)


@app.delete("/api/notes/<int:note_id>")
def delete_note(note_id):
    with connect_db() as connection:
        deleted = connection.execute(
            "DELETE FROM notes WHERE id = %s RETURNING id", (note_id,)
        ).fetchone()
    if deleted is None:
        return jsonify({"error": "note not found"}), 404
    return "", 204


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
