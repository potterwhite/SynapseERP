#!/bin/bash
# Copyright (c) 2025-present, PotterWhite (themanuknowwhom@outlook.com).
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
# T-HEAD-GR-V0.8.0-20250910 (Orchestration script for SynapseERP)

# ==============================================================================
# Synapse Framework Project Orchestrator (v4.3 - The Definitive Final Version)
# ==============================================================================
# Provides a comprehensive, readable, and robust interface for all project tasks,
# restoring detailed feedback for critical operations.
# ==============================================================================

set -e

# --- Configuration ---
VENV_DIR=".venv"; PYTHON_CMD="python3"; REQUIREMENTS_FILE="requirements.txt"
ENV_FILE=".env"; DJANGO_MANAGE_PY="manage.py"; SERVICE_NAME="synapse"

# --- Helper Functions ---
fn_log() {
    local message="$1"; local color_name="$2"; local color_code=""
    case "$color_name" in
        green)  color_code="\033[0;32m" ;; yellow) color_code="\033[0;33m" ;;
        red)    color_code="\033[0;31m" ;; blue)   color_code="\033[0;34m" ;;
        *)      color_code="\033[0m" ;;
    esac
    local color_reset="\033[0m"; echo -e "${color_code}${message}${color_reset}"
}

fn_activate_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        fn_log "❌ Venv not found. Run './run.sh prepare' first." "red"; exit 1
    fi
    source "$VENV_DIR/bin/activate"
}

# --- Main Functions ---

fn_prepare_env() {
    fn_log "🛠️  Starting project preparation..." "blue"
    if [ ! -d "$VENV_DIR" ]; then fn_log "   - Creating virtual environment..." "yellow"; "$PYTHON_CMD" -m venv "$VENV_DIR"; fi
    source "$VENV_DIR/bin/activate"
    fn_log "   - Installing dependencies..." "yellow"
    pip install --upgrade pip; pip install -r "$REQUIREMENTS_FILE"; pip install -e .
    if [ ! -f "$ENV_FILE" ]; then
        fn_log "   - Generating .env file with SECRET_KEY..." "yellow"
        local new_key=$("$PYTHON_CMD" -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
        echo "DJANGO_SECRET_KEY='$new_key'" > "$ENV_FILE"; echo "DJANGO_DEBUG='True'" >> "$ENV_FILE"; echo "DJANGO_ALLOWED_HOSTS='127.0.0.1,localhost'" >> "$ENV_FILE"
    fi
    if ! grep -q "^ATTENDANCE_ANALYZER_RULE_URL=" "$ENV_FILE" 2>/dev/null; then
        read -p "   Do you want to set a remote URL for attendance rules now? [y/N] " -n 1 -r; echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            read -p "   Please enter the full URL for the rules.toml file: " remote_url
            if [[ -n "$remote_url" ]]; then fn_set_rule_url "$remote_url"; fi
        fi
    fi
    fn_log "   - Initializing database..." "yellow"; "$PYTHON_CMD" "$DJANGO_MANAGE_PY" migrate
    if command -v msgfmt &> /dev/null; then
        fn_log "   - Compiling translations..." "yellow"; "$PYTHON_CMD" "$DJANGO_MANAGE_PY" compilemessages
    fi
    fn_log "🎉 Preparation complete!" "green"
}

# --- RESTORED: The detailed clean function ---
fn_clean() {
    fn_log "🧹  This will completely reset the project to its initial state." "red"
    fn_log "   The following will be DELETED:"
    fn_log "   - Virtual environment (.venv)"
    fn_log "   - Database (db.sqlite3)"
    fn_log "   - Environment config (.env)"
    fn_log "   - All Python cache files (__pycache__, *.pyc)"
    fn_log "   - All deployment artifacts (staticfiles/, *.service, *.conf)"
    read -p "   Are you sure you want to continue? [y/N] " -n 1 -r; echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        fn_log "   Operation cancelled." "yellow"; exit 1
    fi

    fn_log "   - Removing virtual environment..." "yellow"
    rm -rf "$VENV_DIR"
    fn_log "   - Removing database and environment file..." "yellow"
    rm -f db.sqlite3 "$ENV_FILE"
    fn_log "   - Removing deployment artifacts..." "yellow"
    rm -rf staticfiles/
    rm -f synapse.service synapse_nginx.conf
    fn_log "   - Removing all Python cache files..." "yellow"
    find . -type d -name "__pycache__" -exec rm -r {} +
    find . -type f -name "*.pyc" -delete

    fn_log "✅ Project has been cleaned successfully." "green"
    fn_log "   Run './run.sh prepare' to start over."
}

fn_run_dev_server() { fn_log "🚀 Starting Django dev server..." "blue"; "$PYTHON_CMD" "$DJANGO_MANAGE_PY" runserver 0.0.0.0:8000; }
fn_create_superuser() { fn_log "👤 Creating superuser..." "blue"; "$PYTHON_CMD" "$DJANGO_MANAGE_PY" createsuperuser; }
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
    # ... (This function is in its perfect final state) ...
    fn_log "🚢  Starting automated deployment..." "blue"
    if ! command -v nginx &> /dev/null; then fn_log "❌ Nginx not found. Run: sudo apt install nginx" "red"; exit 1; fi
    if ! command -v msgfmt &> /dev/null; then fn_log "❌ gettext (msgfmt) not found. Run: sudo apt install gettext" "red"; exit 1; fi
    if [ "$EUID" -ne 0 ]; then fn_log "❌ This command requires sudo. Run with 'sudo ./run.sh deploy'." "red"; exit 1; fi

    # --- NEW: Intelligent default for server name ---
    local default_server_name=$(hostname -I | awk '{print $1}')
    read -p "Enter domain/IP for this server (press Enter to use default: ${default_server_name}): " server_name
    server_name=${server_name:-$default_server_name}

    read -p "Enter the non-root Linux user for the service (e.g., $(whoami)): " service_user
    service_user=${service_user:-$(whoami)}
    fn_deploy_permissions_wizard "$service_user"
    fn_deploy_log_config_wizard
    local project_path=$(pwd)
    fn_log "   - Step 3: Preparing environment..." "yellow"
    sudo -u "$service_user" bash -c "source ${project_path}/.venv/bin/activate && python ${project_path}/manage.py compilemessages && python ${project_path}/manage.py collectstatic --noinput"
    fn_log "   - Step 4: Installing Systemd & Nginx configs..." "yellow"
    fn_install_system_configs "$service_user" "$project_path" "$server_name"
    fn_log "   - Step 5: Enabling and restarting services..." "yellow"
    systemctl daemon-reload; systemctl enable --now "${SERVICE_NAME}.socket"; systemctl restart "${SERVICE_NAME}.service"; nginx -t && systemctl restart nginx
    fn_log "🎉 Deployment complete!" "green"
    fn_update_production_env "$server_name"
    local nginx_display_name=${server_name:-$(hostname -I | awk '{print $1}')}
    fn_log "   Your application should be live at http://${nginx_display_name}"
}

