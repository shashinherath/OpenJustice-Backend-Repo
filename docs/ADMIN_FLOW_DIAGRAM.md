# Admin Flow Diagram

## Overview

This document maps the complete admin journey through the OpenJustice admin panel — from the dashboard overview to analytics, user management, knowledge base monitoring, and system configuration.

---

## 🏠 Admin Dashboard Overview

The admin dashboard (`/admin`) is the central hub that aggregates system-wide statistics.

```mermaid
flowchart TD
    A["Admin logs in"] --> B["Navigate to /admin"]
    B --> C["GET /api/admin/overview"]
    C --> D["AdminOverviewService.get_overview_stats()"]
    D --> E["Aggregate from multiple repositories"]

    E --> F["UserRepository — total users, active users"]
    E --> G["ChatRepository — total conversations, messages"]
    E --> H["DocumentRepository — total documents, chunks"]
    E --> I["PgLLMLogRepository — total LLM calls, error count"]
    E --> J["PgAuditLogRepository — recent activities"]

    F & G & H & I & J --> K["AdminOverviewResponse"]
    K --> L["Dashboard renders stats cards"]

    style A fill:#1a1a2e,color:#e0e0ff
    style L fill:#0f3460,color:#e0e0ff
```

---

## 👥 User Management Flow

Admins can view all registered users and toggle their active status.

```mermaid
flowchart TD
    A["Admin navigates to /admin/users"] --> B["GET /api/admin/users?skip=0&limit=100"]
    B --> C["AdminUsersService.get_users()"]
    C --> D["UserRepository — fetch paginated users"]
    D --> E["Render user list with status"]

    E --> F["Admin clicks toggle status"]
    F --> G["PATCH /api/admin/users/:user_id/status"]
    G --> H["AdminUsersService.update_user_status()"]
    H --> I{"User found?"}
    I -->|Yes| J["Update is_active flag"]
    I -->|No| K["404 Not Found"]
    J --> L["Return updated AdminUserItem"]

    style A fill:#1a1a2e,color:#e0e0ff
    style L fill:#0f3460,color:#e0e0ff
```

---

## 📚 Knowledge Base & Document Management Flow

Admins manage the legal document knowledge base — upload, process, and monitor documents.

```mermaid
flowchart TD
    A["Admin navigates to /admin/data-sources"] --> B["GET /api/documents"]
    B --> C["DocumentService.list_documents()"]
    C --> D["Show document list with status"]

    D --> E{"Admin Action?"}

    E -->|Upload| F["POST /api/documents"]
    F --> G["DocumentService.ingest_document()"]
    G --> H["Save file to uploads/"]
    H --> I["Create Document record in DB"]

    E -->|Process| J["POST /api/documents/:id/process"]
    J --> K["BackgroundTasks.add_task()"]
    K --> L["RAGService.process_and_store_document()"]
    L --> M["LangChain: Load → Split → Embed"]
    M --> N["Store DocumentChunks with pgvector embeddings"]
    N --> O["Update status: Processed or Failed"]

    E -->|Delete| P["DELETE /api/documents/:id"]
    P --> Q["Remove file + DB record + chunks"]

    E -->|Monitor| R["GET /api/admin/knowledge"]
    R --> S["AdminKnowledgeService.get_knowledge_metrics()"]
    S --> T["Document counts, chunk stats, language breakdown"]

    style A fill:#1a1a2e,color:#e0e0ff
    style N fill:#0f3460,color:#e0e0ff
    style T fill:#16213e,color:#e0e0ff
```

---

## 🔍 Retrieval Monitoring Flow

Monitor RAG pipeline performance — how documents are being retrieved and used.

```mermaid
flowchart TD
    A["Admin navigates to /admin/retrieval-monitoring"] --> B["GET /api/admin/retrieval-monitoring"]
    B --> C["AdminRetrievalService.get_retrieval_monitoring()"]
    C --> D["Query retrieval_logs + retrieved_documents"]
    D --> E["Calculate retrieval metrics"]

    E --> F["Total retrieval queries"]
    E --> G["Average chunks returned per query"]
    E --> H["Top retrieved documents"]
    E --> I["Retrieval success rate"]

    F & G & H & I --> J["Render retrieval monitoring dashboard"]

    style A fill:#1a1a2e,color:#e0e0ff
    style J fill:#0f3460,color:#e0e0ff
```

---

## 📋 LLM Logs Management Flow

View, filter, and manage LLM request/response logs for debugging and research.

