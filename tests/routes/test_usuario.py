import uuid
import logging
from pydantic import ValidationError

from http import HTTPStatus
from sqlalchemy.exc import IntegrityError

from schemas.usuario import UsuarioViewSchema

##  python -m pytest -rA tests/routes/test_usuario.py
##  python -m pytest -rA

logger = logging.getLogger(__name__)

def test_create_valid_user_returns_201(mock_db_session, client):
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

    UsuarioViewSchema.model_validate(response_data)
 
  
def test_create_user_duplicate_email_returns_409(mock_db_session, client):
    mock_orig_exception = Exception("duplicate key value violates unique constraint")
    mock_db_session.commit.side_effect = IntegrityError(None, None, mock_orig_exception)
    
    payload = {
        "nome_usuario": "Maria",
        "email": "maria@exemplo.com",
        "senha": "123"
        }
    response = client.post("/usuarios/criar", json=payload)

    assert response.status_code == HTTPStatus.CONFLICT
    mock_db_session.rollback.assert_called_once()
    assert response.json["error_code"] == "EMAIL_ALREADY_EXISTS"

def test_create_user_returns_500(mock_db_session, client):
    mock_db_session.commit.side_effect = Exception("Database connection lost")
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

def test_create_user_invalid_data_returns_422(mock_db_session, client):
    payload = {
        "nome_usuario": "Maria"
    }
    response = client.post("/usuarios/criar", json=payload)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    mock_db_session.add.assert_not_called()
    mock_db_session.commit.assert_not_called()


### ---------------- get ---------------- ###
def test_list_users_no_records_returns_200(mock_db_session, client):
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


def test_list_users_returns_200(mock_db_session, client, mock_user_generator):
    usuarios_mock = mock_user_generator(amount=2)

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


def test_list_users_returns_500(mock_db_session, client):
    mock_db_session.query.side_effect = Exception("Query failure")
    response = client.get("/usuarios/listar")

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json["error_code"] == "INTERNAL_SERVER_ERROR"
    assert response.json["message"] == "Ocorreu um erro interno ao processar a requisição."

    mock_db_session.query.assert_called_once()
    mock_db_session.remove.assert_called_once()


def test_search_user_by_valid_uuid_returns_200(mock_db_session, client, mock_user_generator):
    fake_user = mock_user_generator(amount=1)[0]
    mock_db_session.query.return_value.filter.return_value.first.return_value = fake_user
    valid_uuid = fake_user.usuario_id

    response = client.get(f"/usuarios/{valid_uuid}")
    response_data = response.json

    assert response.status_code == HTTPStatus.OK
    mock_db_session.query.assert_called_once()
    mock_db_session.remove.assert_called_once()

    user_data = response_data["dados"]
    
    assert response_data["status"] == "success"    
    assert user_data["usuario_id"] == valid_uuid
    assert user_data["nome_usuario"] == fake_user.nome_usuario
    assert user_data["email"] == fake_user.email
    assert "data_criacao" in user_data


def test_search_user_not_found_returns_404(mock_db_session, client):
    mock_db_session.query.return_value.filter.return_value.first.return_value = None
    random_uuid = str(uuid.uuid4())

    response = client.get(f"/usuarios/{random_uuid}")
    
    assert response.status_code == HTTPStatus.NOT_FOUND
    mock_db_session.query.assert_called_once()
    mock_db_session.remove.assert_called_once()


def test_search_user_exception_returns_500(mock_db_session, client):
    error_message = "Database connection lost"
    mock_db_session.query.side_effect = Exception(error_message)
    valid_uuid = str(uuid.uuid4())

    response = client.get(f"/usuarios/{valid_uuid}")
    response_data = response.json

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    mock_db_session.query.assert_called_once()
    mock_db_session.remove.assert_called_once()

    assert response_data["status"] == "error"
    assert response_data["mensagem"] == error_message