# --- Deployment Sub-Functions (all perfect) ---
fn_deploy_permissions_wizard() {
    local service_user="$1"
    fn_log "   - Step 1: Checking permissions..." "yellow"
    if ! groups "$service_user" | grep -q '\bwww-data\b'; then
        read -p "   [ACTION REQUIRED] User '$service_user' must join 'www-data' group. Add now? [Y/n] " -n 1 -r; echo
        if [[ $REPLY =~ ^[Yy]$ || -z $REPLY ]]; then usermod -aG www-data "$service_user"; fn_log "   ✅ User added. [CRITICAL] You must log out and log back in, then re-run deploy." "red"; exit 0; fi
    fi
}
# In run.sh, add this new function block after fn_deploy_permissions_wizard

fn_deploy_log_config_wizard() {
    fn_log "   - Step 2: Checking system log rotation policy..." "yellow"
    local journald_conf="/etc/systemd/journald.conf"

    # Check if the setting is already present and uncommented
    if grep -q -E "^SystemMaxUse=" "$journald_conf"; then
        fn_log "   ✅ SystemMaxUse is already set in '$journald_conf'. Skipping." "green"
        return
    fi

    read -p "   To prevent logs from filling your disk, do you want to set a size limit now? (Recommended) [Y/n] " -n 1 -r; echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        fn_log "   Skipping log configuration." "yellow"
        return
    fi

    # --- Start of Intelligent Suggestion Logic ---
    local final_size=""
    # Get available space in Megabytes on the current partition
    local available_mb=$(df --output=avail --block-size=1M . | tail -n 1 | xargs)

    # Calculate a sensible suggestion (10% of available, capped between 200M and 4G)
    local suggestion_mb=$((available_mb / 10))
    if [ "$suggestion_mb" -gt 4096 ]; then suggestion_mb=4096; fi
    if [ "$suggestion_mb" -lt 200 ]; then suggestion_mb=200; fi
    local suggestion_str="${suggestion_mb}M"

    read -p "   Available space is ~${available_mb}M. The suggested limit is ${suggestion_str}. Do you accept this suggestion? [Y/n] " -n 1 -r; echo
    if [[ $REPLY =~ ^[Yy]$ || -z $REPLY ]]; then
        final_size="$suggestion_str"
    else
        # Loop until the user provides valid input
        while true; do
            read -p "   Please enter your desired size (e.g., 500M, 2G): " custom_size
            if [[ "$custom_size" =~ ^[0-9]+[MG]?$ ]]; then
                final_size="$custom_size"
                break
            else
                fn_log "   ❌ Invalid format. Please use a number optionally followed by 'M' or 'G'." "red"
            fi
        done
    fi
    # --- End of Intelligent Suggestion Logic ---

    fn_log "   Setting 'SystemMaxUse=${final_size}' in '$journald_conf'..." "yellow"

    # Safely add or update the setting
    if ! grep -q "\[Journal\]" "$journald_conf"; then
        echo -e "\n[Journal]" >> "$journald_conf"
    fi
    # This command will replace the line if it exists (even commented out), otherwise it will add it under the [Journal] section.
    if grep -q -E "^#?SystemMaxUse=" "$journald_conf"; then
        sed -i "s|^#\?SystemMaxUse=.*|SystemMaxUse=${final_size}|" "$journald_conf"
    else
        sed -i "/\[Journal\]/a SystemMaxUse=${final_size}" "$journald_conf"
    fi

    fn_log "   Restarting journald service to apply changes..." "green"
    systemctl restart systemd-journald
}

