<!--
Copyright (c) 2025-present, PotterWhite (themanuknowwhom@outlook.com).
All rights reserved.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.

T-HEAD-GR-V0.8.0-20250910 (English README for SynapseERP)
-->

<div align="center">
  <h2>SynapseERP</h2>
  <p><i>A Modular Django Framework for Data Analysis Tools</i></p>
</div>

<p align="center">
  <img src="./assets/logo.jpg" alt="SynapseERP Logo" width="100%"/>
</p>

<p align="center">
  <a href="https://github.com/potterwhite/SynapseERP/releases"><img src="https://img.shields.io/badge/version-v0.8.0-orange" alt="version"></a>
  <a href="https://github.com/potterwhite/SynapseERP/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="license"></a>
</p>

<p align="center">
  <strong>English</strong> | <a href="./README.zh.md">简体中文</a>
</p>

<p align="center">
  <a href="#1-quick-start">🚀 Quick Start</a> •
  <a href="#2-production-deployment">⚙️ Deployment</a> •
  <a href="#3-appendix">📚 Appendix</a>
</p>

---

# 1. Quick Start

This guide is for getting a local development environment up and running as quickly as possible.

**Prerequisites:**
*   Python 3.8+
*   Git (for cloning)

### Step 1.1: Get the Code

Clone the repository and navigate into the project directory:
```bash
git clone git@github.com:potterwhite/SynapseERP.git
cd SynapseERP
```

### Step 1.2: Prepare the Environment

This project uses a fully automated preparation script.

1.  **Give execution permission to the script:**
    ```bash
    chmod +x run.sh
    ```

2.  **Run the script:**
    ```bash
    ./run.sh prepare
    ```
    This single command handles everything: it creates a Python virtual environment, installs all dependencies, generates a secure `.env` configuration file, and initializes the database.

### Step 1.3: Run the Application

After preparation is complete:

1.  **Create an administrative user:**
    ```bash
    ./run.sh superuser
    ```
    Follow the prompts to create your admin account.

2.  **Run the development server:**
    ```bash
    ./run.sh run
    ```
    You can now access the application at **http://127.0.0.1:8000** and the admin panel at **http://127.0.0.1:8000/admin/**.

---

# 2. Production Deployment

The `./run.sh run` command is for **development only**. For a live production environment, you must use a proper WSGI server (like Gunicorn) and a reverse proxy (like Nginx). This project includes scripts to simplify this process.

### Step 2.1: Generate Configuration Files

Run the interactive configuration generator on your production server:
```bash
./run.sh deploy:config
```
The script will ask for:
1.  **Your server's domain name or IP address.**
2.  **The Linux user that will run the application service.**

It will then generate two production-ready files in your project root: `synapse.service` (for Systemd/Gunicorn) and `synapse_nginx.conf` (for Nginx).

### Step 2.2: Execute the Deployment Instructions

After generating the files, the script will print a clear, step-by-step list of commands. As a user with `sudo` privileges on your server, you will need to follow these instructions to:

1.  **Collect static files** for Nginx to serve directly.
2.  **Move the generated service and Nginx files** to the appropriate system directories.
3.  **Enable and start the services.**
4.  **Critically, update your `.env` file for production** by setting `DJANGO_DEBUG='False'` and updating `DJANGO_ALLOWED_HOSTS` with your domain/IP.

The script's output provides the exact commands for you to copy and paste.

---

# 3. Appendix

### 3.1 Attendance Analyzer Rules

The Attendance Analyzer is controlled by a TOML rule file. The system uses a 3-tier priority system to determine which rule file to load:

**`Remote URL > Local Custom File > Default File`**

This provides maximum flexibility.

#### Method A (Production): Using a Remote URL
Ideal for providing a specific ruleset to a user without changing the code.

*   **To set a remote rule URL:**
    ```bash
    # Replace the URL with your own Gist or raw file URL
    ./run.sh set-rule "https://your-url/path/to/rules.toml"
    ```
    This command saves the URL to your local `.env` file.

*   **To clear the remote rule URL** (and revert to local or default rules):
    ```bash
    ./run.sh set-rule
    ```

#### Method B (Local Development): Using a Local File
Useful for offline development or quickly testing rule changes.

1.  Create a file named `local_rules.toml` inside `src/synapse_attendance/engine/rules/`.
2.  You can copy the contents of `default_rules.toml` into it as a starting point.

The application will automatically use this file if it exists and no remote URL is set. This file is ignored by Git.

#### Method C (Default): Out-of-the-Box Rules
If neither a remote URL nor a local file is found, the system falls back to using `src/synapse_attendance/engine/rules/default_rules.toml`.

### 3.2 Developer Commands

These commands are for contributors or developers who want to **modify the application's source code or database structure**. Regular users **do not need** to interact with these commands for daily use.

*   **`./run.sh dev:migrate`**
    *   **What it does:** Creates and applies database migrations.
    *   **When to use:** Use this command **after you have modified a `models.py` file** to update the database schema.

*   **`./run.sh dev:makemessages`**
    *   **What it does:** Scans all source code and templates for translatable strings and updates the `.po` translation files.
    *   **When to use:** Use this **after adding or changing user-facing text** that needs to be translated.

*   **`./run.sh dev:compilemessages`**
    *   **What it does:** Compiles the text-based `.po` files into binary `.mo` files that Django uses for translations.
    *   **When to use:** Use this after `dev:makemessages` or after pulling translation updates from the repository.

*   **`./run.sh dev:test`**
    *   **What it does:** Runs the project's automated test suite.
    *   **When to use:** Use this frequently **while developing new features** to ensure you haven't broken existing functionality.

---
