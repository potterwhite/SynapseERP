<!--
Copyright (c) 2025-present, PotterWhite (themanuknowwhom@outlook.com).
All rights reserved.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
-->

<div align="center">
  <h1>SynapseERP</h1>
  <p><i>A Modular ERP Framework — Django Backend · Vue 3 Frontend · Docker Ready</i></p>
</div>

<p align="center">
  <img src="https://github.com/potterwhite/SynapseERP/blob/main/docs/assets/logo.jpg" alt="SynapseERP Logo" width="100%"/>
</p>

<p align="center">
  <a href="https://github.com/potterwhite/SynapseERP/releases"><img src="https://img.shields.io/github/v/release/potterwhite/SynapseERP?color=orange&label=version" alt="version"></a>
  <a href="#"><img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python Version"></a>
  <a href="#"><img src="https://img.shields.io/badge/framework-Django%205.x-green" alt="Framework"></a>
  <a href="#"><img src="https://img.shields.io/badge/frontend-Vue%203%20%2B%20TypeScript-42b883" alt="Frontend"></a>
  <a href="https://github.com/potterwhite/SynapseERP/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License"></a>
</p>

<p align="center">
  <strong>English</strong> | <a href="./docs/README.zh.md">简体中文</a>
</p>

<p align="center">
  <a href="#1-quick-start-local-dev">🚀 Quick Start</a> •
  <a href="#2-docker-deployment">🐳 Docker</a> •
  <a href="#3-production-deployment">⚙️ Production</a> •
  <a href="#4-appendix">📚 Appendix</a>
</p>

---

## Overview

SynapseERP is a modular internal tooling platform built on:

- **Backend** — Django 5.x + Django REST Framework + JWT authentication (SimpleJWT)
- **Frontend** — Vue 3 (Composition API) + TypeScript + Vite 6 + Naive UI
- **Database** — SQLite for local development, PostgreSQL for Docker / production
- **Deployment** — Docker Compose (all-in-one) or Nginx + Gunicorn + Systemd (bare-metal)

### Included Modules

| Module | Description |
|--------|-------------|
| **Project Management** | Kanban-style project & task tracker with optional Obsidian vault sync |
| **Attendance Analyzer** | Excel attendance file parser driven by a TOML rules engine |
| **BOM Analyzer** | Multi-file Bill-of-Materials aggregation tool |
| **Dashboard** | Markdown notification board visible to all users |

---

# 1. Quick Start (Local Dev)

**Prerequisites:** Python 3.10+, Node.js 18+, Git

### Step 1.1 — Get the Code

```bash
git clone git@github.com:potterwhite/SynapseERP.git
cd SynapseERP
chmod +x synapse
```

### Step 1.2 — Prepare the Environment

```bash
./synapse prepare
```

This single command:
- Creates a Python virtual environment (`.venv/`)
- Installs all Python dependencies
- Generates a secure `backend/.env` with a random `SECRET_KEY`
- Runs database migrations (SQLite by default)
- Compiles i18n translation files
- Installs frontend npm dependencies

### Step 1.3 — Create an Admin User

```bash
./synapse superuser
```

### Step 1.4 — Start the Application

```bash
# Backend only (http://127.0.0.1:8000)
./synapse run

# Frontend only (http://localhost:5173, proxies /api to :8000)
./synapse frontend:run

# Both at once
./synapse run:all
```

Log in at **http://localhost:5173** with the superuser account you just created.

---

# 2. Docker Deployment

Docker Compose runs a production-like stack with three services:
- **postgres** — PostgreSQL 16 (data persisted in a named volume)
- **backend** — Django + Gunicorn on port 8000 (internal only)
- **nginx** — serves the pre-built Vue SPA and proxies `/api/` to the backend (port 80)

### Step 2.1 — Configure Environment

```bash
cp .env.docker.example .env.docker
# Open .env.docker and set:
#   DJANGO_SECRET_KEY  (required — any long random string)
#   DB_PASSWORD        (required — PostgreSQL password)
```

### Step 2.2 — Start the Stack

```bash
./synapse docker:up
```

The first run builds both Docker images and starts all services. Visit **http://localhost**.

### Step 2.3 — Create an Admin User

```bash
./synapse docker:manage createsuperuser
```

### Common Docker Commands

