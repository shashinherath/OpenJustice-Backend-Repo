import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.infrastructure.db.base import get_db
from app.presentation.controllers.admin_controller import (
    get_admin_overview_service, get_admin_users_service, get_admin_knowledge_service,
    get_admin_logs_service, get_admin_retrieval_service, get_admin_platform_analytics_service,
    get_admin_usage_analytics_service, get_admin_cost_analytics_service,
    get_admin_multilingual_analytics_service, get_admin_security_monitoring_service,
    get_admin_error_monitoring_service, get_admin_retrieval_evaluation_service,
    get_admin_ai_evaluation_service, get_admin_system_settings_service
)

mock_db = AsyncMock()
mock_overview = AsyncMock()
mock_users = AsyncMock()
mock_knowledge = AsyncMock()
mock_logs = AsyncMock()
mock_retrieval = AsyncMock()
mock_platform = AsyncMock()
mock_usage = AsyncMock()
mock_cost = AsyncMock()
mock_multilingual = AsyncMock()
mock_security = AsyncMock()
mock_error = AsyncMock()
mock_retrieval_eval = AsyncMock()
mock_ai_eval = AsyncMock()
mock_settings = AsyncMock()

@pytest.fixture(autouse=True)
def override_dependencies():
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_admin_overview_service] = lambda: mock_overview
    app.dependency_overrides[get_admin_users_service] = lambda: mock_users
    app.dependency_overrides[get_admin_knowledge_service] = lambda: mock_knowledge
    app.dependency_overrides[get_admin_logs_service] = lambda: mock_logs
    app.dependency_overrides[get_admin_retrieval_service] = lambda: mock_retrieval
    app.dependency_overrides[get_admin_platform_analytics_service] = lambda: mock_platform
    app.dependency_overrides[get_admin_usage_analytics_service] = lambda: mock_usage
    app.dependency_overrides[get_admin_cost_analytics_service] = lambda: mock_cost
    app.dependency_overrides[get_admin_multilingual_analytics_service] = lambda: mock_multilingual
    app.dependency_overrides[get_admin_security_monitoring_service] = lambda: mock_security
    app.dependency_overrides[get_admin_error_monitoring_service] = lambda: mock_error
    app.dependency_overrides[get_admin_retrieval_evaluation_service] = lambda: mock_retrieval_eval
    app.dependency_overrides[get_admin_ai_evaluation_service] = lambda: mock_ai_eval
    app.dependency_overrides[get_admin_system_settings_service] = lambda: mock_settings
    yield
    app.dependency_overrides.clear()

client = TestClient(app)
test_user_id = uuid4()
headers = {"Authorization": "Bearer fake_token"}

@pytest.fixture(autouse=True)
def auth_mock():
    with patch("app.presentation.middleware.auth_middleware.jwt_handler.verify_token") as mock_verify:
        mock_verify.return_value = {"sub": str(test_user_id)}
        yield mock_verify

def test_get_overview():
    mock_overview.get_overview_stats.return_value = {
        "stats": [{"id": 1, "title": "t", "value": "v", "change": "c", "statusType": "s"}],
        "activities": [],
        "core_services": [],
        "data_sources": [],
        "queries_per_day": [],
        "quick_actions": []
    }
    response = client.get("/api/admin/overview", headers=headers)
    assert response.status_code == 200

def test_clear_semantic_cache():
    response = client.post("/api/admin/clear-semantic-cache", headers=headers)
    assert response.status_code == 200

def test_list_users():
    mock_users.get_users.return_value = {
        "users": [],
        "total_active": 0,
        "total_blocked": 0
    }
    response = client.get("/api/admin/users", headers=headers)
    assert response.status_code == 200

def test_create_admin_user():
    mock_users.create_admin_user.return_value = {
        "id": str(uuid4()),
        "first_name": "Admin",
        "last_name": "Test",
        "email": "admin@test.com",
        "phone_number": "1234567890",
        "role": "admin",
        "status": "active",
        "createdDate": "2023-01-01T00:00:00Z",
        "avatar_url": None
    }
    response = client.post("/api/admin/users", json={
        "first_name": "Admin",
        "last_name": "Test",
        "email": "admin@test.com",
        "phone_number": "1234567890",
        "password": "Password123!"
    }, headers=headers)
    assert response.status_code == 200

def test_update_user_status():
    uid = str(uuid4())
    mock_users.update_user_status.return_value = {
        "id": uid,
        "first_name": "Admin",
        "last_name": "Test",
        "email": "admin@test.com",
        "phone_number": "1234567890",
        "role": "admin",
        "status": "inactive",
        "createdDate": "2023-01-01T00:00:00Z",
        "avatar_url": None
    }
    response = client.patch(f"/api/admin/users/{uid}/status", json={"is_active": False}, headers=headers)
    assert response.status_code == 200

def test_get_retrieval_monitoring():
    mock_retrieval.get_retrieval_monitoring.return_value = {
        "metrics": [],
        "trend_points": [],
        "health_targets": {"latencyP95": "a", "citationMismatchRate": "b", "topKHitConfidence": "c"},
        "retrieval_checks": []
    }
    response = client.get("/api/admin/retrieval-monitoring", headers=headers)
    assert response.status_code == 200

def test_get_knowledge():
    mock_knowledge.get_knowledge_metrics.return_value = {
        "records": []
    }
    response = client.get("/api/admin/knowledge", headers=headers)
    assert response.status_code == 200