```mermaid
flowchart TD
    A["Admin navigates to /admin/logs"] --> B["GET /api/admin/logs?skip=0&limit=100"]
    B --> C["AdminLogsService.get_logs()"]
    C --> D["PgLLMLogRepository.get_logs()"]
    D --> E["Return paginated LLMRequest records"]
    E --> F["Render log table with query, model, tokens, latency, status"]

    F --> G{"Admin Action?"}

    G -->|Update Status| H["PATCH /api/admin/logs/:log_id/status"]
    H --> I["PgLLMLogRepository.update_log_status()"]
    I --> J["Mark as reviewed/flagged"]

    G -->|Delete| K["DELETE /api/admin/logs/:log_id"]
    K --> L["PgLLMLogRepository.delete_log()"]
    L --> M["Remove log entry"]

    style A fill:#1a1a2e,color:#e0e0ff
    style F fill:#0f3460,color:#e0e0ff
```

---

## 🛡️ Security Monitoring Flow

Monitor security events and prompt injection attempts.

```mermaid
flowchart TD
    A["Admin navigates to /admin/security-monitoring"] --> B["GET /api/admin/security-monitoring"]
    B --> C["AdminSecurityMonitoringService.get_security_monitoring()"]
    C --> D["SecurityEventRepository — query security_events"]
    D --> E["Aggregate threat data"]

    E --> F["Total security events"]
    E --> G["Prompt injection attempts"]
    E --> H["Event severity breakdown"]
    E --> I["Recent security incidents"]

    F & G & H & I --> J["Render security monitoring dashboard"]

    style A fill:#1a1a2e,color:#e0e0ff
    style J fill:#0f3460,color:#e0e0ff
```

---

## 📊 Analytics Flow

The analytics section provides multiple views into platform performance, usage, costs, and research metrics.

```mermaid
flowchart TD
    A["Admin navigates to /admin/analytics"] --> B["Analytics Hub Page"]

    B --> C["/admin/analytics/platforms"]
    C --> C1["GET /api/admin/platform-analytics"]
    C1 --> C2["AdminPlatformAnalyticsService"]
    C2 --> C3["Conversations by channel, daily activity trends"]

    B --> D["/admin/analytics/usage"]
    D --> D1["GET /api/admin/usage-analytics"]
    D1 --> D2["AdminUsageAnalyticsService"]
    D2 --> D3["Messages per user, peak hours, retention"]

    B --> E["/admin/analytics/cost"]
    E --> E1["GET /api/admin/cost-analytics"]
    E1 --> E2["AdminCostAnalyticsService"]
    E2 --> E3["Token usage, estimated API costs, cost per query"]

    B --> F["/admin/analytics/multilingual"]
    F --> F1["GET /api/admin/multilingual-analytics"]
    F1 --> F2["AdminMultilingualAnalyticsService"]
    F2 --> F3["Language distribution, Sinhala/Tamil/English usage"]

    B --> G["/admin/analytics/retrieval-evaluation"]
    G --> G1["GET /api/admin/analytics/retrieval-evaluation"]
    G1 --> G2["AdminRetrievalEvaluationService"]
    G2 --> G3["Retrieval accuracy, precision, recall metrics"]

    B --> H["/admin/analytics/ai-evaluation"]
    H --> H1["GET /api/admin/analytics/ai-evaluation"]
    H1 --> H2["AdminAIEvaluationService"]
    H2 --> H3["AI response quality, citation accuracy, evaluation scores"]

    B --> I["/admin/analytics/research-metrics"]
    I --> I1["GET /api/admin/analytics/research-metrics"]
    I1 --> I2["AdminResearchService"]
    I2 --> I3["Research interaction data, model performance metrics"]

    style A fill:#1a1a2e,color:#e0e0ff
    style B fill:#533483,color:#e0e0ff
```

---

## ⚙️ System Operations Flow

```mermaid
flowchart TD
    A["Admin Actions"] --> B{"Operation?"}

    B -->|Clear Semantic Cache| C["POST /api/admin/clear-semantic-cache"]
    C --> D["DELETE FROM semantic_cache"]
    D --> E["Force fresh LLM responses for all queries"]

    B -->|Admin Settings| F["Navigate to /admin/settings"]
    F --> G["/admin/settings/language — Language config"]
    F --> H["/admin/settings/ai — AI model config"]
    F --> I["/admin/settings/retrieval — RAG settings"]
    F --> J["/admin/settings/security — Security config"]
    F --> K["/admin/settings/privacy — Privacy settings"]
    F --> L["/admin/settings/integration — Integration config"]

    style A fill:#1a1a2e,color:#e0e0ff
    style E fill:#0f3460,color:#e0e0ff
```

