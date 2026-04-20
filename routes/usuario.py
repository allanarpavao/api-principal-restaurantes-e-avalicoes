from urllib.parse import unquote
import uuid
import logging
from flask_openapi3 import APIBlueprint, Tag
from http import HTTPStatus
from sqlalchemy.exc import IntegrityError

from models import Session
from models.usuario import Usuario
from schemas.error import ErrorSchema
from schemas.usuario import UsuarioBuscaSchema, UsuarioResponseSchema, UsuarioSchema, UsuarioViewSchema

logger = logging.getLogger(__name__)

usuarios_bp = APIBlueprint(
    'usuarios',
    __name__,
    url_prefix='/usuarios',
    abp_tags=[Tag(name='Usuários', description='Operações de usuário')]
)

@usuarios_bp.post('/criar', responses={"201": UsuarioViewSchema, "409": ErrorSchema, "400": ErrorSchema,
                                        "422": ErrorSchema, "500": ErrorSchema})
def criar_usuario(body: UsuarioSchema):
    """Adiciona um novo usuário à base de dados

    Retorna uma representação dos usuários.
    """
    #TODO: model_dump()
    usuario = Usuario(
        nome_usuario = body.nome_usuario,
        email = body.email,
        senha = body.senha
        )
    Session.add(usuario)
    
    try:
        Session.commit()
    
        return UsuarioViewSchema.model_validate(usuario).model_dump(mode='json'), HTTPStatus.CREATED
    
    except IntegrityError:
        Session.rollback()
        logger.warning(f"Tentativa de cadastro com email já existente")
        return ErrorSchema(
            error_code="EMAIL_ALREADY_EXISTS",
            message="Email já existe").model_dump(), HTTPStatus.CONFLICT
    
    except Exception as e:
        Session.rollback()
        logger.exception(f"Falha inesperada ao tentar criar usuário")
        return ErrorSchema(error_code="INTERNAL_SERVER_ERROR",
                message="Ocorreu um erro interno ao processar a requisição."
                ).model_dump(), HTTPStatus.INTERNAL_SERVER_ERROR

    finally:
        Session.remove()

#TODO: melhorar try/except com ErrorSchema
@usuarios_bp.get('/listar', responses={"200": UsuarioViewSchema, "500": ErrorSchema})
def listar_usuarios():
    """ Retorna uma lista de todos os usuários cadastrados
    """
    try:
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
            "usuarios": [UsuarioViewSchema.model_validate(usuario).model_dump() for usuario in usuarios],
            "quantidade": len(usuarios)
        }, HTTPStatus.OK
    
    except Exception as e:
        logger.exception(f"Erro interno detectado")
        return ErrorSchema(error_code="INTERNAL_SERVER_ERROR",
                message="Ocorreu um erro interno ao processar a requisição."
                ).model_dump(), HTTPStatus.INTERNAL_SERVER_ERROR
    finally:
        Session.remove()

#TODO: change to Path
@usuarios_bp.get('/', responses={"200": UsuarioResponseSchema, "404": ErrorSchema})
def buscar_usuario(query:UsuarioBuscaSchema):
    """Busca e retorna os dados detalhados de um usuário a partir do uuid do usuário
    """
    uuid_usuario = str(query.id_usuario)

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
                "dados": UsuarioResponseSchema.model_validate(usuario).model_dump(mode='json')
            }, HTTPStatus.OK
    
    except Exception as e:
        return {"status": "error", "mensagem": str(e)}, HTTPStatus.INTERNAL_SERVER_ERROR
    
    finally:
        Session.remove()

@usuarios_bp.delete('/',
            responses={"200": UsuarioResponseSchema, "404": ErrorSchema})
def deletar_usuario(query:UsuarioBuscaSchema):
    """Remove um usuário do sistema com base no uuid fornecido.
    Retorna uma resposta indicando o sucesso ou a falha da operação.
    """
    # try:
    uuid_usuario = str(query.id_usuario)        
    # uuid.UUID(uuid_usuario)
    
    # except ValueError:
    #     return {"status": "error", "mensagem": "UUID inválido"}, HTTPStatus.BAD_REQUEST


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