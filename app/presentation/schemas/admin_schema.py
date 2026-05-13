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
    chunkCount: int
    embeddingModel: str
    status: str

class AdminKnowledgeResponse(BaseModel):
    records: List[AdminKnowledgeRecord]
