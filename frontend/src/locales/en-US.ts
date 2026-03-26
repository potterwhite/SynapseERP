// Copyright (c) 2026 PotterWhite — MIT License

/**
 * English (US) locale for SynapseERP.
 *
 * Adding a new language:
 *   1. Copy this file as <lang>.ts  (e.g. ja-JP.ts)
 *   2. Translate every string value — keep all keys identical
 *   3. Import and register in src/i18n.ts
 *   4. Add the language option in Header.vue's langOptions array
 */
export default {
  // ─── Common ────────────────────────────────────────────────────────────────
  common: {
    save: 'Save',
    cancel: 'Cancel',
    delete: 'Delete',
    edit: 'Edit',
    confirm: 'Confirm',
    create: 'Create',
    search: 'Search',
    loading: 'Loading…',
    retry: 'Retry',
    unknown_error: 'Unknown error',
    never: 'Never',
    none: 'None',
  },

  // ─── Header ────────────────────────────────────────────────────────────────
  header: {
    logout: 'Logout',
    switch_to_light: 'Switch to light mode',
    switch_to_dark: 'Switch to dark mode',
    language: 'Language',
  },

  // ─── Sidebar / Navigation ──────────────────────────────────────────────────
  nav: {
    dashboard: 'Dashboard',
    projects: 'Projects',
    gantt: 'Gantt Chart',
    sync: 'Sync Settings',
    attendance: 'Attendance',
    bom: 'BOM Analyzer',
    users: 'User Management',
  },

  // ─── Dashboard ─────────────────────────────────────────────────────────────
  dashboard: {
    title: 'Dashboard',
    modules: 'Modules',
  },

  // ─── PM — Project List ─────────────────────────────────────────────────────
  projects: {
    title: 'Project Management',
    meeting_mode: 'Meeting Mode',
    exit_meeting: 'Exit Meeting',
    meeting_mode_tip: 'Meeting mode active — personal projects are hidden',
    meeting_mode_hint: 'Meeting mode: hide projects tagged "personal"',
    new_project: 'New Project',
    delete_selected: 'Delete ({n})',
    search_placeholder: 'Search projects…',
    filter_status: 'Status filter',
    filter_tag: 'Filter by tag…',
    sync_vault: 'Sync Vault',
    status: {
      active: 'Active',
      archived: 'Archived',
      on_hold: 'On Hold',
      all: 'All',
    },
    columns: {
      project: 'Project',
      status: 'Status',
      tasks: 'Tasks',
      hours: 'Hours',
      deadline: 'Deadline',
      last_sync: 'Last Sync',
    },
    stats: {
      total_projects: 'Total Projects',
      active: 'Active',
      total_tasks: 'Total Tasks',
      hours_logged: 'Hours Logged',
    },
    delete_confirm_title: 'Delete Project',
    delete_confirm_content: 'Are you sure you want to delete "{name}"? This action cannot be undone.',
    bulk_delete_confirm_title: 'Delete {count} Projects',
    bulk_delete_confirm_content: 'Are you sure you want to delete {count} selected projects? This action cannot be undone.',
    delete_success: 'Project "{name}" deleted',
    bulk_delete_success: '{count} projects deleted',
    load_error: 'Failed to load projects',
  },

  // ─── PM — Project Form Modal ───────────────────────────────────────────────
  project_form: {
    create_title: 'New Project',
    edit_title: 'Edit Project',
    name_label: 'Project Name',
    name_placeholder: 'Enter project name',
    name_required: 'Project name is required',
    status_label: 'Status',
    deadline_label: 'Deadline',
    tags_label: 'Tags',
    tags_placeholder: 'Type a tag and press Enter',
  },

  // ─── PM — Task View ────────────────────────────────────────────────────────
  tasks: {
    all_projects: 'All Projects',
    new_task: 'New Task',
    delete_selected: 'Delete ({n})',
    edit_task: 'Edit Task',
    search_placeholder: 'Search tasks…',
    status: {
      all: 'All Statuses',
      todo: 'To Do',
      doing: 'In Progress',
      done: 'Done',
      cancelled: 'Cancelled',
    },
    priority: {
      all: 'All Priorities',
      high: 'High',
      medium: 'Medium',
      low: 'Low',
    },
    columns: {
      task: 'Task',
      status: 'Status',
      priority: 'Priority',
      deadline: 'Deadline',
      est_actual: 'Est / Actual',
    },
    form: {
      name_label: 'Task Name',
      name_placeholder: 'Enter task name',
      name_required: 'Task name is required',
      status_label: 'Status',
      status_required: 'Status is required',
      priority_label: 'Priority',
      priority_required: 'Priority is required',
      deadline_label: 'Deadline',
      est_hours_label: 'Est. Hours',
      est_hours_placeholder: 'e.g. 8',
      description_label: 'Description',
      description_placeholder: 'Task description (written to vault)',
    },
    delete_confirm_title: 'Delete Task',
    delete_confirm_content: 'Delete "{name}"? This action cannot be undone.',
    bulk_delete_confirm_title: 'Delete {count} Tasks',
    bulk_delete_confirm_content: 'Delete {count} selected tasks? This cannot be undone.',
    delete_success: 'Task "{name}" deleted',
    bulk_delete_success: '{count} tasks deleted',
    create_success: 'Task created and written to vault',
    update_success: 'Task updated and written to vault',
  },

  // ─── PM — Gantt ────────────────────────────────────────────────────────────
  gantt: {
    title: 'Gantt Chart',
    all_projects: 'All projects',
    no_tasks: 'No tasks to display',
    tasks_count: '{n} tasks',
    view: 'View:',
    update_dates_title: 'Update Task Dates?',
    update_dates_content: 'Move {name} to\n{start} → {end}?',
    update_success: 'Task dates updated',
    update_failed: 'Update failed',
    load_error: 'Failed to load Gantt data',
  },

  // ─── Sync Settings ─────────────────────────────────────────────────────────
  sync: {
    title: 'Obsidian Sync',
    subtitle: 'Bidirectional sync between the database and your Obsidian vault',
    import_btn: 'Import from Vault',
    export_btn: 'Export to Vault',
    filter_card_title: 'Import Filter (optional)',
    filter_placeholder_blur: 'Filter by project name keywords (leave empty = import all)',
    filter_placeholder_focus: 'e.g. AI, Quantitative, Demo  ← separate multiple keywords with commas',
    filter_suffix: 'comma-separated',
    filter_hint: 'Enter one or more keywords separated by commas. Only projects whose name contains <b>at least one</b> keyword will be imported.\nLeave empty to import <b>all</b> projects from the vault.\nExample:',
    status_card: 'Sync Status',
    status_enabled: 'Enabled',
    status_disabled: 'Disabled',
    db_projects: 'Projects in DB',
    db_tasks: 'Tasks in DB',
    vault_projects: 'Projects in Vault',
    vault_tasks: 'Tasks in Vault',
    last_import: 'Last Import (vault → DB)',
    last_export: 'Last Export (DB → vault)',
    never_synced: 'Never synced',
    never_exported: 'Never exported',
    auto_sync_title: 'Auto-Sync (Vault Watcher)',
    watchdog_installed: 'watchdog installed',
    watchdog_missing: 'watchdog not installed',
    vault_path_title: 'Vault Path Configuration',
    vault_path_active: 'Active',
    vault_path_not_configured: 'Not configured',
    vault_path_label: 'Dynamic Vault Path',
    vault_path_placeholder: '/absolute/path/to/your/obsidian/vault',
    vault_path_save: 'Save',
    vault_path_clear: 'Clear (use .env)',
    vault_path_hint: 'Set here to override the .env value. Leave empty to use OBSIDIAN_VAULT_PATH from .env.',
    env_path_label: '.env OBSIDIAN_VAULT_PATH',
    effective_path_label: 'Effective Vault Path',
    effective_path_none: '(none — sync disabled)',
    import_success: 'Import complete: {tasks_created} tasks created, {tasks_updated} updated',
    export_success: 'Export complete: {tasks_created} files created, {tasks_updated} updated',
    import_failed: 'Import failed: {error}',
    export_failed: 'Export failed: {error}',
    load_failed: 'Failed to load sync status: {error}',
    path_saved: 'Vault path saved',
    path_save_failed: 'Failed to save vault path: {error}',
    result_title: 'Last Sync Result',
    result_mode: 'Mode',
    result_duration: 'Duration',
    result_status: 'Status',
    result_projects_created: 'Projects Created',
    result_projects_updated: 'Projects Updated',
    result_tasks_created: 'Tasks Created',
    result_tasks_updated: 'Tasks Updated',
    result_time_entries: 'Time Entries Created',
    result_skipped: 'Skipped',
    sync_errors: 'Sync Errors',
  },

  // ─── Auth ──────────────────────────────────────────────────────────────────
  auth: {
    login_title: 'Sign in to SynapseERP',
    username: 'Username',
    password: 'Password',
    login_btn: 'Sign In',
    logging_in: 'Signing in…',
    login_failed: 'Invalid username or password',
    logout_success: 'Logged out successfully',
  },

  // ─── User Management ───────────────────────────────────────────────────────
  users: {
    title: 'User Management',
    new_user: 'New User',
    columns: {
      username: 'Username',
      email: 'Email',
      role: 'Role',
      created: 'Created',
      actions: 'Actions',
    },
    roles: {
      admin: 'Admin',
      editor: 'Editor',
      viewer: 'Viewer',
    },
  },
}
