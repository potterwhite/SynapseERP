# Phase 5.7 — Permission System + Multi-user: Implementation Plan

> **⚠️ FOR AI AGENTS**
> This document describes the complete implementation plan for Phase 5.7.
> If you are resuming this work mid-session, check which steps below are marked ✅.
> Start from the first ❌ step.
>
> Last updated: 2026-03-26

---

## Overview

Replace Django Session authentication with JWT (via `djangorestframework-simplejwt`).
Add user roles and tag-based project access control.

**Goals:**
1. Custom Vue login page (no more Django admin login redirect)
2. JWT access + refresh token flow
3. Three user roles: `admin` / `editor` / `viewer`
4. Tag-based project visibility: non-admin users only see projects matching their `allowed_tags`

---

## Architecture Decisions

### Why JWT?
- Enables mobile-friendly / multi-client auth (Phase 6 Docker, future mobile)
- Decoupled from Django session/cookie system
- Easier to add per-user claims (role, allowed_tags)

### Token Storage
- `access` token: `localStorage` (key: `synapse_access_token`)
- `refresh` token: `localStorage` (key: `synapse_refresh_token`)
- Access token lifetime: 60 minutes
- Refresh token lifetime: 7 days

### Role Model
```
admin  → full access: all projects, user management, sync config
editor → can read/write projects/tasks they have tag access to
viewer → read-only access to projects they have tag access to
```

### Tag-Based Access
- `UserProfile.allowed_tags: list[str]` — empty list means NO projects visible (except for admin)
- A project is visible to a user if: `user.role == 'admin'` OR `any(tag in project.tags for tag in user.allowed_tags)`
- Projects with empty `tags` are visible to all authenticated users

---

## Implementation Steps

### BACKEND

#### Step B1: Install simplejwt ✅ (requirements.txt already updated)
```
djangorestframework-simplejwt>=5.3
```

#### Step B2: Create `synapse_auth` Django app ❌
Location: `backend/src/synapse_auth/`

Files to create:
- `__init__.py`
- `apps.py`
- `models.py` — `UserProfile` model
- `serializers.py` — login, user CRUD, token serializers
- `views.py` — login, logout, me, users CRUD
- `urls.py` — URL patterns
- `permissions.py` — `IsAdminRole`, `IsEditorOrAbove`

**`UserProfile` model:**
```python
class UserProfile(models.Model):
    user = OneToOneField(User, on_delete=CASCADE, related_name='profile')
    role = CharField(choices=['admin','editor','viewer'], default='viewer')
    allowed_tags = JSONField(default=list)  # e.g. ["work", "urgent"]
    created_at = DateTimeField(auto_now_add=True)
```

**Signal:** auto-create `UserProfile` on `User` post_save.
First superuser gets `role='admin'` automatically.

#### Step B3: Update `settings.py` ❌

Add to `INSTALLED_APPS`: `'synapse_auth'`

Add JWT config:
```python
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```

Update `REST_FRAMEWORK`:
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # keep for /admin/
    ],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
}
```

Add `'rest_framework_simplejwt'` to INSTALLED_APPS (for blacklist).

#### Step B4: Auth URL patterns ❌

In `backend/synapse_project/api_urls.py`, add:
```python
path("auth/", include("synapse_auth.urls")),
```

`synapse_auth/urls.py`:
```python
urlpatterns = [
    path("login/",    views.login_view,       name="auth-login"),
    path("refresh/",  views.refresh_view,     name="auth-refresh"),
    path("logout/",   views.logout_view,      name="auth-logout"),
    path("me/",       views.current_user,     name="auth-me"),  # replaces synapse_api's auth/me
    path("users/",    views.user_list,        name="auth-user-list"),
    path("users/<int:pk>/", views.user_detail, name="auth-user-detail"),
]
```

Note: `GET /api/auth/me/` is currently in `synapse_api/urls.py`.
Phase 5.7 moves it to `synapse_auth/urls.py` with expanded response (adds `role`, `allowed_tags`).
Old endpoint in `synapse_api` should be removed or redirect.

#### Step B5: Update PM views — tag-based access ❌

In `synapse_pm/api/views.py`, update `project_list` GET:
```python
# After fetching all projects, filter by user's allowed_tags
user = request.user
if hasattr(user, 'profile') and user.profile.role != 'admin':
    allowed = set(user.profile.allowed_tags or [])
    if allowed:
        projects = [
            p for p in projects
            if not p['tags'] or any(t in allowed for t in p['tags'])
        ]
    else:
        projects = []  # no allowed tags → see nothing
