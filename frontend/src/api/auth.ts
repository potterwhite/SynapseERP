// Copyright (c) 2026 PotterWhite
// MIT License — see LICENSE in the project root.
//
// Auth API call functions: login, logout, refresh, current user, user management.

import client from '@/api/client'
import type { User } from '@/types/auth'

// ---------------------------------------------------------------------------
// Auth endpoints
// ---------------------------------------------------------------------------

export interface LoginPayload {
  username: string
  password: string
}

export interface LoginResponse {
  access: string
  refresh: string
  user: User
}

export interface TokenRefreshResponse {
  access: string
  refresh?: string
}

export const authApi = {
  /**
   * POST /api/auth/login/
   * Authenticate and receive JWT tokens + user profile.
   */
  login(payload: LoginPayload) {
    return client.post<LoginResponse>('/auth/login/', payload)
  },

  /**
   * POST /api/auth/logout/
   * Blacklist the refresh token on the server side.
   */
  logout(refreshToken: string) {
    return client.post('/auth/logout/', { refresh: refreshToken })
  },

  /**
   * GET /api/auth/me/
   * Fetch the currently authenticated user's profile (id, username, role, allowed_tags).
   */
  me() {
    return client.get<User>('/auth/me/')
  },
}

// ---------------------------------------------------------------------------
// User management (admin only)
// ---------------------------------------------------------------------------

export interface UserCreatePayload {
  username: string
  email?: string
  password: string
  role: 'admin' | 'editor' | 'viewer'
  allowed_tags?: string[]
}

export interface UserUpdatePayload {
  role?: 'admin' | 'editor' | 'viewer'
  allowed_tags?: string[]
  email?: string
}

export const userApi = {
  /** GET /api/auth/users/ */
  list() {
    return client.get<User[]>('/auth/users/')
  },

  /** GET /api/auth/users/{id}/ */
  get(id: number) {
    return client.get<User>(`/auth/users/${id}/`)
  },

  /** POST /api/auth/users/ */
  create(payload: UserCreatePayload) {
    return client.post<User>('/auth/users/', payload)
  },

  /** PATCH /api/auth/users/{id}/ */
  update(id: number, payload: UserUpdatePayload) {
    return client.patch<User>(`/auth/users/${id}/`, payload)
  },

  /** DELETE /api/auth/users/{id}/ */
  delete(id: number) {
    return client.delete(`/auth/users/${id}/`)
  },
}