def test_get_logs():
    mock_logs.get_logs.return_value = {
        "logs": [],
        "total": 0,
        "total_completed": 0,
        "total_reviewed": 0,
        "total_pending": 0,
        "total_failed": 0,
        "total_tokens": 0,
        "avg_latency": 0
    }
    response = client.get("/api/admin/logs", headers=headers)
    assert response.status_code == 200

def test_get_platform_analytics():
    mock_platform.get_platform_analytics.return_value = {
        "platform_distribution": [],
        "platform_mode_split": [],
        "voice_metrics": [],
        "language_detection": []
    }
    response = client.get("/api/admin/platform-analytics", headers=headers)
    assert response.status_code == 200

def test_get_usage_analytics():
    mock_usage.get_usage_analytics.return_value = {
        "total_queries_this_week": 100,
        "active_users": 50,
        "peak_hour": "14:00",
        "queries_per_day": []
    }
    response = client.get("/api/admin/usage-analytics", headers=headers)
    assert response.status_code == 200

def test_get_cost_analytics():
    mock_cost.get_cost_analytics.return_value = {
        "cost_drivers": [],
        "twilio_items": [],
        "daily_costs": [],
        "daily_model_costs": []
    }
    response = client.get("/api/admin/cost-analytics", headers=headers)
    assert response.status_code == 200

def test_get_multilingual_analytics():
    mock_multilingual.get_multilingual_analytics.return_value = {
        "total_queries": 100,
        "total_languages": 5,
        "translation_requests": 10,
        "languages": []
    }
    response = client.get("/api/admin/multilingual-analytics", headers=headers)
    assert response.status_code == 200

def test_get_security_monitoring():
    mock_security.get_security_monitoring.return_value = {
        "signals": [],
        "monitoring_areas": [],
        "priority_alerts": [],
        "recent_events": [],
        "activity_logs": []
    }
    response = client.get("/api/admin/security-monitoring", headers=headers)
    assert response.status_code == 200

def test_get_error_monitoring():
    mock_error.get_errors.return_value = {
        "errors": [],
        "total_errors": 0,
        "total_llm": 0,
        "total_db": 0,
        "total_api": 0,
        "total_auth": 0,
        "total_system": 0
    }
    response = client.get("/api/admin/error-monitoring", headers=headers)
    assert response.status_code == 200

def test_get_retrieval_evaluation():
    mock_retrieval_eval.get_retrieval_evaluation.return_value = {
        "recall_at_5": 0.8,
        "precision_at_5": 0.7,
        "similarity_distribution": []
    }
    response = client.get("/api/admin/analytics/retrieval-evaluation", headers=headers)
    assert response.status_code == 200

def test_get_ai_evaluation():
    mock_ai_eval.get_ai_evaluation_metrics.return_value = {
        "accuracy": 0.9,
        "hallucination_rate": 0.1,
        "avg_tokens": 100,
        "recent_model_runs": []
    }
    response = client.get("/api/admin/analytics/ai-evaluation", headers=headers)
    assert response.status_code == 200

@patch("app.presentation.controllers.admin_controller.AdminResearchService")
def test_research_endpoints(mock_research_cls):
    mock_research = AsyncMock()
    mock_research_cls.return_value = mock_research
    
    mock_research.get_research_metrics.return_value = {
        "metrics": [],
        "datasets": [],
        "experiment_notes": []
    }
    response = client.get("/api/admin/analytics/research-metrics", headers=headers)
    assert response.status_code == 200
    
def test_get_language_settings():
    mock_settings.get_language_settings.return_value = {
        "enabled_languages": ["en", "es"],
        "default_language": "en",
        "translation_pipeline_enabled": True
    }
    response = client.get("/api/admin/settings/language", headers=headers)
    assert response.status_code == 200

def test_get_ai_settings():
    mock_settings.get_ai_settings.return_value = {
        "ai_model_name": "gpt-4",
        "ai_temperature": 0.7,
        "ai_max_tokens": 1000,
        "ai_top_p": 1.0,
        "ai_frequency_penalty": 0.0
    }
    response = client.get("/api/admin/settings/ai", headers=headers)
    assert response.status_code == 200

def test_get_retrieval_settings():
    mock_settings.get_retrieval_settings.return_value = {
        "retrieval_top_k": 5,
        "retrieval_similarity_threshold": 0.7,
        "retrieval_embedding_model": "text-embedding-ada-002",
        "retrieval_chunk_size": 1000,
        "retrieval_chunk_overlap": 200
    }
    response = client.get("/api/admin/settings/retrieval", headers=headers)
    assert response.status_code == 200

def test_get_integration_settings():
    mock_settings.get_integration_settings.return_value = {
        "openai_api_key": "sk-test",
        "twilio_account_sid": "ACtest",
        "twilio_auth_token": "token",
        "whatsapp_phone_number": "+1234567890",
        "web_socket_url": "ws://localhost:8000"
    }
    response = client.get("/api/admin/settings/integration", headers=headers)
    assert response.status_code == 200

def test_get_security_settings():
    mock_settings.get_security_settings.return_value = {
        "jwt_expiry_minutes": 60,
        "rate_limit_per_minute": 100,
        "prompt_validation_enabled": True,
        "account_lockout_threshold": 5
    }
    response = client.get("/api/admin/settings/security", headers=headers)
    assert response.status_code == 200