```

Apply same filter to `project_detail`, `task_list`, `gantt_tasks` (when project_id given).

#### Step B6: Create migrations ❌
```bash
./synapse dev:migrate
```

---

### FRONTEND

#### Step F1: Update `api/client.ts` — JWT Bearer ❌

Replace CSRF-based approach with JWT Bearer:
```typescript
// Request interceptor: attach JWT Bearer token
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('synapse_access_token')
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`
  }
  return config
})

// Response interceptor: on 401, try refresh then retry once
// If refresh fails, redirect to /login
```

Keep `withCredentials: true` for `/admin/` Django admin session compatibility.

#### Step F2: Update `stores/auth.ts` ❌

New state:
```typescript
interface User {
  id: number
  username: string
  email: string
  role: 'admin' | 'editor' | 'viewer'
  allowed_tags: string[]
}

const accessToken = ref<string | null>(localStorage.getItem('synapse_access_token'))
const refreshToken = ref<string | null>(localStorage.getItem('synapse_refresh_token'))
const user = ref<User | null>(null)
const isAuthenticated = ref(false)

async function login(username: string, password: string): Promise<void>
async function logout(): Promise<void>
async function refreshAccessToken(): Promise<boolean>
async function fetchCurrentUser(): Promise<void>
const isAdmin = computed(() => user.value?.role === 'admin')
const isEditor = computed(() => ['admin','editor'].includes(user.value?.role ?? ''))
```

#### Step F3: Create `views/LoginView.vue` ❌

Design: centered card, Naive UI style, dark mode compatible.
- Username / password fields (NInput)
- Login button (NButton type="primary")
- Error message on failure (NAlert type="error")
- On success: call `authStore.login()` → router.push('/')
- No registration (admin creates users via /admin/users/ page)

#### Step F4: Update `router/index.ts` ❌

```typescript
// Routes to add:
{ path: '/login', name: 'login', component: () => import('@/views/LoginView.vue'), meta: { public: true } }
{ path: '/admin/users', name: 'admin-users', component: () => import('@/views/admin/UsersView.vue') }

// New guard logic:
router.beforeEach(async (to) => {
  if (to.meta.public) return true        // public routes: /login

  const authStore = useAuthStore()
  if (!authStore.isAuthenticated) {
    await authStore.fetchCurrentUser()   // try with stored token
  }
  if (!authStore.isAuthenticated) {
    return { name: 'login' }             // redirect to Vue login page (not /admin/)
  }
  // Role guard for admin-only routes
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    return { name: 'dashboard' }
  }
  return true
})
```

#### Step F5: Update `components/layout/Header.vue` ❌

Add right side: username chip + role badge + logout button.
```html
<n-space>
  <n-tag size="small">{{ authStore.user?.role }}</n-tag>
  <n-text>{{ authStore.user?.username }}</n-text>
  <n-button size="small" @click="handleLogout">Logout</n-button>
</n-space>
```

#### Step F6: Update `components/layout/Sidebar.vue` ❌

Add "User Management" menu item, visible only when `authStore.isAdmin`.

#### Step F7: Create `views/admin/UsersView.vue` ❌

Features:
- Table: username, email, role, allowed_tags, created_at
- Create user modal (NModal): username, email, password, role, allowed_tags
- Edit user inline or modal: role + allowed_tags only (not password)
- Delete user with confirmation
- Calls `/api/auth/users/` endpoints

---

## File Change Summary

### New Files to Create

