#!/bin/bash
# Copyright (c) 2025-present, PotterWhite (themanuknowwhom@outlook.com).
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
# T-HEAD-GR-V0.8.0-20250910 (Orchestration script for SynapseERP)

# ==============================================================================
# Synapse Framework Project Orchestrator (v3.4 - Final with IP Auto-Detection)
# ==============================================================================
# Provides a comprehensive interface for development, setup, and deployment.
# ==============================================================================

set -e

# --- Configuration ---
VENV_DIR=".venv"; PYTHON_CMD="python3"; REQUIREMENTS_FILE="requirements.txt"
ENV_FILE=".env"; DJANGO_MANAGE_PY="manage.py"; SERVICE_NAME="synapse"

# --- Helper Functions ---
fn_log() {
    local message="$1"; local color_name="$2"; local color_code=""
    case "$color_name" in green) color_code="\033[0;32m" ;; yellow) color_code="\033[0;33m" ;; red) color_code="\033[0;31m" ;; blue) color_code="\033[0;34m" ;; *) color_code="\033[0m" ;; esac
    local color_reset="\033[0m"; echo -e "${color_code}${message}${color_reset}"
}

fn_activate_venv() {
    if [ ! -d "$VENV_DIR" ]; then fn_log "❌ Venv not found. Run './run.sh prepare' first." "red"; exit 1; fi
    source "$VENV_DIR/bin/activate"
}

# --- Main Functions ---

