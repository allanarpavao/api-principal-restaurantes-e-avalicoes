from pydantic import BaseModel, ConfigDict
from typing import Optional, List

from datetime import datetime
from models.usuario import Usuario

class UsuarioSchema(BaseModel):
    """Define os campos de um novo usuário a ser inserido
    """
    email: str = "fulanodesouza@gmail.com"
    nome_usuario: str = "Fulano de Souza Rodrigues"
    senha: str = "senha123"


class UsuarioBuscaSchema(BaseModel):
    """ Define como deve ser a estrutura que representa a busca.
        A busca será feita apenas com base no uuid do usuario.
    """
    id_usuario: str = "7a743fa4-57b5-4b0b-b97a-5da34a58bf62"


class ListagemUsuariosSchema(BaseModel):
    """ Define como uma listagem de produtos será retornada.
    """
    usuarios: List[UsuarioSchema]


class UsuarioViewSchema(BaseModel):
    """Define como o usuario será retornado
    """
    model_config = ConfigDict(from_attributes=True)
    email: str
    nome_usuario: str
    data_criacao: datetime