| File | Description |
|------|-------------|
| `backend/src/synapse_auth/__init__.py` | Django app init |
| `backend/src/synapse_auth/apps.py` | AppConfig |
| `backend/src/synapse_auth/models.py` | UserProfile model |
| `backend/src/synapse_auth/serializers.py` | Auth serializers |
| `backend/src/synapse_auth/views.py` | Auth views |
| `backend/src/synapse_auth/urls.py` | Auth URL patterns |
| `backend/src/synapse_auth/permissions.py` | Role-based permissions |
| `backend/src/synapse_auth/signals.py` | Auto-create UserProfile on User save |
| `frontend/src/views/LoginView.vue` | Custom login page |
| `frontend/src/views/admin/UsersView.vue` | User management (admin) |
| `frontend/src/api/auth.ts` | Auth API call functions |

### Files to Modify

| File | Change |
|------|--------|
| `backend/requirements.txt` | ✅ Added `djangorestframework-simplejwt>=5.3` |
| `backend/synapse_project/settings.py` | Add SIMPLE_JWT config, update REST_FRAMEWORK auth classes, add synapse_auth to INSTALLED_APPS |
| `backend/synapse_project/api_urls.py` | Add `path("auth/", include("synapse_auth.urls"))` |
| `backend/src/synapse_api/urls.py` | Remove old `auth/me/` (moved to synapse_auth) |
| `backend/src/synapse_api/views.py` | Remove `current_user` view (moved to synapse_auth) |
| `backend/src/synapse_pm/api/views.py` | Add tag-based access filter in project_list, project_detail, task_list, gantt_tasks |
| `frontend/src/api/client.ts` | Replace CSRF interceptor with JWT Bearer interceptor + auto-refresh |
| `frontend/src/stores/auth.ts` | Add role, JWT token management, login/logout actions |
| `frontend/src/router/index.ts` | New JWT guard, add /login and /admin/users routes |
| `frontend/src/components/layout/Header.vue` | Add user info + logout |
| `frontend/src/components/layout/Sidebar.vue` | Add Users link (admin only) |

---

## Testing Checklist

After implementation, verify:

- [ ] `POST /api/auth/login/` returns `{access, refresh}`
- [ ] `GET /api/auth/me/` with Bearer token returns user + role + allowed_tags
- [ ] `POST /api/auth/refresh/` rotates tokens
- [ ] `POST /api/auth/logout/` blacklists refresh token
- [ ] Expired access token → auto-refresh → seamless UX
- [ ] Expired refresh token → redirect to /login page
- [ ] Admin user sees all projects regardless of tags
- [ ] Editor with `allowed_tags: ["work"]` only sees projects tagged "work" or untagged
- [ ] Viewer with empty `allowed_tags: []` sees no projects
- [ ] Admin can create/edit/delete users via `/admin/users`
- [ ] Non-admin cannot access `/admin/users` route
- [ ] Django `/admin/` interface still works (session auth preserved)
- [ ] Dark mode still works on login page
- [ ] Mobile layout still works after header changes

---

## Notes & Gotchas

1. **Token blacklist**: `rest_framework_simplejwt.token_blacklist` must be in `INSTALLED_APPS` for logout to work. Run migrations after adding it.

2. **First superuser**: When Django `createsuperuser` runs, the `UserProfile` signal will auto-create a profile. Set `role='admin'` in the signal handler when `user.is_superuser`.

3. **Existing sessions**: After deploying Phase 5.7, existing Django admin sessions remain valid (SessionAuthentication is kept). Users will be prompted to log in via the new Vue page on next SPA load.

4. **CORS/CSRF**: JWT doesn't need CSRF (stateless). Keep `withCredentials: true` only for `/admin/` compatibility. For `/api/` endpoints using JWT, CSRF is not required.

5. **`/api/auth/me/` migration**: The old endpoint in `synapse_api` must be removed to avoid conflict. The new one in `synapse_auth` returns expanded data (adds `role`, `allowed_tags`).

6. **Naive UI password input**: Use `<n-input type="password" show-password-on="click">` for the login form.