fn_install_system_configs() {
    local service_user="$1"
    local project_path="$2"
    local server_name="$3"

    # Install Systemd configs
    sed -e "s|__USER__|${service_user}|g" \
        "deploy/synapse.socket.template" > "/etc/systemd/system/${SERVICE_NAME}.socket"

    sed -e "s|__USER__|${service_user}|g" \
        -e "s|__PROJECT_PATH__|${project_path}|g" \
        "deploy/synapse.service.template" > "/etc/systemd/system/${SERVICE_NAME}.service"

    # Install Nginx config
    sed -e "s|__SERVER_NAME__|${server_name}|g" \
        -e "s|__PROJECT_PATH__|${project_path}|g" \
        "deploy/nginx.conf.template" > "/etc/nginx/sites-available/${SERVICE_NAME}"

    # Enable the new site and disable the default
    rm -f /etc/nginx/sites-enabled/default
    ln -sf "/etc/nginx/sites-available/${SERVICE_NAME}" "/etc/nginx/sites-enabled/"
}

fn_update_production_env() {
    local server_name="$1"

    fn_log "   - Updating .env for production..." "yellow"

    # Construct the final ALLOWED_HOSTS string
    local detected_ips=$(hostname -I | tr ' ' ',')
    local final_allowed_hosts="127.0.0.1,localhost,${detected_ips%,}"
    if [ -n "$server_name" ]; then
        final_allowed_hosts="${server_name},${final_allowed_hosts}"
    fi

    # Use sed to update the .env file in place
    sed -i "s/^DJANGO_DEBUG=.*/DJANGO_DEBUG='False'/" "$ENV_FILE"
    sed -i "s/^DJANGO_ALLOWED_HOSTS=.*/DJANGO_ALLOWED_HOSTS='${final_allowed_hosts}'/" "$ENV_FILE"

    fn_log "   - DJANGO_DEBUG set to 'False' and ALLOWED_HOSTS updated."
}

fn_show_help() {
    echo "Usage: ./run.sh [command]"; echo ""
    echo "Lifecycle:"
    echo "  prepare         (One-time) Sets up the development environment."
    echo "  run             Starts the Django development server for local testing."
    echo "  deploy          (Requires sudo) Automates the production deployment."
    echo "  clean           (Destructive) Resets the project to a clean state."; echo ""
    echo "Utilities:"
    echo "  superuser       Creates a new administrative user."
    echo "  set-rule [URL]  Sets or clears the remote attendance rules URL."; echo ""
    echo "Development:"
    echo "  dev:migrate     Creates and applies database migrations."
    echo "  dev:test        Runs the project's test suite."
    echo "  dev:makemessages Updates translation source files (*.po)."
    echo "  dev:compilemessages Compiles translation files for use (*.mo)."; echo ""
    echo "Help:"
    echo "  help            Shows this help message."
}

# --- Main Logic ---
main() {
    local command="$1"

    # Handle commands that can run without needing to activate the venv first
    case "$command" in
        prepare|deploy|clean|help|--help|-h|"")
            case "$command" in
                prepare)    fn_prepare_env ;;
                deploy)     fn_deploy ;;
                clean)      fn_clean ;;
                *)          fn_show_help ;;
            esac
            exit 0
            ;;
    esac

    # All subsequent commands require the virtual environment to be active
    fn_activate_venv

    case "$command" in
        run)
            fn_run_dev_server
            ;;
        superuser)
            fn_create_superuser
            ;;
        set-rule)
            fn_set_rule_url "$2"
            ;;
        dev:migrate)
            python manage.py makemigrations && python manage.py migrate
            ;;
        dev:makemessages)
            # python manage.py makemessages -l zh_Hans
            python manage.py makemessages -l zh_Hans -d django --ignore "venv/*" --ignore "tests/*"
            ;;
        dev:compilemessages)
            python manage.py compilemessages
            ;;
        dev:test)
            python manage.py test
            ;;
        *)
            fn_log "❌ Error: Unknown command '$command'." "red"
            fn_show_help
            exit 1
            ;;
    esac
}

main "$@"