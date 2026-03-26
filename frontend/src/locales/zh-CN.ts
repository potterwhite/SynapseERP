// Copyright (c) 2026 PotterWhite — MIT License

/**
 * Simplified Chinese locale for SynapseERP.
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
    save: '保存',
    cancel: '取消',
    delete: '删除',
    edit: '编辑',
    confirm: '确认',
    create: '创建',
    search: '搜索',
    loading: '加载中…',
    retry: '重试',
    unknown_error: '未知错误',
    never: '从未',
    none: '无',
  },

  // ─── Header ────────────────────────────────────────────────────────────────
  header: {
    logout: '退出登录',
    switch_to_light: '切换浅色模式',
    switch_to_dark: '切换深色模式',
    language: '语言',
  },

  // ─── Sidebar / Navigation ──────────────────────────────────────────────────
  nav: {
    dashboard: '仪表盘',
    projects: '项目管理',
    gantt: '甘特图',
    sync: '同步设置',
    attendance: '考勤分析',
    bom: 'BOM 分析',
    users: '用户管理',
  },

  // ─── Dashboard ─────────────────────────────────────────────────────────────
  dashboard: {
    title: '仪表盘',
    modules: '功能模块',
  },

  // ─── PM — Project List ─────────────────────────────────────────────────────
  projects: {
    title: '项目管理',
    meeting_mode: '会议模式',
    exit_meeting: '退出会议',
    meeting_mode_tip: '会议模式激活 — 已隐藏个人项目',
    meeting_mode_hint: '会议模式：隐藏标记为 "personal" 的项目',
    new_project: '新建项目',
    delete_selected: '删除 ({n})',
    search_placeholder: '搜索项目…',
    filter_status: '状态筛选',
    filter_tag: '按标签筛选…',
    sync_vault: '同步 Vault',
    status: {
      active: '进行中',
      archived: '已归档',
      on_hold: '暂停',
      all: '全部',
    },
    columns: {
      project: '项目',
      status: '状态',
      tasks: '任务',
      hours: '工时',
      deadline: '截止日期',
      last_sync: '最后同步',
    },
    stats: {
      total_projects: '项目总数',
      active: '进行中',
      total_tasks: '任务总数',
      hours_logged: '已记录工时',
    },
    delete_confirm_title: '删除项目',
    delete_confirm_content: '确定要删除 "{name}"？此操作不可撤销。',
    bulk_delete_confirm_title: '删除 {count} 个项目',
    bulk_delete_confirm_content: '确定要删除所选的 {count} 个项目？此操作不可撤销。',
    delete_success: '项目 "{name}" 已删除',
    bulk_delete_success: '已删除 {count} 个项目',
    load_error: '项目加载失败',
  },

  // ─── PM — Project Form Modal ───────────────────────────────────────────────
  project_form: {
    create_title: '新建项目',
    edit_title: '编辑项目',
    name_label: '项目名称',
    name_placeholder: '请输入项目名称',
    name_required: '项目名称不能为空',
    status_label: '状态',
    deadline_label: '截止日期',
    tags_label: '标签',
    tags_placeholder: '输入标签后按 Enter',
  },

  // ─── PM — Task View ────────────────────────────────────────────────────────
  tasks: {
    all_projects: '全部项目',
    new_task: '新建任务',
    delete_selected: '删除 ({n})',
    edit_task: '编辑任务',
    search_placeholder: '搜索任务…',
    status: {
      all: '全部状态',
      todo: '待办',
      doing: '进行中',
      done: '已完成',
      cancelled: '已取消',
    },
    priority: {
      all: '全部优先级',
      high: '高',
      medium: '中',
      low: '低',
    },
    columns: {
      task: '任务',
      status: '状态',
      priority: '优先级',
      deadline: '截止日期',
      est_actual: '预估 / 实际',
    },
    form: {
      name_label: '任务名称',
      name_placeholder: '请输入任务名称',
      name_required: '任务名称不能为空',
      status_label: '状态',
      status_required: '状态不能为空',
      priority_label: '优先级',
      priority_required: '优先级不能为空',
      deadline_label: '截止日期',
      est_hours_label: '预估工时',
      est_hours_placeholder: '例如 8',
      description_label: '描述',
      description_placeholder: '任务描述（将写入 Vault）',
    },
    delete_confirm_title: '删除任务',
    delete_confirm_content: '删除 "{name}"？此操作不可撤销。',
    bulk_delete_confirm_title: '删除 {count} 个任务',
    bulk_delete_confirm_content: '删除所选 {count} 个任务？此操作不可撤销。',
    delete_success: '任务 "{name}" 已删除',
    bulk_delete_success: '已删除 {count} 个任务',
    create_success: '任务已创建并写入 Vault',
    update_success: '任务已更新并写入 Vault',
  },

  // ─── PM — Gantt ────────────────────────────────────────────────────────────
  gantt: {
    title: '甘特图',
    all_projects: '全部项目',
    no_tasks: '暂无任务',
    tasks_count: '{n} 个任务',
    view: '视图：',
    update_dates_title: '更新任务日期？',
    update_dates_content: '将 {name} 移动到\n{start} → {end}？',
    update_success: '任务日期已更新',
    update_failed: '更新失败',
    load_error: '甘特图数据加载失败',
  },

  // ─── Sync Settings ─────────────────────────────────────────────────────────
  sync: {
    title: 'Obsidian 同步',
    subtitle: '数据库与 Obsidian Vault 双向同步',
    import_btn: '从 Vault 导入',
    export_btn: '导出到 Vault',
    filter_card_title: '导入过滤器（可选）',
    filter_placeholder_blur: '按项目名称关键字过滤（留空 = 导入全部）',
    filter_placeholder_focus: '例如 AI, 量化, Demo  ← 多个关键字用英文逗号分隔',
    filter_suffix: '英文逗号分隔',
    filter_hint: '输入一个或多个关键字，用逗号分隔。只有项目名称包含 <b>至少一个</b> 关键字的项目才会被导入。\n留空则导入 Vault 中的 <b>全部</b> 项目。\n示例：',
    status_card: '同步状态',
    status_enabled: '已启用',
    status_disabled: '未启用',
    db_projects: '数据库项目数',
    db_tasks: '数据库任务数',
    vault_projects: 'Vault 项目数',
    vault_tasks: 'Vault 任务数',
    last_import: '最后导入（Vault → DB）',
    last_export: '最后导出（DB → Vault）',
    never_synced: '从未同步',
    never_exported: '从未导出',
    auto_sync_title: '自动同步（Vault 监控）',
    watchdog_installed: 'watchdog 已安装',
    watchdog_missing: 'watchdog 未安装',
    vault_path_title: 'Vault 路径配置',
    vault_path_active: '已激活',
    vault_path_not_configured: '未配置',
    vault_path_label: '动态 Vault 路径',
    vault_path_placeholder: '/absolute/path/to/your/obsidian/vault',
    vault_path_save: '保存',
    vault_path_clear: '清除（使用 .env）',
    vault_path_hint: '在此处设置可覆盖 .env 中的值。留空则使用 .env 中的 OBSIDIAN_VAULT_PATH。',
    env_path_label: '.env OBSIDIAN_VAULT_PATH',
    effective_path_label: '实际 Vault 路径',
    effective_path_none: '（未配置 — 同步已禁用）',
    import_success: '导入完成：新建 {tasks_created} 个任务，更新 {tasks_updated} 个',
    export_success: '导出完成：新建 {tasks_created} 个文件，更新 {tasks_updated} 个',
    import_failed: '导入失败：{error}',
    export_failed: '导出失败：{error}',
    load_failed: '同步状态加载失败：{error}',
    path_saved: 'Vault 路径已保存',
    path_save_failed: '保存 Vault 路径失败：{error}',
    result_title: '最近同步结果',
    result_mode: '模式',
    result_duration: '耗时',
    result_status: '状态',
    result_projects_created: '新建项目',
    result_projects_updated: '更新项目',
    result_tasks_created: '新建任务',
    result_tasks_updated: '更新任务',
    result_time_entries: '时间记录',
    result_skipped: '跳过',
    sync_errors: '同步错误',
  },

  // ─── Auth ──────────────────────────────────────────────────────────────────
  auth: {
    login_title: '登录 SynapseERP',
    username: '用户名',
    password: '密码',
    login_btn: '登录',
    logging_in: '登录中…',
    login_failed: '用户名或密码错误',
    logout_success: '已退出登录',
  },

  // ─── User Management ───────────────────────────────────────────────────────
  users: {
    title: '用户管理',
    new_user: '新建用户',
    columns: {
      username: '用户名',
      email: '邮箱',
      role: '角色',
      created: '创建时间',
      actions: '操作',
    },
    roles: {
      admin: '管理员',
      editor: '编辑者',
      viewer: '访客',
    },
  },
}
