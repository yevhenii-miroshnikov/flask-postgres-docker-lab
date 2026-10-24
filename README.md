# Flask Notes API with Docker Compose

A small Flask REST API for managing notes, backed by PostgreSQL and packaged with Docker. This university lab project demonstrates manual container networking, persistent database storage with a named volume, and a repeatable two-service Docker Compose setup.

## Project Context

This project was developed for a university practical assignment on application containerization. The implementation extends the basic container workflow with a PostgreSQL-backed API, persistent storage, a database health check, and a Bash deployment script.

## 📖 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [REST API](#rest-api)
- [Verification and Data Persistence](#verification-and-data-persistence)
- [Scope and Limitations](#scope-and-limitations)
- [Kurzbeschreibung (DE)](#kurzbeschreibung-de)
- [Contact](#contact)

## Overview

- Create, list, retrieve, update, and delete notes through a JSON REST API.
- Store notes in PostgreSQL using Psycopg 3.
- Build the API as a Docker image that runs as a non-root user.
- Run the API and database as separate containers on a Compose-managed network.
- Persist PostgreSQL data in a named Docker volume across container recreation.
- Use a database health check so Compose waits for PostgreSQL before starting the API.
- Start or update the local stack with `docker compose` or `bash deploy.sh`.

## Architecture

```text
Host client (curl / browser)
        │
        │ http://127.0.0.1:8002
        ▼
API container (Flask, port 8000)
        │
        │ Compose network: db:5432
        ▼
PostgreSQL container (port 5432)
        │
        │ /var/lib/postgresql/data
        ▼
Named volume: devops-lab1-compose-pgdata
```

The host publishes only the API as `127.0.0.1:8002` to container port `8000`. PostgreSQL listens on port `5432` inside the Compose network and is not published to the host in the Compose configuration. The API reaches the database using the Compose service name `db`.

## Technology Stack

| Component | Version or constraint |
| --- | --- |
| Python | `3.14-slim` container image |
| Flask | `>=3.1,<4` |
| Psycopg | `>=3.2,<4` (`psycopg[binary]`) |
| PostgreSQL | `17.11` |
| Docker | Docker Engine with Docker Compose v2 |

`requirements.txt` uses compatible version ranges rather than a fully pinned dependency lock, so the exact Python package versions may change between builds.

## Project Structure

```text
.
├── README.md         # Project overview, setup, API, and persistence guide
├── app.py            # Flask REST API and table initialization
├── requirements.txt  # Python runtime dependencies
├── Dockerfile        # API image definition
├── compose.yaml      # API, PostgreSQL, health check, and named volume
├── deploy.sh         # Validate, build, and start the Compose stack
├── .env.example      # Safe template for the local database password
├── .gitignore        # Excludes local credentials, environments, and caches
└── .dockerignore     # Keeps local files out of the Docker build context
```

The local `.env` file is created from `.env.example` and is intentionally not part of the repository.

## Quick Start

### Requirements

- Docker Desktop with Linux containers on Windows, or Docker Engine with the Docker Compose v2 plugin on Linux/macOS.
- Git Bash on Windows, or Bash on Linux/macOS, to run `deploy.sh`.

Clone the repository and enter its root directory:

```bash
git clone https://github.com/yevhenii-miroshnikov/flask-postgres-docker-lab.git
cd flask-postgres-docker-lab
```

Create the local environment file and set a non-empty, URL-safe development password for `LAB_DB_PASSWORD`:

```bash
cp .env.example .env
```

Open `.env` in a text editor and set the value. Use a local test password only; never commit `.env`. The Compose file requires this value and uses it for both PostgreSQL initialization and the API connection URL.

Start the stack using either the deployment script:

```bash
bash deploy.sh
```

or Docker Compose directly:

```bash
docker compose up --build --detach
```

Check the service state and API health:

```bash
docker compose ps
curl --include http://127.0.0.1:8002/healthz
```

The health endpoint should return HTTP `200` with JSON indicating `status` is `ok` and the database is `connected`.

On Windows PowerShell, the equivalent health request is:

```powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:8002/healthz'
```

## Configuration

| Variable | Required | Description |
| --- | --- | --- |
| `LAB_DB_PASSWORD` | Yes | Local development password passed to PostgreSQL and used by the API connection URL. |

`.env.example` contains an empty value and no credentials. Copy it to `.env` and set a local password before starting Compose. This simple connection URL expects a password made of URL-safe characters. The credentials are intended for a local learning environment, not for production use.

The PostgreSQL image applies `POSTGRES_PASSWORD` when initializing an empty data directory. Changing `LAB_DB_PASSWORD` later does not change the password of a database that has already been initialized in the named volume.

## REST API

All note requests use JSON. A note has a required non-empty `title` of at most 120 characters and an optional string `body` (empty by default).

| Method | Endpoint | Description | Successful response |
| --- | --- | --- | --- |
| `GET` | `/healthz` | Check API-to-database connectivity | `200 OK` |
| `GET` | `/api/notes` | List notes ordered by ID | `200 OK` |
| `POST` | `/api/notes` | Create a note | `201 Created` |
| `GET` | `/api/notes/<note_id>` | Retrieve one note | `200 OK` |
| `PUT` | `/api/notes/<note_id>` | Replace a note's title and body | `200 OK` |
| `DELETE` | `/api/notes/<note_id>` | Delete one note | `204 No Content` |

Invalid note payloads return `400 Bad Request`. Requests for a note ID that does not exist return `404 Not Found` for the single-note, update, and delete endpoints.

Create and retrieve a note with `curl`:

```bash
curl --include --request POST http://127.0.0.1:8002/api/notes \
  --header 'Content-Type: application/json' \
  --data '{"title":"First note","body":"Created during local verification."}'

curl --include http://127.0.0.1:8002/api/notes
```

## Verification and Data Persistence

The following workflow checks that a note remains in PostgreSQL after its containers are recreated:

1. Start the stack and create a note using the `POST /api/notes` example above. Keep the returned note ID.
2. Confirm it appears in `GET /api/notes`.
3. From the project root, stop and remove this Compose stack's containers and network:

   ```bash
   docker compose down
   ```

4. Start the stack again:

   ```bash
   docker compose up --build --detach
   ```

5. Request `GET /api/notes` again and confirm the note is still present.

The named volume stores PostgreSQL files outside the container, so the data remains when Compose removes and recreates the containers. The command above does not remove the volume. A fresh clone starts with an empty database; the local verification note is not included in the repository.

For this project, the API health endpoint, note creation, note listing, and data persistence after container recreation were exercised locally. The manual Docker workflow was also used to connect a separately run API container to PostgreSQL over a user-defined bridge network. No automated test suite or CI workflow is included.

## Scope and Limitations

- This is an academic local-containerization project, not a production deployment.
- The app uses Flask's built-in development server and has no authentication, authorization, TLS, or request rate limiting.
- The API creates the `notes` table at startup with `CREATE TABLE IF NOT EXISTS`; there is no database migration system.
- PostgreSQL is reachable from the API over the Compose network, while only the API port is bound to the host loopback address.
- Python dependencies use version ranges and are not locked to exact package versions.
- The local `.env` password is a learning credential. Use a secrets-management approach for any real deployment.

<a id="kurzbeschreibung-de"></a>
## 🇩🇪 Kurzbeschreibung

Dieses akademische Projekt entstand im Rahmen einer universitären Übung zur Containerisierung einer Anwendung. Es besteht aus einer Flask-REST-API und einer PostgreSQL-Datenbank in getrennten Docker-Containern. Docker Compose startet beide Dienste, prüft die Bereitschaft der Datenbank und speichert die Daten in einem benannten Volume, das Container-Neuerstellungen überdauert. Das Projekt ist für eine lokale Lernumgebung gedacht und nicht produktionsbereit.

<a id="contact"></a>
## 📬 Contact

- **GitHub:** [@yevhenii-miroshnikov](https://github.com/yevhenii-miroshnikov)
- **LinkedIn:** [yevhenii-miroshnikov](https://www.linkedin.com/in/yevhenii-miroshnikov)
