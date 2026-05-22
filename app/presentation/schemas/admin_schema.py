from typing import List, Optional
from pydantic import BaseModel

class StatItem(BaseModel):
    id: int
    title: str
    value: str
    change: str
    statusType: str

class ActivityItem(BaseModel):
    id: int
    title: str
    description: str
    timeAgo: str
    icon: str
    iconColorClass: str

class ServiceStatusItem(BaseModel):
    id: int
    title: str
    status: str
    icon: str

class DailyQueryStat(BaseModel):
    date: str
    count: int
    heightPercentage: str

class DataSourceItem(BaseModel):
    id: int
    title: str
    statusLabel: str
    statusColorClass: str
    progressPercent: int
    footerText: str
    progressColorClass: Optional[str] = None

class AdminOverviewResponse(BaseModel):
    stats: List[StatItem]
    activities: List[ActivityItem]
    core_services: List[ServiceStatusItem]
    data_sources: List[DataSourceItem]
    queries_per_day: List[DailyQueryStat]

class AdminUserItem(BaseModel):
    id: str
    email: str
    status: str
    createdDate: str

class AdminUserListResponse(BaseModel):
    users: List[AdminUserItem]
    total_active: int
    total_blocked: int

class AdminUserStatusUpdate(BaseModel):
    is_active: bool

class AdminKnowledgeRecord(BaseModel):
    documentId: str
    documentTitle: str
    chunkCount: int
    embeddingModel: str
    status: str

class AdminKnowledgeResponse(BaseModel):
    records: List[AdminKnowledgeRecord]

class AdminTraceLog(BaseModel):
    id: str
    correlationId: str
    eventType: str
    model: str
    promptVersion: str
    language: str
    promptTokens: int
    completionTokens: int
    latencyMs: int
    retrievalCount: int
    citationCount: int
    status: str
    timestamp: str

class AdminLogListResponse(BaseModel):
    logs: List[AdminTraceLog]
    total: int

class AdminLogStatusUpdate(BaseModel):
    status: str
