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

class RetrievalMetric(BaseModel):
    label: str
    value: str
    note: str
    tone: str

class TrendPoint(BaseModel):
    label: str
    value: int

class HealthTargets(BaseModel):
    latencyP95: str
    citationMismatchRate: str
    topKHitConfidence: str

class RetrievalCheck(BaseModel):
    queryFamily: str
    topK: int
    avgSimilarity: str
    latency: str
    citationValidity: str
    status: str

class AdminRetrievalMonitoringResponse(BaseModel):
    metrics: List[RetrievalMetric]
    trend_points: List[TrendPoint]
    health_targets: HealthTargets
    retrieval_checks: List[RetrievalCheck]

class PlatformShare(BaseModel):
    label: str
    value: int
    requests: str
    avgResponse: str
    tone: str

class PlatformModeSplit(BaseModel):
    platform: str
    messageUsage: str
    voiceUsage: str
    messageRequests: str
    voiceRequests: str
    avgResponseMessage: str
    avgResponseVoice: str

class VoiceHealthMetric(BaseModel):
    label: str
    value: str
    note: str
    tone: str

class LanguageDetectionRow(BaseModel):
    language: str
    confidence: str
    detectedRequests: str
    fallbackRate: str

class AdminPlatformAnalyticsResponse(BaseModel):
    platform_distribution: List[PlatformShare]
    platform_mode_split: List[PlatformModeSplit]
    voice_metrics: List[VoiceHealthMetric]
    language_detection: List[LanguageDetectionRow]

