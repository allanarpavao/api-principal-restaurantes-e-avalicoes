from urllib.parse import unquote
import uuid
from flask_openapi3 import APIBlueprint, Tag
from http import HTTPStatus
from sqlalchemy.exc import IntegrityError

from models import Session
from models.usuario import Usuario
from schemas.error import ErrorSchema
from schemas.usuario import ListagemUsuariosSchema, UsuarioBuscaSchema, UsuarioSchema, UsuarioViewSchema, apresenta_usuario, apresenta_usuarios

usuarios_bp = APIBlueprint(
    'usuarios',
    __name__,
    url_prefix='/usuarios',
    abp_tags=[Tag(name='Usuários', description='Operações de usuário')]
)

@usuarios_bp.post('/criar', responses={"201": UsuarioViewSchema, "409": ErrorSchema, "400": ErrorSchema})
def criar_usuario(form: UsuarioSchema):
    """Adiciona um novo usuário à base de dados

    Retorna uma representação dos usuários.
    """

    #TODO: trocar por form.model_dump()
    try:
        usuario = Usuario(
            nome_usuario = form.nome_usuario,
            email = form.email,
            senha = form.senha
        )

        Session.add(usuario)
        Session.commit()
        # TODO: trocar por UsuarioViewSchema...model_dump
        return apresenta_usuario(usuario), HTTPStatus.CREATED
    
    except IntegrityError:
        Session.rollback()

        return {"erro": "Email já existe"}, HTTPStatus.CONFLICT
    
    except Exception as e:
        Session.rollback()
        return {"erro": str(e)}, HTTPStatus.BAD_REQUEST

    finally:
        Session.remove()

@usuarios_bp.get('/listar', responses={"200": ListagemUsuariosSchema})
def listar_usuarios():
    """ Retorna uma lista de todos os usuários cadastrados
    """
    try:
        # session = Session()
        usuarios = Session.query(Usuario).all()

        if not usuarios:
            return {
                "status": "success",
                "mensagem": "Nenhum usuário encontrado.",
                "usuarios": [],
                "quantidade": 0
            }, HTTPStatus.OK

        return {
            "status": "success",
            "mensagem": f"{len(usuarios)} usuário(s) encontrado(s).",
            "usuarios": apresenta_usuarios(usuarios)["usuarios"],
            "quantidade": len(usuarios)
        }, HTTPStatus.OK
    
    except Exception as e:
        return {"status": "error", "mensagem": str(e)}, HTTPStatus.INTERNAL_SERVER_ERROR
    
    finally:
        Session.remove()

@usuarios_bp.get('/', responses={"200": ListagemUsuariosSchema, "404": ErrorSchema})
def buscar_usuario(query:UsuarioBuscaSchema):
    """Busca e retorna os dados detalhados de um usuário a partir do uuid do usuário
    """
    try:
        uuid_usuario = unquote(query.id_usuario)
        uuid.UUID(uuid_usuario)
    
    except ValueError:
        return {"status": "error", "mensagem": "UUID inválido"}, HTTPStatus.BAD_REQUEST

    try:
        usuario = Session.query(Usuario).filter(Usuario.usuario_id == uuid_usuario).first()

        if not usuario:
            return {
                "status": "error",
                "mensagem": f"Usuário '{uuid_usuario}' não foi localizado no sistema."
            }, HTTPStatus.NOT_FOUND
        else:
            return {
                "status": "success",
                "dados": {
                "nome_usuario": usuario.nome_usuario,
                "email": usuario.email,
                "data_criacao": usuario.data_criacao,
                "usuario_id": usuario.usuario_id
            }
        }, HTTPStatus.OK
    
    except Exception as e:
        return {"status": "error", "mensagem": str(e)}, HTTPStatus.INTERNAL_SERVER_ERROR
    
    finally:
        Session.remove()

@usuarios_bp.delete('/',
            responses={"200": ListagemUsuariosSchema, "404": ErrorSchema})
def deletar_usuario(query:UsuarioBuscaSchema):
    """Remove um usuário do sistema com base no uuid fornecido.
    Retorna uma resposta indicando o sucesso ou a falha da operação.
    """
    try:
        uuid_usuario = unquote(query.id_usuario)
        uuid.UUID(uuid_usuario)
    
    except ValueError:
        return {"status": "error", "mensagem": "UUID inválido"}, HTTPStatus.BAD_REQUEST


    try:
        usuario = Session.query(Usuario).filter(Usuario.usuario_id == uuid_usuario).first()
        
        if usuario:
            Session.query(Usuario).filter(Usuario.usuario_id == uuid_usuario).delete()
            Session.commit()
            return {
                "status": "success",
                "mensagem": f"Usuário '{uuid_usuario}' removido com sucesso."
            }, HTTPStatus.OK
        else:
            return {
                "status": "error",
                "mensagem": f"Usuário '{uuid_usuario}' não encontrado na base."
            }, HTTPStatus.NOT_FOUND
    
    except IntegrityError:
        Session.rollback()
    
        return {"status": "error", "mensagem": "Não é possível deletar"}, HTTPStatus.CONFLICT
    
    except Exception as e:
        Session.rollback()
        
        return {"status": "error", "mensagem": str(e)}, HTTPStatus.INTERNAL_SERVER_ERROR

    finally:
        Session.remove()