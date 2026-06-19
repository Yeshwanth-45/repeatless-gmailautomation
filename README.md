# Gmail Intelligence Platform

> AI-powered Gmail Intelligence Platform that syncs your Gmail, provides AI-generated summaries and smart categorization, offers a RAG-powered chat agent to query your emails, and enables AI-assisted email composition.

Built with **Next.js 14**, **FastAPI**, **Supabase** (PostgreSQL + pgvector), **Google Gemini AI**, and **NVIDIA NIM**.

---

## ✨ Key Features

- **Gmail OAuth 2.0 Integration** — Full inbox sync with incremental updates via Gmail History API
- **AI-Powered Email Summarization** — Individual email summaries and thread-level conversation summaries using Gemini
- **Smart Categorization** — Automatic classification into Newsletter, Job/Recruitment, Finance, Notifications, Personal, and Work/Professional
- **RAG-Powered Chat Agent** — Ask questions about your emails with source citations grounded in your actual inbox
- **NVIDIA NIM Reranking** — Improved retrieval precision using neural reranking before answer generation
- **AI-Assisted Email Composition** — Smart replies and email drafting with context from your conversations
- **Thread View** — Full conversation context with chronological message display
- **Semantic Search** — pgvector-based vector search over your entire inbox

---

## 📋 Prerequisites

