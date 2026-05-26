import pytest
import uuid
from unittest.mock import patch
from app import app as flask_app
from datetime import datetime
from types import SimpleNamespace



@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        yield client

@pytest.fixture
def mock_db_session():
    def fake_automatic_data_db(user):
        user.usuario_id = str(uuid.uuid4())
        user.data_criacao = datetime(2026, 4, 14, 0, 0, 0)

        return user
    
    with patch("routes.usuario.Session") as mock_session:
        mock_session.add.side_effect = fake_automatic_data_db
        yield mock_session


@pytest.fixture
def mock_user_generator():
    def _create_users(amount=1):
        users = []
        for i in range(amount):
            users.append(
                SimpleNamespace(
                    usuario_id=str(uuid.uuid4()),
                    nome_usuario=f"Test User {i}",
                    email=f"test{i}@example.com",
                    data_criacao=datetime(2026, 4, 14, 0, 0, 0)
                )
            )
        return users
    
    return _create_users
