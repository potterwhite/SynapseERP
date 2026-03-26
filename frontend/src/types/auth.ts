// Copyright (c) 2026 PotterWhite
// MIT License — see LICENSE in the project root.
//
// TypeScript types for authentication and user management (Phase 5.7).

export type UserRole = 'admin' | 'editor' | 'viewer'

export interface User {
  id: number
  username: string
  email: string
  role: UserRole
  allowed_tags: string[]
  is_superuser: boolean
}
