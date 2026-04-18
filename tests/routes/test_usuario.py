import pytest
from pydantic import ValidationError
from datetime import datetime
from types import SimpleNamespace
from http import HTTPStatus
from unittest.mock import patch
from sqlalchemy.exc import IntegrityError

from app import app as flask_app
from schemas.usuario import UsuarioViewSchema


##  python -m pytest tests/routes/test_usuario.py -v

@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        yield client

@pytest.fixture
def mock_db_session():
    def simular_dados_automaticos_db(usuario_obj):
        usuario_obj.usuario_id = "123e4567-e89b-12d3-a456-426614174000"
        usuario_obj.data_criacao = datetime(2026, 4, 14, 0, 0, 0)

        return usuario_obj
    
    with patch("routes.usuario.Session") as mock_session:
        mock_session.add.side_effect = simular_dados_automaticos_db
        yield mock_session


@pytest.fixture
def gerar_usuarios_mock():
    def _criar_usuarios(quantidade=1):
        usuarios = []
        for i in range(quantidade):
            usuarios.append(
                SimpleNamespace(
                    nome_usuario=f"Usuario Teste {i}",
                    email=f"teste{i}@exemplo.com",
                    data_criacao=datetime(2026, 4, 14, 0, 0, 0)
                )
            )
        return usuarios
    
    return _criar_usuarios


def test_criar_usuario_valido_retorna_201(mock_db_session, client):
    payload = {
        "nome_usuario": "João da Silva",
        "email": "joao@exemplo.com",
        "senha": "senhaSegura123"
    }

    response = client.post("/usuarios/criar", json=payload)
    response_data = response.json
    
    assert response.status_code == HTTPStatus.CREATED
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()

    assert response_data["nome_usuario"] == payload["nome_usuario"]
    assert response_data["email"] == payload["email"]
    assert "senha" not in response_data

    try:
        UsuarioViewSchema.model_validate(response_data)
    except ValidationError as e:
        print(e.json(indent=2))
        pytest.fail(f"O payload de resposta não respeita o UsuarioViewSchema: {e}")

  
def test_criar_usuario_com_email_duplicado_retorna_409(mock_db_session, client):
    mock_db_session.commit.side_effect = IntegrityError("Erro", "Detalhe", "Origem")
    
    payload = {"nome_usuario": "Maria", "email": "maria@exemplo.com", "senha": "123"}
    response = client.post("/usuarios/criar", json=payload)

    assert response.status_code == HTTPStatus.CONFLICT
    mock_db_session.rollback.assert_called_once()
    assert response.json["error_code"] == "EMAIL_ALREADY_EXISTS"

def test_criar_usuario_retorna_500(mock_db_session, client):
    mock_db_session.commit.side_effect = Exception("Conexão com o banco perdida")
    payload = {
        "nome_usuario": "Carlos", 
        "email": "carlos@exemplo.com", 
        "senha": "123"
    }
    response = client.post("/usuarios/criar", json=payload)

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json["error_code"] == "INTERNAL_SERVER_ERROR"
    mock_db_session.rollback.assert_called_once()
    mock_db_session.remove.assert_called_once()

def test_criar_usuario_dados_invalidos_retorna_422(mock_db_session, client):

    payload = {
        "nome_usuario": "Maria"
    }
    response = client.post("/usuarios/criar", json=payload)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    mock_db_session.add.assert_not_called()
    mock_db_session.commit.assert_not_called()


def test_listar_usuarios_sem_registros_retorna_200(mock_db_session, client):
    mock_db_session.query.return_value.all.return_value = []

    response = client.get("/usuarios/listar")
    response_data = response.json

    assert response.status_code == HTTPStatus.OK
    assert response_data["status"] == "success"
    assert response_data["mensagem"] == "Nenhum usuário encontrado."
    assert response_data["usuarios"] == []
    assert response_data["quantidade"] == 0

    mock_db_session.query.assert_called_once()
    mock_db_session.remove.assert_called_once()


def test_listar_usuarios_com_registros_retorna_200(mock_db_session, client, gerar_usuarios_mock):
    usuarios_mock = gerar_usuarios_mock(quantidade=2)

    mock_db_session.query.return_value.all.return_value = usuarios_mock

    response = client.get("/usuarios/listar")
    response_data = response.json

    assert response.status_code == HTTPStatus.OK
    assert response_data["status"] == "success"
    assert response_data["quantidade"] == 2
    assert response_data["mensagem"] == "2 usuário(s) encontrado(s)."

    assert len(response_data["usuarios"]) == 2
    assert "senha" not in response_data["usuarios"][0]

    mock_db_session.query.assert_called_once()
    mock_db_session.remove.assert_called_once()


def test_listar_usuarios_retorna_500(mock_db_session, client):
    mock_db_session.query.side_effect = Exception("Falha na consulta")
    response = client.get("/usuarios/listar")

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json["error_code"] == "INTERNAL_SERVER_ERROR"
    assert response.json["message"] == "Ocorreu um erro interno ao processar a requisição."

    mock_db_session.query.assert_called_once()
    mock_db_session.remove.assert_called_once()