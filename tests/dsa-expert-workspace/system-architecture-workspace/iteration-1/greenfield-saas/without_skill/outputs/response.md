# Architecture for a Simplified Jira-like SaaS MVP

## Context

- Team: 2 developers
- Timeline: 3 months to MVP
- Product: SaaS project management tool (simplified Jira)

---

## Recommended Architecture

### High-Level Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| **Frontend** | Next.js (App Router) + TypeScript | SSR/SSG out of the box, file-based routing, great DX, single framework for UI and API routes |
| **Backend / API** | Next.js API Routes (or Route Handlers) | Eliminates a separate backend service; co-located with the frontend; sufficient for MVP scale |
| **Database** | PostgreSQL (hosted on Supabase, Neon, or Railway) | Relational model fits project management data naturally; strong ecosystem |
| **ORM** | Prisma | Type-safe queries, easy migrations, great with TypeScript |
| **Auth** | NextAuth.js (Auth.js) or Clerk | Handles OAuth + email/password with minimal code; Clerk is even faster to integrate if budget allows |
| **Hosting** | Vercel | Zero-config deployment for Next.js, preview deploys on every PR, generous free tier |
| **File Storage** | S3-compatible (AWS S3, Cloudflare R2, or Supabase Storage) | For attachments on issues |
| **Real-time (stretch)** | Supabase Realtime or Pusher | Only if you need live board updates; skip for MVP if time is tight |

### Why a Monolith, Not Microservices

With 2 developers and 3 months, the single most important architectural decision is to **keep things simple**. A Next.js monolith gives you:

- One repo, one deploy, one mental model
- No inter-service communication overhead
- Shared types between frontend and backend
- Faster iteration speed

You can always extract services later if the product succeeds. Premature decomposition is the most common mistake small teams make.

---

## Data Model (Core Entities)

```
Organization
  |-- has many --> Project
  |-- has many --> User (via Membership)

Project
  |-- has many --> Board (optional, or just one default board per project)
  |-- has many --> Issue
  |-- has many --> Label
  |-- has many --> Status (e.g., To Do, In Progress, Done)

Issue
  |-- belongs to --> Project
  |-- belongs to --> Status
  |-- assigned to --> User (nullable)
  |-- has many --> Comment
  |-- has many --> Label (many-to-many)
  |-- has many --> Attachment
  |-- parent --> Issue (nullable, for sub-tasks)
  |-- fields: title, description (rich text), priority, order (float for reordering), created_at, updated_at

Comment
  |-- belongs to --> Issue
  |-- belongs to --> User
  |-- fields: body, created_at

User
  |-- fields: name, email, avatar_url

Membership
  |-- belongs to --> Organization
  |-- belongs to --> User
  |-- fields: role (owner | admin | member)
```

**Key design notes:**

- Use a `float` for issue ordering within columns to allow reordering without updating every row (insert between two floats).
- Store rich text descriptions as JSON (e.g., Tiptap/ProseMirror JSON) rather than raw HTML for safety and flexibility.
- Keep `Status` as a separate table per project so users can customize their workflow columns.

---

## MVP Feature Scope

Ship these and nothing more for v1:

### Must Have (Month 1-2)
1. **Auth** -- Sign up, sign in, sign out (OAuth with Google at minimum)
2. **Organizations & Projects** -- Create org, invite members by email, create projects
3. **Kanban Board** -- Drag-and-drop columns with issues; reorder within and across columns
4. **Issue CRUD** -- Create, view, edit, delete issues with title, description, status, priority, assignee
5. **Comments** -- Add comments to issues
6. **Filtering & Search** -- Filter board by assignee, priority, label; basic text search on issue titles

### Should Have (Month 2-3)
7. **Labels/Tags** -- Create and assign colored labels
8. **Sub-tasks** -- Simple parent-child issue relationship with a checklist view
9. **Activity Feed** -- Log of changes on an issue (status changed, assignee changed, etc.)
10. **Notifications** -- In-app notification when assigned to an issue or mentioned in a comment

### Explicitly Out of Scope for MVP
- Sprints / time tracking
- Gantt charts or roadmaps
- Custom fields
- Permissions beyond basic roles
- Integrations (Slack, GitHub, etc.)
- Mobile app

---

## Project Structure

