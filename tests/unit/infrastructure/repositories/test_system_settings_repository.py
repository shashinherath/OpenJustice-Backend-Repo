import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.system_settings_repository import SystemSettingsRepository
from app.infrastructure.models.system_settings import SystemSettings

@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)

@pytest.fixture
def repository(mock_db):
    return SystemSettingsRepository(mock_db)

@pytest.mark.asyncio
async def test_get_settings_existing(repository, mock_db):
    mock_settings = SystemSettings(id=str(uuid4()), default_language="en")
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_settings
    mock_db.execute.return_value = mock_result
    
    settings = await repository.get_settings()
    
    assert settings == mock_settings
    mock_db.execute.assert_called_once()
    mock_db.add.assert_not_called()

@pytest.mark.asyncio
async def test_get_settings_not_found_creates_new(repository, mock_db):
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_result
    
    settings = await repository.get_settings()
    
    assert settings is not None
    assert settings.default_language == "en"
    mock_db.add.assert_called_once_with(settings)
    mock_db.flush.assert_called_once()
    mock_db.refresh.assert_called_once_with(settings)

@pytest.mark.asyncio
async def test_update_settings(repository, mock_db):
    mock_settings = SystemSettings(id=str(uuid4()))
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_settings
    mock_db.execute.return_value = mock_result
    
    updated = await repository.update_settings(["en", "es"], "es", False)
    
    assert updated.enabled_languages == ["en", "es"]
    assert updated.default_language == "es"
    assert updated.translation_pipeline_enabled is False
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_with(updated)

@pytest.mark.asyncio
async def test_update_ai_settings(repository, mock_db):
    mock_settings = SystemSettings(id=str(uuid4()))
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_settings
    mock_db.execute.return_value = mock_result
    
    updated = await repository.update_ai_settings("gpt-4", 0.8, 1000, 0.9, 0.1)
    
    assert updated.ai_model_name == "gpt-4"
    assert updated.ai_temperature == 0.8
    assert updated.ai_max_tokens == 1000
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_with(updated)

@pytest.mark.asyncio
async def test_update_retrieval_settings(repository, mock_db):
    mock_settings = SystemSettings(id=str(uuid4()))
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_settings
    mock_db.execute.return_value = mock_result
    
    updated = await repository.update_retrieval_settings(10, 0.75, "text-embedding-3-small", 500, 50)
    
    assert updated.retrieval_top_k == 10
    assert updated.retrieval_similarity_threshold == 0.75
    assert updated.retrieval_embedding_model == "text-embedding-3-small"
    assert updated.retrieval_chunk_size == 500
    assert updated.retrieval_chunk_overlap == 50
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_with(updated)

@pytest.mark.asyncio
async def test_update_integration_settings(repository, mock_db):
    mock_settings = SystemSettings(id=str(uuid4()))
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_settings
    mock_db.execute.return_value = mock_result
    
    updated = await repository.update_integration_settings(
        "sk-test", "sid-test", "token-test", "+12345", "ws://test"
    )
    
    assert updated.openai_api_key == "sk-test"
    assert updated.twilio_account_sid == "sid-test"
    assert updated.twilio_auth_token == "token-test"
    assert updated.whatsapp_phone_number == "+12345"
    assert updated.web_socket_url == "ws://test"
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_with(updated)

@pytest.mark.asyncio
async def test_update_security_settings(repository, mock_db):
    mock_settings = SystemSettings(id=str(uuid4()))
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_settings
    mock_db.execute.return_value = mock_result
    
    updated = await repository.update_security_settings(60, 100, True, 5)
    
    assert updated.jwt_expiry_minutes == 60
    assert updated.rate_limit_per_minute == 100
    assert updated.prompt_validation_enabled is True
    assert updated.account_lockout_threshold == 5
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_with(updated)
