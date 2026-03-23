// Type declaration shim for frappe-gantt.
// The library ships without TypeScript types; this minimal declaration
// satisfies the compiler while keeping the actual usage type-safe.

declare module 'frappe-gantt' {
  interface FrappeTask {
    id: string
    name: string
    start: string
    end: string
    progress: number
    dependencies?: string
    custom_class?: string
    [key: string]: unknown
  }

  interface GanttOptions {
    view_mode?: string
    date_format?: string
    on_click?: (task: FrappeTask) => void
    on_date_change?: (task: FrappeTask, start: Date, end: Date) => void
    on_progress_change?: (task: FrappeTask, progress: number) => void
    on_view_change?: (mode: string) => void
    [key: string]: unknown
  }

  class Gantt {
    constructor(
      wrapper: string | HTMLElement,
      tasks: FrappeTask[],
      options?: GanttOptions,
    )
    change_view_mode(mode: string): void
    refresh(tasks: FrappeTask[]): void
  }

  export default Gantt
}
