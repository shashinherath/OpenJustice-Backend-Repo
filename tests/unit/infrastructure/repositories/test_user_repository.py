import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func

from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.models.user import User

@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)

@pytest.fixture
def repository(mock_db):
    return UserRepository(mock_db)

@pytest.mark.asyncio
async def test_get_by_email(repository, mock_db):
    email = "test@example.com"
    mock_user = User(id=uuid4(), email=email)
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_user
    mock_db.execute.return_value = mock_result
    
    user = await repository.get_by_email(email)
    
    assert user is not None
    assert user.email == email
    mock_db.execute.assert_called_once()

@pytest.mark.asyncio
async def test_get_by_phone(repository, mock_db):
    phone = "+1234567890"
    mock_user = User(id=uuid4(), phone_number=phone)
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_user
    mock_db.execute.return_value = mock_result
    
    user = await repository.get_by_phone(phone)
    
    assert user is not None
    assert user.phone_number == phone
    mock_db.execute.assert_called_once()

@pytest.mark.asyncio
async def test_get_by_uuid(repository, mock_db):
    user_id = uuid4()
    mock_user = User(id=user_id)
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_user
    mock_db.execute.return_value = mock_result
    
    user = await repository.get_by_uuid(user_id)
    
    assert user is not None
    assert user.id == user_id
    mock_db.execute.assert_called_once()

@pytest.mark.asyncio
async def test_get_by_verification_token(repository, mock_db):
    token = "sometoken"
    mock_user = User(id=uuid4(), email_verification_token=token)
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_user
    mock_db.execute.return_value = mock_result
    
    user = await repository.get_by_verification_token(token)
    
    assert user is not None
    assert user.email_verification_token == token
    mock_db.execute.assert_called_once()

@pytest.mark.asyncio
async def test_create(repository, mock_db):
    user = User(id=uuid4(), email="test@test.com")
    
    created_user = await repository.create(user)
    
    assert created_user == user
    mock_db.add.assert_called_once_with(user)
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(user)

@pytest.mark.asyncio
async def test_get_total_count(repository, mock_db):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = 100
    mock_db.execute.return_value = mock_result
    
    count = await repository.get_total_count()
    
    assert count == 100
    mock_db.execute.assert_called_once()

@pytest.mark.asyncio
async def test_list_users(repository, mock_db):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [User(id=uuid4()), User(id=uuid4())]
    mock_db.execute.return_value = mock_result
    
    users = await repository.list_users(
        skip=0,
        limit=10,
        search_query="john",
        role="admin",
        status="active"
    )
    
    assert len(users) == 2
    mock_db.execute.assert_called_once()

@pytest.mark.asyncio
async def test_update_status(repository, mock_db):
    user_id = uuid4()
    mock_user = User(id=user_id, is_active=True)
    
    # We patch get_by_uuid internally or just rely on execute returning it
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_user
    mock_db.execute.return_value = mock_result
    
    updated = await repository.update_status(user_id, False)
    
    assert updated is not None
    assert updated.is_active is False
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(mock_user)

@pytest.mark.asyncio
async def test_update_status_not_found(repository, mock_db):
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_result
    
    updated = await repository.update_status(uuid4(), False)
    
    assert updated is None

@pytest.mark.asyncio
async def test_update_profile(repository, mock_db):
    user_id = uuid4()
    mock_user = User(
        id=user_id,
        first_name="Old",
        last_name="Name",
        email="old@test.com",
        preferred_language="en",
        avatar_url="old.jpg"
    )
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_user
    mock_db.execute.return_value = mock_result
    
    updated = await repository.update_profile(
        user_id,
        first_name="New",
        last_name="Last",
        email="new@test.com",
        preferred_language="es",
        avatar_url="new.jpg"
    )
    
    assert updated is not None
    assert updated.first_name == "New"
    assert updated.last_name == "Last"
    assert updated.email == "new@test.com"
    assert updated.preferred_language == "es"
    assert updated.avatar_url == "new.jpg"
    
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(mock_user)

@pytest.mark.asyncio
async def test_update_profile_not_found(repository, mock_db):
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_result
    
    updated = await repository.update_profile(uuid4(), first_name="New")
    
    assert updated is None

@pytest.mark.asyncio
async def test_set_password(repository, mock_db):
    user_id = uuid4()
    mock_user = User(id=user_id, hashed_password="old")
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_user
    mock_db.execute.return_value = mock_result
    
    updated = await repository.set_password(user_id, "new_hashed")
    
    assert updated is not None
    assert updated.hashed_password == "new_hashed"
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(mock_user)

@pytest.mark.asyncio
async def test_set_password_not_found(repository, mock_db):
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_result
    
    updated = await repository.set_password(uuid4(), "new_hashed")
    
    assert updated is None

@pytest.mark.asyncio
async def test_get_active_sessions_count(repository, mock_db):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = 50
    mock_db.execute.return_value = mock_result
    
    count = await repository.get_active_sessions_count()
    
    assert count == 50
    mock_db.execute.assert_called_once()