---

## 🗺️ Complete Admin Navigation Map

```mermaid
flowchart TD
    ADMIN["/admin — Dashboard Overview"] --> USERS["/admin/users — User Management"]
    ADMIN --> DATA["/admin/data-sources — Document Upload"]
    ADMIN --> KNOWLEDGE["/admin/knowledge-monitoring — Knowledge Base"]
    ADMIN --> RETRIEVAL["/admin/retrieval-monitoring — Retrieval Monitoring"]
    ADMIN --> SECURITY["/admin/security-monitoring — Security Monitoring"]
    ADMIN --> LOGS["/admin/logs — LLM Logs"]
    ADMIN --> ERRORS["/admin/error-monitoring — Error Monitoring"]
    ADMIN --> ANALYTICS["/admin/analytics — Analytics Hub"]
    ADMIN --> SETTINGS["/admin/settings — Settings"]

    ANALYTICS --> A1["/admin/analytics/platforms"]
    ANALYTICS --> A2["/admin/analytics/usage"]
    ANALYTICS --> A3["/admin/analytics/cost"]
    ANALYTICS --> A4["/admin/analytics/multilingual"]
    ANALYTICS --> A5["/admin/analytics/retrieval-evaluation"]
    ANALYTICS --> A6["/admin/analytics/ai-evaluation"]
    ANALYTICS --> A7["/admin/analytics/research-metrics"]

    SETTINGS --> S1["/admin/settings/language"]
    SETTINGS --> S2["/admin/settings/ai"]
    SETTINGS --> S3["/admin/settings/retrieval"]
    SETTINGS --> S4["/admin/settings/security"]
    SETTINGS --> S5["/admin/settings/privacy"]
    SETTINGS --> S6["/admin/settings/integration"]

    style ADMIN fill:#1a1a2e,color:#e0e0ff
    style ANALYTICS fill:#533483,color:#e0e0ff
    style SETTINGS fill:#0f3460,color:#e0e0ff
```

---

## 📡 Admin API Endpoints Summary

| Endpoint | Method | Service | Purpose |
|---|---|---|---|
| `/api/admin/overview` | GET | `AdminOverviewService` | Dashboard statistics |
| `/api/admin/users` | GET | `AdminUsersService` | List all users |
| `/api/admin/users/:id/status` | PATCH | `AdminUsersService` | Toggle user active status |
| `/api/admin/knowledge` | GET | `AdminKnowledgeService` | Knowledge base metrics |
| `/api/admin/retrieval-monitoring` | GET | `AdminRetrievalService` | RAG retrieval stats |
| `/api/admin/security-monitoring` | GET | `AdminSecurityMonitoringService` | Security events |
| `/api/admin/logs` | GET | `AdminLogsService` | Paginated LLM logs |
| `/api/admin/logs/:id/status` | PATCH | `AdminLogsService` | Update log status |
| `/api/admin/logs/:id` | DELETE | `AdminLogsService` | Delete log entry |
| `/api/admin/clear-semantic-cache` | POST | Direct DB delete | Clear semantic cache |
| `/api/admin/platform-analytics` | GET | `AdminPlatformAnalyticsService` | Platform usage |
| `/api/admin/usage-analytics` | GET | `AdminUsageAnalyticsService` | User engagement |
| `/api/admin/cost-analytics` | GET | `AdminCostAnalyticsService` | API cost tracking |
| `/api/admin/multilingual-analytics` | GET | `AdminMultilingualAnalyticsService` | Language stats |
| `/api/admin/analytics/retrieval-evaluation` | GET | `AdminRetrievalEvaluationService` | RAG evaluation |
| `/api/admin/analytics/ai-evaluation` | GET | `AdminAIEvaluationService` | AI quality metrics |
| `/api/admin/analytics/research-metrics` | GET | `AdminResearchService` | Research metrics |

---

## 🔄 Background Evaluation Pipeline

An automated evaluation pipeline runs continuously in the background via the application lifespan:

```mermaid
flowchart LR
    A["App Startup"] --> B["lifespan() context manager"]
    B --> C["asyncio.create_task()"]
    C --> D["background_evaluation_worker()"]
    D --> E["Run every 600 seconds"]
    E --> F["Evaluate AI response quality"]
    F --> G["Store results in ai_evaluations table"]
    G --> E

    style A fill:#1a1a2e,color:#e0e0ff
    style D fill:#0f3460,color:#e0e0ff
```

```python
# app/presentation/lifespan.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(background_evaluation_worker(interval_seconds=600))
    yield
    task.cancel()
```

---

_Last updated: June 2026_
