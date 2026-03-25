// Copyright (c) 2026 PotterWhite
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

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
