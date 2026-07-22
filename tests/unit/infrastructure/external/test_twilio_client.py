import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.infrastructure.external.twilio_client import TwilioWhatsAppClient

@pytest.fixture
def mock_sys_repo():
    repo = AsyncMock()
    mock_settings = MagicMock()
    mock_settings.twilio_account_sid = "test-db-sid"
    mock_settings.twilio_auth_token = "test-db-token"
    mock_settings.whatsapp_phone_number = "+19999999999"
    repo.get_settings.return_value = mock_settings
    return repo

@pytest.mark.asyncio
async def test_ensure_client_updates_credentials(mock_sys_repo):
    with patch("app.infrastructure.external.twilio_client.Client") as mock_client_cls:
        client = TwilioWhatsAppClient(system_settings_repository=mock_sys_repo)
        
        await client._ensure_client()
        
        assert client.current_sid == "test-db-sid"
        assert client.current_token == "test-db-token"
        assert client.from_number == "+19999999999"
        mock_client_cls.assert_called_with("test-db-sid", "test-db-token")

@pytest.mark.asyncio
async def test_send_message_text(mock_sys_repo):
    with patch("app.infrastructure.external.twilio_client.Client"):
        client = TwilioWhatsAppClient(system_settings_repository=mock_sys_repo)
        await client._ensure_client()
        
        # Mock the synchronous messages.create inside asyncio.to_thread
        mock_create = MagicMock()
        client.client.messages.create = mock_create
        
        await client.send_message(to="+12223334444", body="Hello")
        
        mock_create.assert_called_once_with(
            from_="whatsapp:+19999999999",
            to="whatsapp:+12223334444",
            body="Hello"
        )

@pytest.mark.asyncio
async def test_send_message_media(mock_sys_repo):
    with patch("app.infrastructure.external.twilio_client.Client"):
        client = TwilioWhatsAppClient(system_settings_repository=mock_sys_repo)
        await client._ensure_client()
        
        mock_create = MagicMock()
        client.client.messages.create = mock_create
        
        await client.send_message(to="+12223334444", media_url="http://audio.mp3")
        
        mock_create.assert_called_once_with(
            from_="whatsapp:+19999999999",
            to="whatsapp:+12223334444",
            media_url=["http://audio.mp3"]
        )

@pytest.mark.asyncio
async def test_send_message_no_client():
    client = TwilioWhatsAppClient()
    client.client = None
    
    # Should just return without exception
    await client.send_message(to="+12223334444", body="Hello")

@pytest.mark.asyncio
async def test_send_message_error(mock_sys_repo):
    with patch("app.infrastructure.external.twilio_client.Client"):
        client = TwilioWhatsAppClient(system_settings_repository=mock_sys_repo)
        await client._ensure_client()
        
        mock_create = MagicMock(side_effect=Exception("API Error"))
        client.client.messages.create = mock_create
        
        with pytest.raises(Exception):
            await client.send_message(to="+12223334444", body="Hello")
