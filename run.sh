#!/bin/bash

# Copyright (c) 2025-present, PotterWhite (themanuknowwhom@outlook.com).
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
# T-HEAD-GR-V0.1.0-20250905 (Utility script for the Synapse Framework)

# ==============================================================================
# Synapse Framework Project Runner
# ==============================================================================
# This script provides a consistent interface for development and testing tasks
# for the Synapse Framework Django project.
#
# It ensures that the correct virtual environment is used and standardizes
# command execution for common development workflows.
#
# Author: PotterWhite
# Version: v1.0.0
# ==============================================================================

set -e

# --- Configuration ---
# This section centralizes key paths and commands for easy modification.
VENV_DIR=".venv"
PYTHON_CMD="python3"
REQUIREMENTS_FILE="requirements.txt"
# IMPORTANT: Your manage.py is inside the 'tests' directory.
DJANGO_MANAGE_PY="tests/manage.py"

# --- Helper Functions ---
# These functions provide reusable logic for logging and environment activation.

# fn_log: Prints a formatted message with color.
# Usage: fn_log "Your message" "green"
fn_log() {
    local message="$1"
    local color_name="$2"
    local color_code=""
    case "$color_name" in
    green) color_code="\033[0;32m" ;;
    yellow) color_code="\033[0;33m" ;;
    red) color_code="\033[0;31m" ;;
    blue) color_code="\033[0;34m" ;;
    *) color_code="\033[0m" ;;
    esac
    local color_reset="\033[0m"
    echo -e "${color_code}${message}${color_reset}"
}

# fn_activate_venv: Checks for and activates the Python virtual environment.
fn_activate_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        fn_log "❌ Virtual environment not found. Please run './run.sh prepare' first." "red"
        exit 1
    fi
    source "$VENV_DIR/bin/activate"
    fn_log "✅ Virtual environment activated." "green"
}

# --- Main Functions ---
# Each function corresponds to a command that can be passed to the script.

# fn_prepare_env: Sets up the project for the first time.
fn_prepare_env() {
    fn_log "🛠️  Starting project preparation..." "blue"
    if ! command -v "$PYTHON_CMD" &>/dev/null; then
        fn_log "❌ Error: '$PYTHON_CMD' could not be found." "red"
        exit 1
    fi
    fn_log "   - Found $($PYTHON_CMD --version)" "green"

    if [ ! -d "$VENV_DIR" ]; then
        fn_log "   - Creating virtual environment in './$VENV_DIR'..." "yellow"
        "$PYTHON_CMD" -m venv "$VENV_DIR"
    else
        fn_log "   - Virtual environment already exists." "green"
    fi

    source "$VENV_DIR/bin/activate"

    fn_log "   - Upgrading pip..." "yellow"
    pip install --upgrade pip

    if [ -f "$REQUIREMENTS_FILE" ]; then
        fn_log "   - Installing dependencies from '$REQUIREMENTS_FILE'..." "yellow"
        pip install -r "$REQUIREMENTS_FILE"
    else
        fn_log "   - Warning: '$REQUIREMENTS_FILE' not found. Skipping dependency installation." "yellow"
    fi
    fn_log "🎉 Preparation complete! You can now use other commands." "green"
}

# fn_run_dev_server: Starts the Django development server.
fn_run_dev_server() {
    fn_log "🚀 Starting Django development server..." "blue"
    fn_log "   Access it at http://127.0.0.1:8000" "yellow"
    "$PYTHON_CMD" "$DJANGO_MANAGE_PY" runserver 0.0.0.0:8000
}

# fn_run_migrations: Generates and applies database migrations.
fn_run_migrations() {
    fn_log "📦 Applying database migrations..." "blue"
    fn_log "   - Creating new migration files..." "yellow"
    "$PYTHON_CMD" "$DJANGO_MANAGE_PY" makemigrations
    fn_log "   - Applying migrations to the database..." "yellow"
    "$PYTHON_CMD" "$DJANGO_MANAGE_PY" migrate
    fn_log "✅ Migrations complete." "green"
}

# fn_run_tests: Executes the project's test suite.
fn_run_tests() {
    fn_log "🧪 Running tests..." "blue"
    "$PYTHON_CMD" "$DJANGO_MANAGE_PY" test
}

# fn_create_superuser: Creates an admin user.
fn_create_superuser() {
    fn_log "👤 Creating a new superuser (admin)..." "blue"
    "$PYTHON_CMD" "$DJANGO_MANAGE_PY" createsuperuser
}

# fn_make_translations: Scans source files and updates .po translation files.
fn_make_translations() {
    fn_log "🌍 Updating translation source files (.po)..." "blue"
    # The -l flag specifies the language. zh_Hans comes from your directory structure.
    "$PYTHON_CMD" "$DJANGO_MANAGE_PY" makemessages -l zh_Hans
    fn_log "✅ Translation source files updated." "green"
}

# fn_compile_translations: Compiles .po files into binary .mo files for use.
fn_compile_translations() {
    fn_log "🌍 Compiling translation files (.mo)..." "blue"
    "$PYTHON_CMD" "$DJANGO_MANAGE_PY" compilemessages
    fn_log "✅ Translation files compiled." "green"
}

# fn_show_help: Displays the help message.
fn_show_help() {
    echo "Usage: ./run.sh [command]"
    echo ""
    echo "A runner script for the Synapse Framework Django project."
    echo ""
    echo "Commands:"
    echo "  prepare         Sets up the virtual environment and installs dependencies."
    echo "  run             Starts the Django development server."
    echo "  test            Runs the project's test suite."
    echo "  migrate         Creates and applies database migrations."
    echo "  superuser       Creates a new administrative user."
    echo "  makemessages    Updates translation source files (*.po)."
    echo "  compilemessages Compiles translation files for use (*.mo)."
    echo "  help            Shows this help message."
    echo ""
}

# --- Main Logic ---
# This is the entry point of the script.
main() {
    local command="$1"

    # Commands that do not require an active venv
    if [ "$command" == "prepare" ]; then
        fn_prepare_env
        exit 0
    fi
    if [ "$command" == "help" ] || [ "$command" == "--help" ] || [ "$command" == "-h" ]; then
        fn_show_help
        exit 0
    fi

    # All subsequent commands require the virtual environment to be active
    fn_activate_venv

    case "$command" in
    run)
        fn_run_dev_server
        ;;
    test)
        fn_run_tests
        ;;
    migrate)
        fn_run_migrations
        ;;
    superuser)
        fn_create_superuser
        ;;
    makemessages)
        fn_make_translations
        ;;
    compilemessages)
        fn_compile_translations
        ;;
    *)
        fn_log "❌ Error: Unknown command '$command'." "red"
        fn_show_help
        exit 1
        ;;
    esac
}

# --- Script Execution ---
# Ensures a command is provided, otherwise shows help.
if [ -z "$1" ]; then
    fn_show_help
    exit 1
fi

main "$@"