| Requirement | Details |
|---|---|
| **Python** | 3.11 or higher |
| **Node.js** | 18 or higher |
| **Supabase Account** | Free tier works — [supabase.com](https://supabase.com) |
| **Google Cloud Project** | With Gmail API enabled — [console.cloud.google.com](https://console.cloud.google.com) |
| **Google Gemini API Key** | Free at [aistudio.google.com](https://aistudio.google.com) |
| **NVIDIA NIM API Key** | Free at [build.nvidia.com](https://build.nvidia.com) |

---

## 🚀 Setup Instructions

### 1. Supabase Setup

1. Create a new project at [supabase.com](https://supabase.com)
2. Once the project is ready, go to **SQL Editor** in the dashboard
3. Open and run the schema file:
   ```
   supabase/schema.sql
   ```
4. Copy your **Project URL** and **Service Role Key** from **Settings → API**

> [!IMPORTANT]
> Use the **service role key**, not the anon key. The service role key bypasses Row Level Security, which is required for backend operations.

### 2. Google Cloud Setup

1. Go to [console.cloud.google.com](https://console.cloud.google.com) and create a new project (or select existing)
2. Navigate to **APIs & Services → Library** and enable the **Gmail API**
3. Go to **APIs & Services → Credentials** and create an **OAuth 2.0 Client ID**:
   - Application type: **Web application**
   - Authorized redirect URIs: add `http://localhost:8000/auth/gmail/callback`
4. Copy the **Client ID** and **Client Secret**
5. Go to **OAuth consent screen**:
   - Set the publishing status to **Testing**
   - Add your own email address under **Test users**

> [!WARNING]
> While in Testing mode, only users you explicitly add as test users can authenticate. Move to Production only after you've verified everything works.

### 3. Backend Setup

```bash
cd backend
pip install -r requirements.txt
cp ../.env.example .env
```

Edit `.env` and fill in your actual values (see [Environment Variables](#-environment-variables) below), then start the server:

```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### 4. Frontend Setup

```bash
cd frontend
npm install
cp ../.env.example .env.local
```

Edit `.env.local` and set `NEXT_PUBLIC_BACKEND_URL=http://localhost:8000`, then start the dev server:

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`.

---

## 📁 Folder Structure

```
gmail-intelligence-platform/
├── .env.example              # Template for all environment variables
├── README.md                 # This file
├── Architecture.md           # Detailed architecture & design document
│
├── backend/                  # FastAPI backend application
│   ├── __init__.py           # Python package marker
│   ├── requirements.txt      # Python dependencies
│   ├── db/                   # Database client & connection setup
│   │   └── __init__.py       #   Supabase client initialization
│   ├── models/               # Pydantic data models & schemas
│   │   └── __init__.py       #   Request/response models
│   ├── routers/              # API route handlers (FastAPI routers)
│   │   └── __init__.py       #   Auth, emails, chat, compose endpoints
│   └── services/             # Business logic & external API integrations
│       └── __init__.py       #   Gmail, Gemini, NVIDIA, embedding services
│
├── frontend/                 # Next.js frontend application
│   ├── package.json          # Node.js dependencies & scripts
│   ├── next.config.ts        # Next.js configuration
│   ├── tsconfig.json         # TypeScript configuration
│   ├── postcss.config.mjs    # PostCSS config (Tailwind CSS)
│   ├── eslint.config.mjs     # ESLint configuration
│   ├── public/               # Static assets (favicon, images)
│   │   └── ...
│   └── app/                  # Next.js App Router pages & layouts
│       ├── layout.tsx        #   Root layout (fonts, global styles)
│       ├── page.tsx          #   Home / landing page
│       ├── globals.css       #   Global CSS styles (Tailwind)
│       └── favicon.ico       #   App favicon
│
└── supabase/                 # Database setup
    └── schema.sql            # Full PostgreSQL schema (tables, indexes, pgvector)
```

---

## 🔐 Environment Variables

Create a `.env` file in the `backend/` directory (copy from `.env.example`). For the frontend, create `.env.local` in the `frontend/` directory.

| Variable | Description | Example |
|---|---|---|
| `SUPABASE_URL` | Your Supabase project URL | `https://abc123.supabase.co` |
| `SUPABASE_SERVICE_KEY` | Service role key from Supabase API settings | `eyJhbGciOiJIUzI1NiIs...` |
| `GOOGLE_CLIENT_ID` | OAuth 2.0 Client ID from Google Cloud Console | `123456.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | OAuth 2.0 Client Secret | `GOCSPX-...` |
| `GOOGLE_REDIRECT_URI` | OAuth callback URL registered in Google Cloud | `http://localhost:8000/auth/gmail/callback` |
| `GEMINI_API_KEY` | Google Gemini API key from AI Studio | `AIzaSy...` |
| `NVIDIA_API_KEY` | NVIDIA NIM API key from build.nvidia.com | `nvapi-...` |
| `NVIDIA_BASE_URL` | NVIDIA NIM API base URL | `https://integrate.api.nvidia.com/v1` |
| `FRONTEND_URL` | Frontend application URL | `http://localhost:3000` |
| `BACKEND_URL` | Backend API URL | `http://localhost:8000` |
| `NEXT_PUBLIC_BACKEND_URL` | Backend URL accessible from the browser (frontend `.env.local`) | `http://localhost:8000` |

> [!CAUTION]
> Never commit your `.env` files to version control. The `.env.example` file contains only placeholder values and is safe to commit.

---

## 📡 API Endpoints

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/auth/gmail/login` | Initiates Gmail OAuth 2.0 flow — redirects to Google consent screen |
| `GET` | `/auth/gmail/callback` | Handles OAuth callback, stores tokens, redirects to frontend |
| `GET` | `/auth/me` | Returns the current authenticated user's profile |

### Email Sync & Management

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/emails/sync` | Triggers full Gmail sync (initial) or incremental sync |
| `GET` | `/emails` | Retrieves all synced emails with pagination & filters |
| `GET` | `/emails/{email_id}` | Retrieves a single email by ID |
| `GET` | `/emails/thread/{thread_id}` | Retrieves all messages in a thread |

### AI Features

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/emails/{email_id}/summarize` | Generates AI summary for a single email |
| `POST` | `/emails/thread/{thread_id}/summarize` | Generates AI summary for an entire thread |
| `POST` | `/emails/{email_id}/categorize` | AI-categorizes a single email |
| `POST` | `/emails/categorize-all` | Batch categorizes all uncategorized emails |

### Chat Agent (RAG)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/chat/sessions` | Creates a new chat session |
| `GET` | `/chat/sessions` | Lists all chat sessions for the user |
| `POST` | `/chat/sessions/{session_id}/messages` | Sends a message and receives an AI response with sources |
| `GET` | `/chat/sessions/{session_id}/messages` | Retrieves chat history for a session |

### Email Composition

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/compose/draft` | AI-assisted email draft generation |
| `POST` | `/compose/reply` | AI-generated smart reply to an email |
| `POST` | `/compose/send` | Sends a composed email via Gmail API |

---

## 🛠️ Tech Stack

| Technology | Role | Why |
|---|---|---|
| **Next.js 14** | Frontend framework | App Router for simplified routing, server components, great DX, Vercel-ready |
| **Tailwind CSS** | UI styling | Utility-first CSS; rapid prototyping with consistent design |
| **TypeScript** | Frontend language | Type safety, better DX, catches bugs at compile time |
| **FastAPI** | Backend framework | Async Python, auto-generated docs, ideal for AI/API integrations |
| **Supabase** | Database & Auth | Managed PostgreSQL + pgvector in one platform; generous free tier |
| **pgvector** | Vector search | Native vector similarity search inside PostgreSQL — no extra infrastructure |
| **Google Gemini 1.5 Flash** | LLM (summarize, chat, categorize) | Fast, cost-effective, large context window, free tier available |
| **Gemini text-embedding-004** | Text embeddings | Same ecosystem as Gemini; 768-dimensional vectors; strong retrieval performance |
| **NVIDIA NIM** | Neural reranking | Free-tier reranking that measurably improves RAG retrieval quality |
| **Google Gmail API** | Email data source | Full programmatic access to Gmail (read, sync, send) via OAuth 2.0 |

---

## 📄 License

This project is for educational and personal use.