```bash
./synapse docker:up              # Build + start all services
./synapse docker:down            # Stop and remove containers (data volumes preserved)
./synapse docker:clean           # ⚠️  Destroy containers + volumes + images (data loss!)
./synapse docker:logs            # Tail logs from all services
./synapse docker:logs backend    # Tail backend logs only
./synapse docker:shell           # Open a shell in the backend container
./synapse docker:manage <cmd>    # Run a Django management command in the backend container
```

> **`docker:down` vs `docker:clean`**
> - `docker:down` — stops and removes containers but **keeps** the PostgreSQL data volume. Safe to use between restarts.
> - `docker:clean` — removes containers, **all named volumes** (database data will be lost), and locally-built images. Use this to start completely fresh.

### Optional: Obsidian Vault Sync in Docker

Set `OBSIDIAN_VAULT_PATH` in `.env.docker` to the absolute path of your Obsidian vault on the **host machine**. The directory is automatically bind-mounted read-only into the backend container. No other changes are needed.

```bash
# In .env.docker:
OBSIDIAN_VAULT_PATH=/home/youruser/Documents/MyVault
```

Restart the stack after changing this value: `./synapse docker:down && ./synapse docker:up`

---

# 3. Production Deployment (Bare-metal)

For a server without Docker, SynapseERP can be deployed using Nginx + Gunicorn managed by Systemd.

```bash
sudo ./synapse deploy
```

This interactive command:
1. Checks that Nginx and `gettext` are installed
2. Asks for your server domain/IP and the Linux user to run the service
3. Builds the Vue frontend
4. Collects Django static files
5. Installs and enables Systemd socket + service units and an Nginx site config
6. Updates `backend/.env` with production settings

After deployment, the application is live at the domain you provided.

---

# 4. Appendix

### 4.1 All `./synapse` Commands

```
Setup & Run
  prepare             One-time setup (venv, deps, migrate, npm install)
  clean               Destructive local reset (removes .venv, DB, node_modules)
  run                 Start Django backend dev server (:8000)
  frontend:run        Start Vue frontend dev server (:5173)
  run:all             Start backend + frontend + vault watcher in parallel
  superuser           Create a Django admin superuser

Development
  dev:migrate         Run makemigrations + migrate
  dev:test            Run the Django test suite
  dev:makemessages    Update .po translation source files (zh_Hans)
  dev:compilemessages Compile .mo translation files

Docker Compose
  docker:up [env]           Build + start (postgres + backend + nginx)
  docker:down [env]         Stop containers (volumes preserved)
  docker:clean [env]        ⚠️  Destroy containers + volumes + images
  docker:logs [service]     Tail logs (omit service for all)
  docker:shell [service]    Open shell in container (default: backend)
  docker:manage <cmd>       Run Django management command in backend container

Production
  deploy              Automated Nginx + Gunicorn + Systemd deployment (requires sudo)
```

### 4.2 Authentication

SynapseERP uses JWT authentication via `djangorestframework-simplejwt`.

- **`POST /api/auth/login/`** — returns `{access, refresh, user}`
- **`POST /api/auth/refresh/`** — rotates the refresh token
- **`POST /api/auth/logout/`** — blacklists the refresh token

Three roles are supported: `admin`, `editor`, `viewer`. Admins can manage users at **Settings → User Management** in the sidebar.

### 4.3 Attendance Analyzer Rules

The Attendance Analyzer uses a TOML rules file. Priority order:

**Remote URL > Local custom file > Built-in default**

```bash
# Set a remote rules URL
./synapse set-rule "https://your-url/path/to/rules.toml"

# Clear the remote URL (fall back to local/default)
./synapse set-rule
```

For local development, place a `local_rules.toml` in `backend/src/synapse_attendance/engine/rules/` — it is automatically detected and ignored by Git.

### 4.4 Publishing a Dashboard Notification

1. Open the Django admin panel: **http://127.0.0.1:8000/admin/**
2. Under **SYNAPSE DASHBOARD**, click **Add** next to **Notifications**.
3. Enter Markdown content and click **Save**.

The dashboard always displays the most recently updated notification.

### 4.5 Developer Notes

- API contracts: `docs/architecture/plan/10_api_spec.md`
- Architecture decisions: `docs/architecture/background/`
- Codebase map (start here for AI agents): `docs/architecture/plan/13_codebase_map.md`
