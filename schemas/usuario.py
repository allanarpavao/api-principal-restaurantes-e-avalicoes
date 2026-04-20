from pydantic import BaseModel, ConfigDict, Field, UUID4, EmailStr
from typing import Optional, List

from datetime import datetime
from models.usuario import Usuario

class UsuarioSchema(BaseModel):
    """Define os campos de um novo usuário a ser inserido
    """
    nome_usuario: str = Field(..., json_schema_extra={"example": "João da Silva"})
    email: EmailStr = Field(..., json_schema_extra={"example": "joao@exemplo.com"})
    senha: str = Field(..., json_schema_extra={"example": "SenhaForte!123"})

class UsuarioBuscaSchema(BaseModel):
    """ Define como deve ser a estrutura que representa a busca.
        A busca será feita apenas com base no uuid do usuario.
    """
    id_usuario: UUID4 = Field(..., 
        description="Identificador único do usuário no formato UUID4.",
        json_schema_extra={"example": "7a743fa4-57b5-4b0b-b97a-5da34a58bf62"}
    )

class UsuarioResponseSchema(BaseModel):
    """ Define a resposta a uma busca direta pelo usuario
    """
    model_config = ConfigDict(from_attributes=True)
    nome_usuario: str
    email: EmailStr
    data_criacao: datetime
    usuario_id: UUID4

class UsuarioViewSchema(BaseModel):
    """Define como o usuario será retornado
    """
    model_config = ConfigDict(from_attributes=True)
    email: EmailStr
    nome_usuario: str
    data_criacao: datetime
