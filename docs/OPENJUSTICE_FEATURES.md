# OpenJustice — Complete Features & Functions Reference

> **AI-Powered Legal Assistance Platform for Sri Lanka**
> Multilingual legal Q&A, RAG-powered document retrieval, voice interface, and WhatsApp integration.

---

## Table of Contents

- [1. System Overview](#1-system-overview)
- [2. Technology Stack](#2-technology-stack)
- [3. Authentication & User Management](#3-authentication--user-management)
- [4. Conversational AI Chat](#4-conversational-ai-chat)
- [5. RAG Pipeline (Retrieval-Augmented Generation)](#5-rag-pipeline-retrieval-augmented-generation)
- [6. Semantic Cache](#6-semantic-cache)
- [7. Voice Interface (STT & TTS)](#7-voice-interface-stt--tts)
- [8. WhatsApp Integration](#8-whatsapp-integration)
- [9. Document Analyzer](#9-document-analyzer)
- [10. Legal Library](#10-legal-library)
- [11. Multilingual Support & Language Detection](#11-multilingual-support--language-detection)
- [12. Prompt Security & Safety](#12-prompt-security--safety)
- [13. Real-Time WebSocket Communication](#13-real-time-websocket-communication)
- [14. Admin Dashboard & Analytics](#14-admin-dashboard--analytics)
- [15. System Settings Management](#15-system-settings-management)
- [16. Research & Evaluation Framework](#16-research--evaluation-framework)
- [17. Background Task Pipeline](#17-background-task-pipeline)
- [18. Telemetry & Logging](#18-telemetry--logging)
- [19. Frontend Features & UI](#19-frontend-features--ui)
- [20. Deployment & DevOps](#20-deployment--devops)
- [21. API Route Summary](#21-api-route-summary)
- [22. Database Models](#22-database-models)
- [23. Architecture Summary](#23-architecture-summary)

---

## 1. System Overview

OpenJustice is a full-stack AI-powered legal assistance platform designed to help users navigate **Sri Lankan law**. It provides legally grounded answers using **RAG (Retrieval-Augmented Generation)** across **English, Sinhala, and Tamil** languages. The system comprises:

- **Backend** — FastAPI (Python) with Clean Architecture, PostgreSQL + pgvector, OpenAI GPT-4o integration
- **Frontend** — React 19 + TypeScript + Vite 7 SPA with TailwindCSS, Zustand state management, and i18next internationalization

### Key Capabilities

| Capability | Description |
|---|---|
| **Legal Q&A** | Multi-turn conversational AI with streaming responses grounded in Sri Lankan legal documents |
| **Voice Interaction** | Full voice pipeline with Speech-to-Text (Whisper) and Text-to-Speech (OpenAI TTS) |
| **WhatsApp Bot** | Complete conversational AI via Twilio WhatsApp API including voice message support |
| **Document Analysis** | Upload legal documents (PDF/DOCX) for AI-powered risk & compliance analysis |
| **Legal Library** | Browsable collection-based directory of ingested legal documents |
| **Admin Panel** | Comprehensive analytics, user management, data sources, retrieval monitoring, and system settings |
| **Multilingual** | Native trilingual support (English, Sinhala, Tamil) with Unicode-based language detection |
| **Security** | Prompt injection detection, reCAPTCHA, JWT auth with HTTP-only cookies, audit logging |

---

## 2. Technology Stack

### Backend

| Category | Technology |
|---|---|
| Framework | FastAPI (Python 3.10+) |
| Package Manager | uv (Rust-based) |
| Database | PostgreSQL 15+ with pgvector extension |
| ORM | SQLAlchemy 2+ (async via asyncpg) |
| Migrations | Alembic (async-aware) |
| Validation | Pydantic 2 + pydantic-settings |
| Authentication | JWT (python-jose) + bcrypt (passlib) |
| AI / LLM | OpenAI GPT-4o / GPT-4o-mini via openai SDK |
| RAG | LangChain + langchain-openai + langchain-community |
| Embeddings | OpenAI `text-embedding-3-large` |
| Speech-to-Text | OpenAI Whisper API (`gpt-4o-mini-transcribe`) |
| Text-to-Speech | OpenAI TTS API (`gpt-4o-mini-tts`) |
| WhatsApp | Twilio WhatsApp API |
| WebSocket | FastAPI WebSocket with connection manager |
| Token Counting | tiktoken |
| Testing | pytest, pytest-asyncio, pytest-cov, pytest-mock |
| Code Quality | Black, Flake8, mypy, isort |

### Frontend

| Category | Technology |
|---|---|
| Core | React 19 · TypeScript ~5.9 · Vite 7 |
| Routing | React Router DOM 7 (centralized config + lazy loading) |
| Styling | TailwindCSS 4 · class-variance-authority · clsx · tailwind-merge |
| State Management | Zustand 5 (with `persist` middleware) · React Context |
| HTTP & Networking | Axios (with interceptors) · Socket.IO Client |
| UI Components | Radix UI (Dialog, Dropdown, Tabs, Tooltip) · Lucide React icons |
| Voice | MediaRecorder API · Web Audio API (AnalyserNode) · WaveSurfer.js |
| Internationalization | i18next · react-i18next · i18next-browser-languagedetector |
| Testing | Vitest · React Testing Library · jsdom |
| Linting | ESLint 9 · typescript-eslint · react-hooks · react-refresh |

---

## 3. Authentication & User Management

### 3.1 User Registration

- **Endpoint:** `POST /api/auth/register`
- New users register with first name, last name, email, phone number, password, and preferred language
- Passwords are hashed using **bcrypt** (via `BcryptPasswordHasher`)
- **Email verification** is required — a verification link is sent via **Azure Email Client**
- Optional **Google reCAPTCHA v3** validation on registration
- Audit log entry is created on registration

### 3.2 Email Verification

- **Endpoint:** `POST /api/auth/verify-email`
- Token-based email verification flow
- **Resend verification:** `POST /api/auth/resend-verification`
- Anti-enumeration protection — always returns success message regardless of email existence

### 3.3 User Login

- **Endpoint:** `POST /api/auth/login`
- Supports login via **email** or **phone number** + password
- Successful login issues a **JWT access token** set as an **HTTP-only, secure cookie**
- JWT expiry is configurable via admin system settings
- Cookie settings (Secure, SameSite) are environment-aware (production vs. debug)
- Optional **reCAPTCHA** validation
- Session tracking via `PgUserSessionRepository` (IP address, user agent, channel)
- Audit log entry is created on login

### 3.4 User Logout

- **Endpoint:** `POST /api/auth/logout`
- Clears the authentication cookie
- Audit log entry is created on logout

### 3.5 User Profile Management

- **Get Profile:** `GET /api/auth/me` — Returns current authenticated user's profile
- **Update Profile:** `PATCH /api/auth/users/me` — Update first name, last name, email, preferred language, avatar URL
- **Upload Avatar:** `POST /api/auth/users/me/avatar` — Upload profile picture (supports local storage and Azure Blob Storage)
- **Change Password:** `POST /api/auth/change-password` — Requires current password verification

### 3.6 Authentication Middleware

- `AuthMiddleware` intercepts all requests and validates JWT tokens from cookies
- Injects user data (`request.state.user`) for downstream controllers
- Whitelists public routes (e.g., `/health`, `/docs`, `/api/auth/login`, `/api/auth/register`)

### 3.7 Frontend Auth

- Authentication state managed by **persisted Zustand store** (`authStore`) — no Context/Provider needed
- Cookie-based authentication with `withCredentials: true` on all Axios requests
- Path-based auth guards: `RequireAuth` for `/chat/*`, `RequireAdmin` for `/admin/*`
- **Login modal** component for unauthenticated users
- **Sign-up page** with full registration form
- **Email verification page** for post-registration flow

---

## 4. Conversational AI Chat

### 4.1 Conversation Management

| Endpoint | Method | Description |
|---|---|---|
| `/api/chats` | `POST` | Create a new conversation thread (with title and channel) |
| `/api/chats` | `GET` | List all conversations for the authenticated user (paginated) |
| `/api/chats/{id}` | `GET` | Get a specific conversation with all its messages |
| `/api/chats/{id}` | `PATCH` | Update conversation (title, archived/pinned status) |
| `/api/chats/{id}` | `DELETE` | Delete a conversation thread completely |
| `/api/chats/{id}/archive` | `PATCH` | Archive a conversation |
| `/api/chats/{id}/pin` | `PATCH` | Pin a conversation |

### 4.2 Messaging

| Endpoint | Method | Description |
|---|---|---|
| `/api/chats/{id}/messages` | `POST` | Add a new message to a conversation |
| `/api/chats/{id}/messages/complete` | `POST` | Generate an AI reply with streaming response |
| `/api/chats/{id}/messages/voice` | `POST` | Process voice note → transcribe → AI reply → synthesize audio |
| `/api/chats/{id}/messages/{msg_id}/audio` | `GET` | Get/synthesize audio for a voice message |

### 4.3 AI Response Generation

- **Streaming responses** via `StreamingResponse` — AI reply is generated token-by-token
- **LLMService** orchestrates the full pipeline:
  1. Query sanitization (prompt injection detection)
  2. Language detection (Unicode-based)
  3. Semantic cache check (cosine similarity in pgvector)
  4. Conversation history retrieval
  5. Multilingual prompt construction via `MultilingualPromptBuilder`
  6. RAG context augmentation from retrieved legal document chunks
  7. OpenAI GPT-4o streaming completion
  8. Semantic cache storage of new responses
  9. Token counting and telemetry logging
- **Non-streaming mode** available for document analysis and WhatsApp responses

### 4.4 Frontend Chat UI

- **ChatPage** — Main conversation interface with sidebar for conversation list
- **AnswerPage** — Displays AI responses with streaming token-by-token animation
- **ConversationComposer** — Rich text input with voice recording button
- **MarkdownText** — Renders AI responses with markdown formatting support
- **Sidebar** — Conversation list with search, pin, archive, and delete functionality
- **ChatLayout** — Wraps chat pages with sidebar navigation
- Chat state managed by `chatStore` (Zustand) — handles conversations, messages, streaming state

---

## 5. RAG Pipeline (Retrieval-Augmented Generation)

### 5.1 Document Ingestion

- **Upload:** `POST /api/documents` — Upload legal documents (PDF, TXT, DOCX)
- **Chunked Upload:** For large files:
  - `POST /api/documents/chunked/initialize` — Initialize upload session
  - `POST /api/documents/chunked/upload` — Upload individual chunks
  - `POST /api/documents/chunked/complete` — Merge chunks and process
- Supports metadata: title, document type, language, published year, collection ID
- Storage: **Local filesystem** or **Azure Blob Storage** (configurable)

### 5.2 Document Processing (RAG Service)

- **Trigger:** `POST /api/documents/{id}/process` — Runs in background
- **RAGService** pipeline:
  1. **Text Extraction** — `PyPDFLoader` (PDF), `TextLoader` (TXT) via LangChain
  2. **Text Chunking** — `RecursiveCharacterTextSplitter` with legal-domain separators (configurable chunk size/overlap via admin settings)
  3. **Embedding Generation** — OpenAI `text-embedding-3-large` (configurable model)
  4. **Vector Storage** — Embeddings stored as pgvector rows in `document_chunks` table
- Downloads files from Azure Blob Storage if configured, processes locally via temp files
- Logs embedding token usage and latency for cost tracking

### 5.3 Semantic Search (Retrieval Service)

- **RetrievalService** performs cosine similarity search against pgvector
- Configurable parameters (via admin system settings):
  - **Top-K** — Number of chunks to retrieve (default: 5)
  - **Similarity Threshold** — Minimum cosine similarity score (default: 0.7)
  - **Embedding Model** — OpenAI embedding model to use
- Confidence scoring: `"High"` (avg score ≥ 0.8), `"Medium"` (≥ 0.6), `"Low"` (< 0.6)
- Full telemetry logging: query embedding latency, search latency, total latency, confidence level

### 5.4 Document Management

| Endpoint | Method | Description |
|---|---|---|
| `/api/documents` | `GET` | List all documents (paginated, filterable by search, language, status, collection) |
| `/api/documents/stats` | `GET` | Get document statistics by status |
| `/api/documents/{id}` | `GET` | Get specific document metadata |
| `/api/documents/{id}/access` | `GET` | Get secure access URL (SAS token for Azure, FileResponse for local) |
| `/api/documents/{id}/chunks` | `GET` | Get all chunks for a document |
| `/api/documents/{id}` | `DELETE` | Delete document and its chunks |

### 5.5 Vector Cleanup Service

- `VectorCleanupService` identifies and removes orphaned and archived pgvector chunks
- Finds chunks referencing deleted documents
- Finds archived chunks older than configurable threshold (default: 30 days)
- Batch deletion for performance

---

## 6. Semantic Cache

- **pgvector-based response caching** to reduce LLM API costs and latency
- Before querying the LLM, the system generates an embedding of the user query and checks for semantically similar cached responses
- Cache hits return the stored response immediately
- Cache misses trigger the full RAG + LLM pipeline, and the new response is cached
- **Admin action:** `POST /api/admin/clear-semantic-cache` — Manually flush the entire cache
- Implemented via `PgVectorSemanticCacheRepository` using the `semantic_cache` table

---

## 7. Voice Interface (STT & TTS)

### 7.1 Speech-to-Text (STT)

- **SpeechToTextService** — Transcribes audio files using OpenAI Whisper API (`gpt-4o-mini-transcribe`)
- Supports multiple audio formats
- Used in both web voice messages and WhatsApp voice notes
- Handles Azure Blob Storage URLs (downloads to temp file for processing)
- Audio request logging with latency tracking

### 7.2 Text-to-Speech (TTS)

- **TextToSpeechService** — Synthesizes speech from text using OpenAI TTS API (`gpt-4o-mini-tts`)
- Used for AI audio responses in both web and WhatsApp channels
- Audio files persisted to **local filesystem** or **Azure Blob Storage**
- On-demand synthesis for messages without pre-generated audio
- Temporary files cleaned up after delivery

### 7.3 Voice Message Flow (Web)

1. User records voice note via **MediaRecorder API** in browser
2. Audio uploaded to `POST /api/chats/{id}/messages/voice`
3. Backend: STT transcription → RAG retrieval → LLM response → TTS synthesis
4. Persisted audio returned as response (redirect to Blob URL or direct FileResponse)
5. Both user and AI voice messages saved with `message_type="voice"` and `audio_path`

### 7.4 Frontend Voice Components

- **useVoiceRecording** hook — Full voice recording lifecycle (start, pause, resume, stop) with real-time audio level visualization using Web Audio API `AnalyserNode`
- **VoiceRecordingUI** — Recording interface with visual audio level feedback
- **VoiceMessagePlayer** — Audio playback component using **WaveSurfer.js** waveform visualization
- Voice state managed by `voiceStore` (Zustand)

---

## 8. WhatsApp Integration

### 8.1 Twilio Webhook

- **Endpoint:** `POST /api/whatsapp/webhook`
- Receives incoming WhatsApp messages from Twilio (text and voice notes)
- Returns empty TwiML response immediately — processing runs in background
- Prevents Twilio timeout (15-second requirement)

### 8.2 WhatsApp Service Pipeline

1. **User Lookup** — Matches incoming phone number to existing user, or auto-creates a new user
2. **Voice Note Handling** — Downloads Twilio media, transcribes via Whisper STT (with Twilio auth credentials)
3. **RAG Retrieval** — Fetches relevant legal context from pgvector
4. **LLM Response** — Generates legal answer via GPT-4o with conversation context
5. **Text Response** — Sends text reply via Twilio WhatsApp API
6. **Voice Response** — For voice notes: synthesizes TTS audio, persists to storage, sends audio URL via Twilio
7. **Conversation Tracking** — Creates/retrieves WhatsApp-specific conversations per user, saves all messages

### 8.3 Audio Handling

- Downloads Twilio voice notes with HTTP Basic Auth (Twilio SID/Token)
- Persists audio files to Azure Blob Storage or local filesystem
- Serves audio responses via public URLs for Twilio delivery
- MIME type fix for `.ogg` files on Windows

---

## 9. Document Analyzer

### 9.1 Document Analysis Service

- **Endpoint:** `POST /api/analyzer/document`
- Accepts uploaded documents (PDF, DOCX) with configurable analysis parameters:
  - **Document Type** — e.g., "General Document", "Contract", "Agreement"
  - **Analysis Type** — e.g., "Risk & Compliance", "Summary", "Key Terms"
  - **Custom Prompt** — Optional user-defined analysis instructions

### 9.2 Analysis Pipeline

1. **Text Extraction** — Extracts text from PDF (via `pypdf`) or DOCX (via `python-docx`)
2. **RAG Context Retrieval** — Uses the first 1000 characters as a query to retrieve relevant legal context from the knowledge base (with lower threshold of 0.6)
3. **Prompt Construction** — Builds analysis-specific prompts via `AnalyzerPrompts` template system
4. **Conversation Creation** — Creates a new chat conversation titled "Analysis: {filename}"
5. **LLM Analysis** — Generates comprehensive analysis via GPT-4o with the extracted text, legal context, and analysis instructions
6. **Result** — Returns the `conversation_id` so the frontend can redirect to the chat view with the analysis

### 9.3 Frontend Document Analyzer

- **DocumentAnalyzer** component — Upload interface with document type selection, analysis type dropdown, and custom prompt input
- Supports drag-and-drop file upload
- Redirects to chat conversation after analysis completes

---

## 10. Legal Library

### 10.1 Library Service

- **LibraryService** — Provides a browsable, organized view of ingested legal documents

### 10.2 Library Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/library/collections` | `GET` | Get document counts grouped by collection (e.g., "Acts", "Ordinances") |
| `/api/library/collections/{id}/letters` | `GET` | Get document counts grouped by starting letter within a collection |
| `/api/library/documents` | `GET` | List documents filtered by collection, starting letter, search query (paginated) |

### 10.3 Frontend Legal Library

- **LegalLibrary** component — Collection-based browsable directory
- Hierarchical navigation: Collections → Letters → Documents
- Search functionality within collections
- Document viewing with secure access URLs

---

## 11. Multilingual Support & Language Detection

### 11.1 Language Detection

- **LanguageDetectionService** — Unicode-based language detection without external dependencies
- Detects **Sinhala** (Unicode range `U+0D80–U+0DFF`), **Tamil** (`U+0B80–U+0BFF`), and **English** (Latin characters)
- Uses character percentage thresholds for reliable classification
- Falls back to English as default language

### 11.2 Multilingual Prompt System

- **MultilingualPromptBuilder** — Constructs language-specific system prompts for the LLM
- **PromptRegistry** — Versioned prompt templates for each supported language
- Dynamic language switching based on detected user language
- Fallback notice when user queries in a disabled language — response in configured default language

### 11.3 Frontend i18n

- **i18next** integration with full translation files for:
  - **English** (`en/`)
  - **Sinhala** (`si/`)
  - **Tamil** (`ta/`)
- `LanguageContext` — React Context provider managing language state
- `LanguageSelect` and `LanguageSwitcherButton` — UI components for language switching
- `i18next-browser-languagedetector` — Auto-detects browser language preference
- Per-user language preference synced to backend

---

## 12. Prompt Security & Safety

### 12.1 Prompt Injection Detection

- **PromptSecurityValidator** class with configurable validation (can be enabled/disabled via admin settings)
- Detects injection patterns:
  - `ignore previous/above/all instructions`
  - `disregard previous/above/instructions`
  - `new instructions:`
  - `system:` / `assistant:` role overrides
  - Special tokens (`<|...|>`)
  - Instruction tags (`[INST]...[/INST]`)

### 12.2 Input Sanitization

- Removes control characters (non-printable)
- Strips detected injection patterns
- Normalizes whitespace
- Applied before any LLM interaction

### 12.3 Neutral Language Validation

- Validates AI responses for prohibited legal advice phrases:
  - "you should", "you must", "i recommend", "my advice is"
  - "definitely", "certainly will", "guaranteed", "obviously", "clearly wrong"
- Ensures AI maintains neutral, informational tone (not legal advice)

### 12.4 Security Event Logging

- Security events are logged to `SecurityEventRepository`
- Tracked in the admin Security Monitoring dashboard

### 12.5 reCAPTCHA Integration

- **Google reCAPTCHA v3** verification on login and registration
- `GoogleRecaptchaVerifier` validates tokens server-side
- Configurable via `RECAPTCHA_SECRET_KEY` environment variable
- Frontend `useRecaptcha` hook for token management

---

## 13. Real-Time WebSocket Communication

### 13.1 WebSocket Chat Endpoint

- **Endpoint:** `WS /api/ws/chat/{conversation_id}`
- JWT-authenticated via query parameter token
- Validates user access to the specified conversation

### 13.2 Connection Management

- **ConnectionManager** — Tracks active WebSocket connections per user
- Handles connect/disconnect lifecycle
- Supports multiple connections per user

### 13.3 Rate Limiting

- **WebSocket Rate Limiter** — Prevents message flooding
- Configurable rate limit per minute (via admin system settings)
- Returns `rate_limit_exceeded` error when exceeded

### 13.4 Message Types

| Type | Direction | Description |
|---|---|---|
| `ping` | Client → Server | Keep-alive heartbeat |
| `pong` | Server → Client | Heartbeat response |
| `chat_message` | Client → Server | User sends a message |
| `chat_chunk` | Server → Client | Streaming AI response token |
| `chat_completion` | Server → Client | AI response complete signal |
| `connection_established` | Server → Client | Initial connection confirmation |
| `error` | Server → Client | Error notification |

### 13.5 WebSocket AI Pipeline

- Receives `chat_message` → RAG retrieval → LLM streaming → sends `chat_chunk` tokens → sends `chat_completion`
- Full error handling with error messages sent back to client

### 13.6 Frontend Socket Integration

- **Socket.IO Client** integration via `socketService`
- Socket configuration in `socket.config.ts`
- Real-time updates and notifications

---

## 14. Admin Dashboard & Analytics

### 14.1 Admin Overview

- **Endpoint:** `GET /api/admin/overview`
- **AdminOverviewService** — Aggregates top-level platform statistics:
  - Total users, active users, conversations, messages
  - Documents uploaded and processed
  - LLM request counts
  - Recent activity feed
  - Audit log entries

### 14.2 User Management

- **List Users:** `GET /api/admin/users` — Paginated with search, role filter, status filter
- **Create Admin User:** `POST /api/admin/users` — Create new admin accounts
- **Update User Status:** `PATCH /api/admin/users/{id}/status` — Activate/deactivate users
- Audit logging for all admin actions

### 14.3 Knowledge Base Management

- **Endpoint:** `GET /api/admin/knowledge`
- **AdminKnowledgeService** — Document/chunk statistics and status monitoring

### 14.4 Logs Management

- **List Logs:** `GET /api/admin/logs` — View LLM request logs, audio logs, and retrieval logs
- **Update Log Status:** `PATCH /api/admin/logs/{id}/status`
- **Delete Log:** `DELETE /api/admin/logs/{id}`
- **AdminLogsService** — Aggregates logs from `PgLLMLogRepository`, `PgAudioLogRepository`, and `PgRetrievalLogRepository`

### 14.5 Analytics Modules

#### Platform Analytics
- **Endpoint:** `GET /api/admin/platform-analytics`
- Message volume trends, conversation statistics
- Channel distribution (web, WhatsApp, voice)

#### Usage Analytics
- **Endpoint:** `GET /api/admin/usage-analytics`
- User activity metrics, chat frequency, active user trends

#### Cost Analytics
- **Endpoint:** `GET /api/admin/cost-analytics`
- **AdminCostAnalyticsService** — Comprehensive LLM cost tracking:
  - Token usage by model (prompt/completion/total)
  - Cost calculations per model
  - Daily/weekly/monthly cost trends
  - Cost breakdown by channel and language

#### Multilingual Analytics
- **Endpoint:** `GET /api/admin/multilingual-analytics`
- Language distribution across conversations
- Per-language message and conversation counts

#### Retrieval Evaluation
- **Endpoint:** `GET /api/admin/analytics/retrieval-evaluation`
- RAG retrieval quality metrics from `RetrievalEvaluationRepository`

#### AI Evaluation Metrics
- **Endpoint:** `GET /api/admin/analytics/ai-evaluation`
- Model accuracy, hallucination rates, average token usage
- Computed by the background `AIEvaluationPipelineService`

#### Research Metrics
- **Endpoint:** `GET /api/admin/analytics/research-metrics`
- Experiment notes, dataset evaluation results (BLEU, ROUGE-L, context recall, faithfulness, answer relevance)

### 14.6 Monitoring

#### Retrieval Monitoring
- **Endpoint:** `GET /api/admin/retrieval-monitoring`
- **AdminRetrievalService** — Real-time RAG pipeline health:
  - Document/chunk counts and status
  - Embedding statistics
  - Retrieval performance metrics

#### Security Monitoring
- **Endpoint:** `GET /api/admin/security-monitoring`
- **AdminSecurityMonitoringService** — Security event tracking:
  - Prompt injection attempts
  - Authentication failures
  - Audit log analysis

#### Error Monitoring
- **Endpoint:** `GET /api/admin/error-monitoring`
- **AdminErrorMonitoringService** — System error tracking from `PgSystemErrorRepository`
  - Error list with pagination
  - Error categorization and severity

### 14.7 Frontend Admin Pages

| Page | Description |
|---|---|
| `AdminDashboard` | Main dashboard with overview stats, activity feed, data source status |
| `UserManagementPage` | User list with search, filter, status toggle, and admin creation |
| `KnowledgeBasePage` | Knowledge base metrics and document management |
| `AdminDataSourcesPage` | Data source monitoring and management |
| `AdminLogsPage` | System logs viewer with status management |
| `AnalyticsPage` | Analytics module hub |
| `PlatformAnalyticsPage` | Platform usage charts and trends |
| `UsageAnalyticsPage` | User activity analytics |
| `CostAnalyticsPage` | LLM cost breakdowns and trends |
| `MultilingualAnalyticsPage` | Language distribution analytics |
| `RetrievalEvaluationPage` | RAG quality metrics |
| `AIEvaluationMetricsPage` | AI model performance metrics |
| `ResearchMetricsPage` | Research evaluation results and experiment notes |
| `RetrievalMonitoringPage` | RAG pipeline health monitoring |
| `SecurityMonitoringPage` | Security event monitoring |
| `ErrorMonitoringPage` | System error monitoring |
| `HealthStatusPage` | System health status |
| `SettingsPage` | Admin system settings hub |

---

## 15. System Settings Management

### 15.1 Language Settings

- **GET/PATCH** `/api/admin/settings/language`
- Configure enabled languages, default language, translation pipeline toggle

### 15.2 AI Settings

- **GET/PATCH** `/api/admin/settings/ai`
- Configure: AI model name, temperature, max tokens, top_p, frequency penalty

### 15.3 Retrieval Settings

- **GET/PATCH** `/api/admin/settings/retrieval`
- Configure: Top-K results, similarity threshold, embedding model, chunk size, chunk overlap

### 15.4 Integration Settings

- **GET/PATCH** `/api/admin/settings/integration`
- Configure: OpenAI API key, Twilio credentials (SID, auth token), WhatsApp phone number, WebSocket URL

### 15.5 Security Settings

- **GET/PATCH** `/api/admin/settings/security`
- Configure: JWT expiry minutes, rate limit per minute, prompt validation toggle, account lockout threshold

### 15.6 Frontend Settings Pages

| Page | Description |
|---|---|
| `LanguageSettingsPage` | Manage enabled languages and defaults |
| `AISettingsPage` | Configure AI model parameters |
| `RetrievalSettingsPage` | Configure RAG retrieval parameters |
| `IntegrationSettingsPage` | Manage API keys and external service credentials |
| `SecuritySettingsPage` | Configure security policies |
| `PrivacySettingsPage` | Privacy-related settings |

### 15.7 Settings Persistence

- All settings stored in `system_settings` table via `SystemSettingsRepository`
- Settings are loaded dynamically at runtime — no server restart required
- Changes are audit-logged with the admin user who made the change

---

## 16. Research & Evaluation Framework

### 16.1 Dataset Evaluation Service

- Upload Q&A evaluation datasets (CSV with question, golden_answer, golden_context)
- Run automated evaluations computing:
  - **BLEU** — Unigram overlap precision
  - **ROUGE-L** — Longest common subsequence recall
  - **Context Recall** — Golden context token overlap with retrieved context
  - **Faithfulness** — LLM-as-a-Judge evaluation (is the response faithful to context?)
  - **Answer Relevance** — LLM-as-a-Judge evaluation (is the response relevant to the query?)

### 16.2 LLM-as-a-Judge Service

- `LLMAsAJudgeService` — Uses GPT-4o as an impartial judge to evaluate:
  - **Faithfulness** — Whether response claims can be inferred from context
  - **Answer Relevance** — Whether response directly addresses the query
- Returns float scores between 0.0 and 1.0

### 16.3 Research Management Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/admin/research/datasets/upload` | `POST` | Upload evaluation dataset (CSV) |
| `/api/admin/research/datasets/{id}/evaluate` | `POST` | Trigger background evaluation |
| `/api/admin/research/datasets/{id}` | `DELETE` | Delete a dataset and its results |

### 16.4 Experiment Notes

- Persistent experiment notes stored in database
- Tracks ablation studies and prompt variant experiments
- Displayed on the Research Metrics admin page

---

## 17. Background Task Pipeline

### 17.1 AI Evaluation Pipeline

- **AIEvaluationPipelineService** — Runs on a configurable interval (default: 600 seconds / 10 minutes)
- Computes per-model evaluation metrics:
  - Average token usage
  - Accuracy (weighted by confidence levels)
  - Hallucination rate
- Stores results in `ai_evaluations` table
- Managed via FastAPI `lifespan` context manager
- Graceful shutdown with task cancellation

### 17.2 Document Processing

- RAG document processing runs as FastAPI `BackgroundTasks`
- Triggered manually via `POST /api/documents/{id}/process`

### 17.3 WhatsApp Message Processing

- Incoming WhatsApp messages processed as `BackgroundTasks`
- Ensures immediate 200 OK response to Twilio webhook

### 17.4 Temporary File Management

- **TempFileManager** — Handles temporary audio/document files
- Immediate cleanup after processing
- Manages Twilio audio downloads with authentication

---

## 18. Telemetry & Logging

### 18.1 LLM Request/Response Logging

- `PgLLMLogRepository` — Logs every LLM interaction:
  - Model name, query, context, response
  - Token counts (prompt, completion, total)
  - Latency, cache status
  - Conversation and user association
  - Confidence level

### 18.2 Audio Request Logging

- `PgAudioLogRepository` — Logs every STT/TTS operation:
  - Audio type (STT/TTS), language, duration
  - Provider information
  - User association

### 18.3 Retrieval Logging

- `PgRetrievalLogRepository` — Logs every retrieval operation:
  - Query, number of results, confidence
  - Embedding latency, search latency, total latency
  - Model used

### 18.4 Audit Logging

- `PgAuditLogRepository` — Logs administrative and security-relevant actions:
  - Login/logout events
  - User management actions
  - Settings changes

### 18.5 System Error Logging

- `PgSystemErrorRepository` — Captures and stores system-level errors
- `log_system_error` utility function for consistent error logging
- Displayed on the Error Monitoring admin page

### 18.6 Security Event Logging

- `SecurityEventRepository` — Logs security events:
  - Prompt injection detections
  - Authentication failures
  - Suspicious activity

---

## 19. Frontend Features & UI

### 19.1 Pages

| Page | Path | Description |
|---|---|---|
| `HomePage` | `/` | Landing page with feature cards and call-to-action |
| `ChatPage` | `/chat` | Main chat interface |
| `AnswerPage` | `/chat/{id}` | Individual conversation view with AI responses |
| `SignUpPage` | `/signup` | User registration form |
| `VerifyEmailPage` | `/verify-email` | Email verification flow |
| `TopicBrowserPage` | `/topics` | Browse curated legal topic categories |
| `DeveloperPage` | `/developer` | Developer information |
| `ResearchPage` | `/research` | Research information |
| `SettingsPage` | `/settings` | User settings (theme, language, profile) |
| `AboutUsPage` | `/about` | About the platform |
| `ContactPage` | `/contact` | Contact information |
| `HelpPage` | `/help` | Help and FAQ |
| `ReleaseNotesPage` | `/release-notes` | Version history and changelog |
| `PrivacyPolicyPage` | `/privacy-policy` | Privacy policy |
| `TermsOfServicePage` | `/terms-of-service` | Terms of service |
| `NotFoundPage` | `*` | 404 error page |

### 19.2 Layouts

| Layout | Scope | Description |
|---|---|---|
| `MainLayout` | Public pages | Standard layout with navbar |
| `ChatLayout` | Chat pages | Chat-specific layout with sidebar |
| `AdminLayout` | Admin pages | Admin panel layout with admin sidebar |
| `BrowseLayout` | Browse/topics | Browse header with navigation |
| `PrivacyPolicyLayout` | Legal pages | Specialized layout for legal documents |

### 19.3 Theme System

- **Dark/Light mode** with system preference detection
- `ThemeContext` — React Context provider for theme management
- `ThemeToggleButton` — UI toggle component
- Accent color customization
- Theme preference persisted to `localStorage`

### 19.4 UI Components

| Component | Description |
|---|---|
| `LoginModal` | Modal dialog for user authentication |
| `ProfileModal` | User profile management with avatar upload |
| `SettingsModal` | Quick settings access modal |
| `ChatActionModal` | Conversation action menu (rename, archive, pin, delete) |
| `BrandLogo` | Application branding component |
| `ConstellationBackground` | Animated constellation background effect |
| `FeatureCard` | Feature showcase card for landing page |
| `TopicCard` | Legal topic category card |
| `LanguageSelect` | Language dropdown selector |
| `LanguageSwitcherButton` | Floating language toggle |
| `VoiceMessagePlayer` | Audio playback with WaveSurfer.js waveform |
| `VoiceRecordingUI` | Voice recording interface with level visualization |
| `DocumentAnalyzer` | Document upload and analysis interface |
| `LegalLibrary` | Browsable legal document directory |
| `LawyerDirectory` | Lawyer directory listing |

### 19.5 State Management (Zustand Stores)

| Store | Responsibilities |
|---|---|
| `authStore` | Authentication state, user data, login/logout, token management |
| `chatStore` | Conversations, messages, streaming state, search, archive/pin |
| `voiceStore` | Voice recording state |
| `uiStore` | UI state (sidebar open/closed, etc.) |
| `notificationStore` | Notification management |
| `adminStore` | Admin dashboard state |
| `adminUsersStore` | Admin user management state |
| `adminDataSourcesStore` | Admin data source state |
| `adminKnowledgeStore` | Admin knowledge base state |
| `libraryStore` | Legal library browsing state |

### 19.6 API Service Layer

| Service | Scope |
|---|---|
| `apiClient` | Axios instance with interceptors and credentials |
| `authService` | Login, register, logout, profile API calls |
| `chatService` | Conversation and message API calls |
| `adminService` | Admin analytics and monitoring API calls |
| `adminDataSourcesService` | Data source management API calls |
| `adminKnowledgeService` | Knowledge base management API calls |
| `analyzerService` | Document analysis API calls |
| `libraryService` | Legal library browsing API calls |
| `socketService` | Socket.IO connection management |

### 19.7 Custom Hooks

| Hook | Purpose |
|---|---|
| `useVoiceRecording` | Voice recording lifecycle with Web Audio API visualization |
| `useRecaptcha` | Google reCAPTCHA token management |
| `useTheme` | Theme state access (via ThemeContext) |
| `useSettingsModal` | Settings modal open/close state |

---

## 20. Deployment & DevOps

### 20.1 Backend Deployment

- **Dockerfile** — Multi-stage Docker build for containerized deployment
- **GitHub Actions** (`deploy.yml`) — CI/CD pipeline for backend deployment
- **Azure Container Apps** — Target deployment platform
- **Health check:** `GET /health` — Liveness/readiness probe for Azure
- Swagger/ReDoc documentation disabled in production (`DEBUG=False`)
- Static file mounts for media, temp audio, and uploads

### 20.2 Frontend Deployment

- **Azure Static Web Apps** — Deployment via GitHub Actions workflow
- `staticwebapp.config.json` — SPA routing configuration (fallback to `index.html`)
- Production build: `npm run build` (TypeScript check + Vite production bundle)

### 20.3 Storage

- **Development:** Local filesystem for documents and audio
- **Production:** Azure Blob Storage with SAS token generation for secure access
- Automatic detection based on environment variables (`AZURE_STORAGE_CONNECTION_STRING`)

### 20.4 Environment Configuration

- **Backend:** `.env` with pydantic-settings validation
- **Frontend:** `.env` with Vite environment variables (`VITE_API_BASE_URL`, `VITE_SOCKET_URL`)
- Production examples provided in `.env.production.example` files

---

## 21. API Route Summary

All backend routes are mounted under the `/api` prefix:

| Module | Prefix | Endpoints |
|---|---|---|
| **Auth** | `/api/auth` | Login, register, verify-email, resend-verification, logout, profile, avatar, change-password |
| **Chat** | `/api/chats` | CRUD conversations, messages, AI completions, voice messages, audio retrieval |
| **Documents** | `/api/documents` | Upload (standard + chunked), list, get, process, access, chunks, delete, stats |
| **Analyzer** | `/api/analyzer` | Document analysis with AI |
| **Library** | `/api/library` | Collections, letters, document browsing |
| **Admin** | `/api/admin` | Overview, users, knowledge, logs, analytics (6 types), monitoring (3 types), settings (5 categories), research, cache management |
| **WhatsApp** | `/api/whatsapp` | Twilio webhook for incoming messages/voice |
| **WebSocket** | `/api/ws` | Real-time streaming AI responses |
| **Health** | `/health` | Liveness/readiness probe |

Additional static mounts:
- `/media/*` — Persisted audio files
- `/temp/*` — Temporary TTS audio files
- `/uploads/*` — Uploaded documents

---

## 22. Database Models

The system uses **20 SQLAlchemy ORM models** backed by PostgreSQL + pgvector:

| Model | Table | Description |
|---|---|---|
| `User` | `users` | User accounts with role, language preference, avatar, verification status |
| `UserSession` | `user_sessions` | Login session tracking (IP, user agent, channel) |
| `Conversation` | `conversations` | Chat conversation threads (title, channel, pinned, archived) |
| `Message` | `messages` | Individual messages (content, sender, type, audio path) |
| `Document` | `documents` | Ingested legal documents (title, type, language, storage path, status) |
| `DocumentChunk` | `document_chunks` | Text chunks with pgvector embeddings |
| `SemanticCache` | `semantic_cache` | Cached query-response pairs with embeddings |
| `LLMRequest` | `llm_requests` | LLM API request logs (model, tokens, latency, query, context) |
| `LLMResponse` | `llm_responses` | LLM API response logs (response text, confidence) |
| `AudioRequest` | `audio_requests` | STT/TTS operation logs |
| `AuditLog` | `audit_logs` | Administrative action audit trail |
| `RetrievalLog` | `retrieval_logs` | Retrieval operation logs (query, results, latency) |
| `RetrievedDocument` | `retrieved_documents` | Individual retrieved document records per retrieval |
| `SecurityEvent` | `security_events` | Security incident records |
| `SystemError` | `system_errors` | System error records |
| `SystemSettings` | `system_settings` | Dynamic system configuration |
| `AIEvaluation` | `ai_evaluations` | AI model evaluation metrics |
| `RetrievalEvaluation` | `retrieval_evaluations` | RAG retrieval quality evaluations |
| `Research` | `research` | Research datasets and metrics |
| `ExperimentNote` | `experiment_notes` | Research experiment notes |

---

## 23. Architecture Summary

### Clean Architecture (4 Layers)

```
┌─────────────────────────────────────────────────────────────────┐
│  PRESENTATION LAYER                                              │
│  8 Controllers · Pydantic Schemas · JWT Middleware · WebSocket    │
│  Error Handlers · Route Configuration · Lifespan Management      │
├─────────────────────────────────────────────────────────────────┤
│  APPLICATION LAYER                                               │
│  34 Service Modules · Frozen DTOs · Versioned Prompts            │
│  PromptRegistry · MultilingualPromptBuilder · AppError           │
├─────────────────────────────────────────────────────────────────┤
│  INFRASTRUCTURE LAYER                                            │
│  15 Repositories · 20 ORM Models · Security Handlers             │
│  OpenAI Client · Twilio Client · Azure Email Client              │
│  WebSocket Manager · Rate Limiter · Storage Handlers             │
│  Logger Configuration                                            │
├─────────────────────────────────────────────────────────────────┤
│  DOMAIN LAYER                                                    │
│  Entities (User) · 17 Abstract Interfaces (Ports)                │
│  Value Objects · Domain Exceptions                               │
└─────────────────────────────────────────────────────────────────┘
```

### High-Level System Flow

```
User (React Web / Twilio WhatsApp / Voice)
        ↓
FastAPI Backend (Controllers & WebSocket)
        ↓
RAG Engine & Services (LangChain + OpenAI)
        ↓
Database (PostgreSQL + pgvector) & Storage (Local / Azure Blob)
```

---

> **Disclaimer:** OpenJustice is an AI-powered educational tool. It provides legal information, not legal advice or representation. Users should cross-reference all outputs with primary source documents and consult a qualified attorney for specific legal situations.