fn_prepare_env() {
    fn_log "🛠️  Starting project preparation (one-time setup)..." "blue"
    if [ -d "$VENV_DIR" ]; then fn_log "   - Virtual environment already exists." "green"; else
        fn_log "   - Creating virtual environment..." "yellow"; "$PYTHON_CMD" -m venv "$VENV_DIR"
    fi
    source "$VENV_DIR/bin/activate"
    fn_log "   - Installing/updating dependencies..." "yellow"
    pip install --upgrade pip; pip install -r "$REQUIREMENTS_FILE"; pip install -e .
    if [ ! -f "$ENV_FILE" ]; then
        fn_log "   - Generating .env file with SECRET_KEY..." "yellow"
        local new_key=$("$PYTHON_CMD" -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
        echo "DJANGO_SECRET_KEY='$new_key'" > "$ENV_FILE"; echo "DJANGO_DEBUG='True'" >> "$ENV_FILE"; echo "DJANGO_ALLOWED_HOSTS='127.0.0.1,localhost'" >> "$ENV_FILE"
    fi
    fn_log "   - Initializing database..." "yellow"; "$PYTHON_CMD" "$DJANGO_MANAGE_PY" migrate
    fn_log "🎉 Preparation complete!" "green"
}

fn_run_dev_server() {
    fn_log "🚀 Starting Django development server at http://0.0.0.0:8000" "blue"
    "$PYTHON_CMD" "$DJANGO_MANAGE_PY" runserver 0.0.0.0:8000
}

fn_create_superuser() {
    fn_log "👤 Creating a new superuser (admin)..." "blue"
    "$PYTHON_CMD" "$DJANGO_MANAGE_PY" createsuperuser
}

fn_set_rule_url() {
    local url="$1"; local var_name="ATTENDANCE_ANALYZER_RULE_URL"
    if [ -z "$url" ]; then
        if grep -q "^${var_name}=" "$ENV_FILE" 2>/dev/null; then sed -i "/^${var_name}=/d" "$ENV_FILE"; fi
        fn_log "✅ Remote rule URL cleared." "green"
    else
        if grep -q "^${var_name}=" "$ENV_FILE" 2>/dev/null; then sed -i "s|^${var_name}=.*|${var_name}='${url}'|" "$ENV_FILE"; else echo "${var_name}='${url}'" >> "$ENV_FILE"; fi
        fn_log "✅ Remote rule URL set to: $url" "green"
    fi
}

fn_deploy() {
    fn_log "🚢  Starting automated deployment..." "blue"
    if ! command -v nginx &> /dev/null; then fn_log "❌ Nginx not found. Please install it (e.g., sudo apt install nginx)." "red"; exit 1; fi
    if [ "$EUID" -ne 0 ]; then fn_log "❌ This command requires sudo. Please run with 'sudo ./run.sh deploy'." "red"; exit 1; fi

    read -p "Enter the domain name for this server (leave blank to use local IPs): " server_name
    read -p "Enter the non-root Linux user for the service (e.g., $(whoami)): " service_user
    service_user=${service_user:-$(whoami)}

    local detected_ips=$(hostname -I | tr ' ' ',')
    local final_allowed_hosts="127.0.0.1,localhost,${detected_ips%,}"
    if [ -n "$server_name" ]; then final_allowed_hosts="${server_name},${final_allowed_hosts}"; fi

    fn_log "   Step 1: Checking user permissions..." "yellow"
    if ! groups "$service_user" | grep -q '\bwww-data\b'; then
        read -p "   [WARNING] User '$service_user' needs to be in 'www-data' group. Add now? [Y/n] " -n 1 -r; echo
        if [[ $REPLY =~ ^[Yy]$ || -z $REPLY ]]; then usermod -aG www-data "$service_user"; fn_log "   ✅ User added. [IMPORTANT] You must log out and back in, then re-run deploy." "red"; exit 0; fi
    fi

    local project_path=$(pwd)
    fn_log "   Step 2: Preparing environment..." "yellow"
    sudo -u "$service_user" bash -c "source ${project_path}/.venv/bin/activate && python ${project_path}/manage.py collectstatic --noinput"

    fn_log "   Step 3: Installing Systemd socket and service..." "yellow"
    sed -e "s|__USER__|${service_user}|g" "deploy/synapse.socket.template" > "/etc/systemd/system/${SERVICE_NAME}.socket"
    sed -e "s|__USER__|${service_user}|g" -e "s|__PROJECT_PATH__|${project_path}|g" "deploy/synapse.service.template" > "/etc/systemd/system/${SERVICE_NAME}.service"

    fn_log "   Step 4: Installing Nginx config..." "yellow"
    local nginx_display_name=${server_name:-$(hostname -I | awk '{print $1}')}
    sed -e "s|__SERVER_NAME__|${nginx_display_name}|g" -e "s|__PROJECT_PATH__|${project_path}|g" "deploy/nginx.conf.template" > "/etc/nginx/sites-available/${SERVICE_NAME}"

    fn_log "   Step 5: Enabling and restarting services..." "yellow"
    rm -f /etc/nginx/sites-enabled/default
    ln -sf "/etc/nginx/sites-available/${SERVICE_NAME}" "/etc/nginx/sites-enabled/"
    systemctl daemon-reload; systemctl enable --now "${SERVICE_NAME}.socket"; systemctl restart "${SERVICE_NAME}.service"; nginx -t && systemctl restart nginx

    fn_log "🎉 Deployment complete!" "green"
    fn_log "   - Updating .env for production..." "yellow"
    sed -i "s/^DJANGO_DEBUG=.*/DJANGO_DEBUG='False'/" "$ENV_FILE"
    sed -i "s/^DJANGO_ALLOWED_HOSTS=.*/DJANGO_ALLOWED_HOSTS='${final_allowed_hosts}'/" "$ENV_FILE"
    fn_log "   - DJANGO_DEBUG set to 'False'."
    fn_log "   - DJANGO_ALLOWED_HOSTS updated to '${final_allowed_hosts}'."
    fn_log "   Your application should be live at http://${nginx_display_name}"
}

fn_show_help() {
    echo "Usage: ./run.sh [command]"; echo ""
    echo "Setup & Development:"
    echo "  prepare         (One-time) Sets up the development environment."
    echo "  run             Starts the Django development server."
    echo "  superuser       Creates a new administrative user."
    echo "  set-rule [URL]  Sets or clears the remote attendance rules URL."; echo ""
    echo "Production Deployment:"
    echo "  deploy          (Requires sudo) Automates the deployment process to Systemd and Nginx."; echo ""
    echo "Development Utilities:"
    echo "  dev:migrate     Creates and applies database migrations."
    echo "  dev:test        Runs the project's test suite."; echo ""
}

main() {
    local command="$1"
    if [[ -z "$command" || "$command" == "help" ]]; then fn_show_help; exit 0; fi
    if [[ "$command" == "prepare" ]]; then fn_prepare_env; exit 0; fi
    if [[ "$command" == "deploy" ]]; then fn_deploy; exit 0; fi

    fn_activate_venv

    case "$command" in
        run) fn_run_dev_server ;;
        superuser) fn_create_superuser ;;
        set-rule) fn_set_rule_url "$2" ;;
        dev:migrate) "$PYTHON_CMD" "$DJANGO_MANAGE_PY" makemigrations && "$PYTHON_CMD" "$DJANGO_MANAGE_PY" migrate ;;
        dev:test) "$PYTHON_CMD" "$DJANGO_MANAGE_PY" test ;;
        *) fn_log "❌ Error: Unknown command '$command'." "red"; fn_show_help; exit 1 ;;
    esac
}

main "$@"