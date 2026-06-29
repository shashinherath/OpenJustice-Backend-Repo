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
    userEmail: Optional[str] = None

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



class AdminUserCreateRequest(BaseModel):
    first_name: str
    last_name: str
    phone_number: str
    email: str
    password: str

class AdminUserItem(BaseModel):
    id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: str
    phone_number: Optional[str] = None
    role: str
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
    collectionId: Optional[str] = None
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

class UsageDailyStat(BaseModel):
    day: str
    count: int

class AdminUsageAnalyticsResponse(BaseModel):
    total_queries_this_week: int
    active_users: int
    peak_hour: str
    queries_per_day: List[UsageDailyStat]

class CostDriver(BaseModel):
    key: str
    title: str
    model: str
    unit: str
    usage: int
    estimatedCost: float
    trend: str
    detail: str
    colorClass: str

class TwilioItem(BaseModel):
    label: str
    value: int
    cost: float
    note: str

class DailyCostPoint(BaseModel):
    day: str
    openAi: float
    twilio: float

class AdminCostAnalyticsResponse(BaseModel):
    cost_drivers: List[CostDriver]
    twilio_items: List[TwilioItem]
    daily_costs: List[DailyCostPoint]

class LanguageStat(BaseModel):
    code: str
    label: str
    count: int

class AdminMultilingualAnalyticsResponse(BaseModel):
    total_queries: int
    total_languages: int
    translation_requests: int
    languages: List[LanguageStat]

class SecuritySignal(BaseModel):
    label: str
    value: str
    note: str
    tone: str

class MonitoringArea(BaseModel):
    key: str
    title: str
    icon: str
    status: str
    summary: str
    metricLabel: str
    metricValue: str

class PriorityAlert(BaseModel):
    title: str
    detail: str
    severity: str

class SecurityEventRecord(BaseModel):
    area: str
class QuickActionItem(BaseModel):
    icon: str
    label: str
    highlight: Optional[bool] = False
    action_id: str

class AdminOverviewResponse(BaseModel):
    stats: List[StatItem]
    activities: List[ActivityItem]
    core_services: List[ServiceStatusItem]
    data_sources: List[DataSourceItem]
    queries_per_day: List[DailyQueryStat]
    quick_actions: List[QuickActionItem]

class AdminKnowledgeRecord(BaseModel):
    documentId: str
    documentTitle: str
    collectionId: Optional[str] = None
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

class UsageDailyStat(BaseModel):
    day: str
    count: int

class AdminUsageAnalyticsResponse(BaseModel):
    total_queries_this_week: int
    active_users: int
    peak_hour: str
    queries_per_day: List[UsageDailyStat]

class CostDriver(BaseModel):
    key: str
    title: str
    model: str
    unit: str
    usage: int
    estimatedCost: float
    trend: str
    detail: str
    colorClass: str

class TwilioItem(BaseModel):
    label: str
    value: int
    cost: float
    note: str

class DailyCostPoint(BaseModel):
    day: str
    openAi: float
    twilio: float

class AdminCostAnalyticsResponse(BaseModel):
    cost_drivers: List[CostDriver]
    twilio_items: List[TwilioItem]
    daily_costs: List[DailyCostPoint]

class LanguageStat(BaseModel):
    code: str
    label: str
    count: int

class AdminMultilingualAnalyticsResponse(BaseModel):
    total_queries: int
    total_languages: int
    translation_requests: int
    languages: List[LanguageStat]

class SecuritySignal(BaseModel):
    label: str
    value: str
    note: str
    tone: str

class MonitoringArea(BaseModel):
    key: str
    title: str
    icon: str
    status: str
    summary: str
    metricLabel: str
    metricValue: str

class PriorityAlert(BaseModel):
    title: str
    detail: str
    severity: str

class SecurityEventRecord(BaseModel):
    area: str
    source: str
    detail: str
    severity: str
    timestamp: str

class AdminSecurityMonitoringResponse(BaseModel):
    signals: List[SecuritySignal]
    monitoring_areas: List[MonitoringArea]
    priority_alerts: List[PriorityAlert]
    recent_events: List[SecurityEventRecord]

class RetrievalDistributionBin(BaseModel):
    bin_label: str
    count: int

class AdminRetrievalEvaluationResponse(BaseModel):
    recall_at_5: float
    precision_at_5: float
    similarity_distribution: List[RetrievalDistributionBin]

class ModelRun(BaseModel):
    model: str
    accuracy: float
    tokens: int

class AdminAIEvaluationResponse(BaseModel):
    accuracy: float
    hallucination_rate: float
    avg_tokens: int
    recent_model_runs: List[ModelRun]

class ResearchMetricItem(BaseModel):
    label: str
    value: str
    note: str
    trend: str

class EvaluationDatasetItem(BaseModel):
    name: str
    version: str
    samples: int
    split: str
    lastRun: str
    status: str

class ExperimentNoteItem(BaseModel):
    title: str
    description: str

class AdminResearchMetricsResponse(BaseModel):
    metrics: List[ResearchMetricItem]
    datasets: List[EvaluationDatasetItem]
    experiment_notes: List[ExperimentNoteItem]

class LanguageSettingsResponse(BaseModel):
    enabled_languages: List[str]
    default_language: str
    translation_pipeline_enabled: bool

class LanguageSettingsUpdate(BaseModel):
    enabled_languages: List[str]
    default_language: str
    translation_pipeline_enabled: bool

class AISettingsResponse(BaseModel):
    ai_model_name: str
    ai_temperature: float
    ai_max_tokens: int
    ai_top_p: float
    ai_frequency_penalty: float

class AISettingsUpdate(BaseModel):
    ai_model_name: str
    ai_temperature: float
    ai_max_tokens: int
    ai_top_p: float
    ai_frequency_penalty: float

class RetrievalSettingsResponse(BaseModel):
    retrieval_top_k: int
    retrieval_similarity_threshold: float
    retrieval_embedding_model: str
    retrieval_chunk_size: int
    retrieval_chunk_overlap: int

class RetrievalSettingsUpdate(BaseModel):
    retrieval_top_k: int
    retrieval_similarity_threshold: float
    retrieval_embedding_model: str
    retrieval_chunk_size: int
    retrieval_chunk_overlap: int

class IntegrationSettingsResponse(BaseModel):
    openai_api_key: Optional[str]
    twilio_account_sid: Optional[str]
    twilio_auth_token: Optional[str]
    whatsapp_phone_number: Optional[str]
    web_socket_url: Optional[str]

class IntegrationSettingsUpdate(BaseModel):
    openai_api_key: Optional[str]
    twilio_account_sid: Optional[str]
    twilio_auth_token: Optional[str]
    whatsapp_phone_number: Optional[str]
    web_socket_url: Optional[str]
