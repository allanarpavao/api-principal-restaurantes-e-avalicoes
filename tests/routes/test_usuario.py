import pytest
from http import HTTPStatus
from unittest.mock import patch
from sqlalchemy.exc import IntegrityError

from app import app as flask_app

##  python -m pytest tests/routes/test_usuario.py -v

@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        yield client

@patch("routes.usuario.Session")
def test_criar_usuario_com_dados_validos_retorna_201(mock_session, client):
    def simular_banco_add(usuario_obj):
        usuario_obj.usuario_id = "123e4567-e89b-12d3-a456-426614174000"
        usuario_obj.data_criacao = "2026-04-14T00:00:00"
        
    mock_session.add.side_effect = simular_banco_add
    payload = {
        "nome_usuario": "João da Silva",
        "email": "joao@exemplo.com",
        "senha": "senhaSegura123"
    }

    response = client.post("/usuarios/criar", json=payload)

    assert response.status_code == HTTPStatus.CREATED
    assert mock_session.add.called
    assert mock_session.commit.called

@patch("routes.usuario.Session")
def test_criar_usuario_com_email_duplicado_retorna_409(mock_session, client):
    mock_session.commit.side_effect = IntegrityError("Erro", "Detalhe", "Origem")
    
    payload = {"nome_usuario": "Maria", "email": "maria@exemplo.com", "senha": "123"}
    response = client.post("/usuarios/criar", json=payload)

    assert response.status_code == HTTPStatus.CONFLICT
    assert mock_session.rollback.called
    assert response.json["error_code"] == "EMAIL_ALREADY_EXISTS"