```
/
├── prisma/
│   └── schema.prisma
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── (auth)/             # Auth pages (sign-in, sign-up)
│   │   ├── (dashboard)/        # Authenticated layout
│   │   │   ├── [orgSlug]/
│   │   │   │   ├── projects/
│   │   │   │   │   └── [projectId]/
│   │   │   │   │       ├── board/        # Kanban board view
│   │   │   │   │       ├── issues/       # List view
│   │   │   │   │       │   └── [issueId]/ # Issue detail
│   │   │   │   │       └── settings/
│   │   │   │   └── settings/
│   │   │   └── layout.tsx
│   │   ├── api/                # API Route Handlers
│   │   │   ├── issues/
│   │   │   ├── projects/
│   │   │   ├── comments/
│   │   │   └── organizations/
│   │   └── layout.tsx
│   ├── components/
│   │   ├── ui/                 # Reusable primitives (use shadcn/ui)
│   │   ├── board/              # Board-specific components
│   │   ├── issues/             # Issue-specific components
│   │   └── layout/             # Nav, sidebar, etc.
│   ├── lib/
│   │   ├── db.ts               # Prisma client singleton
│   │   ├── auth.ts             # Auth configuration
│   │   └── utils.ts
│   ├── hooks/                  # Custom React hooks
│   └── types/                  # Shared TypeScript types
├── public/
├── .env.local
├── package.json
├── tailwind.config.ts
└── tsconfig.json
```

---

## Key Technical Decisions

### 1. Use Server Components by Default
Fetch data in React Server Components. Only use client components (`"use client"`) for interactive elements like the drag-and-drop board, forms, and modals. This reduces client bundle size and simplifies data fetching.

### 2. Drag-and-Drop
Use **dnd-kit** or **@hello-pangea/dnd** (maintained fork of react-beautiful-dnd). Optimistically update the UI on drag, then persist the new order via an API call. Use `float`-based ordering to avoid rewriting all positions.

### 3. Rich Text Editor
Use **Tiptap** (built on ProseMirror). It is React-friendly, extensible, and stores content as JSON. Avoid rolling your own.

### 4. UI Component Library
Use **shadcn/ui** -- it gives you copy-paste, customizable components built on Radix UI + Tailwind. Not a dependency; it lives in your codebase. This is the fastest path to a professional-looking UI.

### 5. Data Fetching / State
Use **React Query (TanStack Query)** for client-side data fetching, caching, and optimistic updates. For server-side, use Next.js Server Components with direct Prisma calls. Avoid Redux entirely.

### 6. Validation
Use **Zod** for schema validation on both client (forms) and server (API routes). Share schemas between the two.

---

## Infrastructure & DevOps

### For 2 Devs, Keep It Minimal

- **Repo**: Single monorepo on GitHub
- **CI**: GitHub Actions -- lint, type-check, run tests on every PR
- **Deploy**: Vercel (auto-deploys from `main`, preview deploys from PRs)
- **Database**: Managed Postgres (Neon or Supabase -- both have free tiers and handle connection pooling)
- **Monitoring**: Vercel Analytics + Sentry for error tracking (free tier)
- **Environment management**: `.env.local` for local dev, Vercel environment variables for prod

### Database Migrations
Use Prisma Migrate. Run `prisma migrate deploy` as part of your deployment process (Vercel build step or a GitHub Action).

---

## Rough 3-Month Timeline

### Month 1: Foundation
- **Week 1**: Project setup (Next.js, Prisma, auth, database, CI/CD, deploy pipeline). Both devs pair on this.
- **Week 2**: Data model + API routes for orgs, projects, issues. Basic CRUD pages.
- **Week 3-4**: Kanban board with drag-and-drop. Issue detail page with description editor.

### Month 2: Core Features
- **Week 5-6**: Comments, assignees, priority, filtering. One dev on backend/API, one on UI.
- **Week 7-8**: Invite flow, team management, labels, search.

### Month 3: Polish & Launch
- **Week 9-10**: Sub-tasks, activity feed, notifications.
- **Week 11**: Bug fixes, performance, responsive design, loading/error states.
- **Week 12**: Beta testing with real users, iterate on feedback, prepare for launch.

**Division of work**: Avoid strict frontend/backend splits. Instead, divide by feature -- each dev owns a full vertical slice (API + UI for a feature). This reduces coordination overhead and blocking.

---

## Scaling Considerations (Post-MVP)

You do not need to solve these now, but keep them in mind:

- **Database**: Add indexes on frequently queried columns (project_id, status_id, assignee_id on issues). Prisma makes this easy in the schema.
- **Search**: If full-text search gets complex, move to a dedicated search engine (Meilisearch, Typesense) later.
- **Real-time**: Add WebSocket-based live updates for the board when multiple users are collaborating. Supabase Realtime or Ably.
- **Multi-tenancy**: The org-based data model already isolates tenants. Add row-level security or query scoping as you grow.
- **Background jobs**: For email notifications, use a simple queue (Inngest, Trigger.dev, or even a cron-based approach) rather than building your own.

---

## Summary

The architecture boils down to: **Next.js monolith + Postgres + Prisma + Vercel**. This is deliberately boring technology. With 2 devs and 3 months, your biggest risk is not shipping -- not making the wrong infrastructure choice. Pick proven tools, divide work by feature, and cut scope ruthlessly. You can refactor the architecture later; you cannot get back the time spent on premature optimization.
