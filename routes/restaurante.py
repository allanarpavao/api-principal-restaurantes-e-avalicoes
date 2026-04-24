from urllib.parse import unquote
import uuid
from flask_openapi3 import APIBlueprint, Tag
from http import HTTPStatus
from sqlalchemy.exc import IntegrityError
from flask import request
from typing import Optional, Dict, Any

from models import Session
from models.restaurante import Restaurante
from schemas.error import ErrorSchema
from schemas.restaurante import DistanciaQuery, ListagemRestaurantesSchema, RestauranteBuscaSchema, RestaurantePathSchema, RestauranteSchema, RestauranteUpdateSchema, RestauranteViewSchema

from schemas.services import BuscaRestaurantesProximidadeRequest
from utils.openstreetmap import OpenStreetMapService

restaurantes_bp = APIBlueprint(
    'restaurantes',
    __name__,
    url_prefix='/restaurantes',
    abp_tags=[Tag(name='Restaurantes', description='Operações de restaurantes')]
)


def sincronizar_restaurantes_overpass(restaurantes: list):
    """Função que sincroniza DB"""
    try:
        if not restaurantes:
            return {'sincronizados': 0, 'duplicados': 0}
        
        sincronizados = 0
        duplicados = 0
        
        for resto_ext in restaurantes:
            try:
                existe = Session.query(Restaurante).filter_by(
                    id_osm=str(resto_ext.get('id_osm'))
                ).first()
                
                if existe:
                    duplicados += 1
                    continue
                
                novo = Restaurante(
                    id_osm=str(resto_ext.get('id_osm')),
                    nome=resto_ext.get('nome', 'Sem nome'),
                    endereco=resto_ext.get('endereco') or 'Sem endereço',
                    cuisine=resto_ext.get('cuisine', 'Não informado'),
                    latitude=resto_ext.get('latitude'),
                    longitude=resto_ext.get('longitude'),
                    telefone=resto_ext.get('telefone'),
                    website=resto_ext.get('website')
                )
                
                Session.add(novo)
                sincronizados += 1
                
            except Exception as e:
                print(f"Erro ao sincronizar {resto_ext.get('nome')}: {str(e)}")
        
        Session.commit()
        return {'sincronizados': sincronizados, 'duplicados': duplicados}
        
    except Exception as e:
        Session.rollback()
        raise Exception(str(e))
    finally:
        Session.remove()


def anexar_distancia_ao_restaurante(dados: Dict[str, Any], restaurante) -> Dict[str, Any]:
    """
    Lê latitude_usuario/longitude_usuario da query string,
    chama a API secundária e, se der certo, adiciona distancia_km ao dict.
    Não lança erro se faltar dado; apenas retorna o dict original.
    """
    lat_user = request.args.get("latitude_usuario", type=float)
    lng_user = request.args.get("longitude_usuario", type=float)

    if (
        lat_user is None or lng_user is None or
        restaurante.latitude is None or restaurante.longitude is None
    ):
        return dados

    dist_res = OpenStreetMapService.calcular_distancia(
        lat1=lat_user,
        lng1=lng_user,
        lat2=restaurante.latitude,
        lng2=restaurante.longitude,
    )

    if dist_res.get("sucesso") and dist_res.get("distancia_km") is not None:
        dados["distancia_km"] = dist_res["distancia_km"]

    return dados


@restaurantes_bp.post('/criar', responses={"201": RestauranteViewSchema, "409": ErrorSchema, "400": ErrorSchema})
def criar_restaurante(body: RestauranteSchema):
    """Adiciona um novo restaurante à base de dados

    Retorna uma representação do restaurante.
    """
    try:
        restaurante = Restaurante(
            nome=body.nome,
            endereco=body.endereco,
            cuisine=body.cuisine,
            latitude=body.latitude,
            longitude=body.longitude,
            telefone=body.telefone,
            website=body.website,
            id_osm=body.id_osm
        )

        Session.add(restaurante)
        Session.commit()

        return RestauranteViewSchema.model_validate(restaurante).model_dump(), HTTPStatus.CREATED
    
    #TODO: verificar mensagem de erro especifica
    except IntegrityError:
        Session.rollback()

        return {"erro": "Nome já existe"}, HTTPStatus.CONFLICT
    
    except Exception as e:
        Session.rollback()
        return {"erro": str(e)}, HTTPStatus.BAD_REQUEST

    finally:
        Session.remove()

@restaurantes_bp.get('/<int:restaurante_id>', responses={"200": ListagemRestaurantesSchema, "404": ErrorSchema})
def buscar_restaurante(path:RestaurantePathSchema, query:DistanciaQuery):
    """Busca e retorna os dados detalhados de um restaurante a partir do id
        Opcionalmente, calcula distância entre usuário e restaurante.
    """
   
    numero_restaurante = path.restaurante_id
    restaurante = Session.query(Restaurante).filter(Restaurante.restaurante_id == numero_restaurante).first()

    if not restaurante:
        return {
                "status": "error",
                "mensagem": f"Restaurante não localizado no sistema."
            }, HTTPStatus.NOT_FOUND
    try:
        dados_restaurante = RestauranteViewSchema.model_validate(restaurante).model_dump()
        dados_restaurante = anexar_distancia_ao_restaurante(dados_restaurante, restaurante)
        
        return {
            "status": "success",
            "dados": dados_restaurante
        }, HTTPStatus.OK
    
    except Exception as e:
        return {"status": "error", "mensagem": str(e)}, HTTPStatus.INTERNAL_SERVER_ERROR
    
    finally:
        Session.remove()


@restaurantes_bp.delete('/<int:restaurante_id>',
            responses={"200": ListagemRestaurantesSchema, "404": ErrorSchema})
def deletar_restaurante(path: RestaurantePathSchema):
    """Remove um restaurante do sistema com base no id fornecido.
    Retorna uma resposta indicando o sucesso ou a falha da operação.
    """
    
    numero_restaurante = path.restaurante_id
   
    try:
        restaurante = Session.query(Restaurante).filter(Restaurante.restaurante_id == numero_restaurante).first()
        
        if restaurante:
            Session.query(Restaurante).filter(Restaurante.restaurante_id == numero_restaurante).delete()
            Session.commit()
            
            return {
                "status": "success",
                "mensagem": f"Restaurante ({numero_restaurante}) '{restaurante.nome}' removido com sucesso."
            }, HTTPStatus.OK
        else:
            return {
                "status": "error",
                "mensagem": f"Restaurante não encontrado no sistema."
            }, HTTPStatus.NOT_FOUND
    
    except IntegrityError:
        Session.rollback()
    
        return {"status": "error", "mensagem": "Não é possível deletar"}, HTTPStatus.CONFLICT
    
    except Exception as e:
        Session.rollback()

        return {"status": "error", "mensagem": str(e)}, HTTPStatus.INTERNAL_SERVER_ERROR

    finally:
        Session.remove()

@restaurantes_bp.patch('/<int:restaurante_id>', responses={"200": RestauranteViewSchema, "404": ErrorSchema, "400": ErrorSchema})
def atualizar_restaurante(path: RestaurantePathSchema, body: RestauranteUpdateSchema):
    """Atualiza parcialmente um restaurante existente.
    Apenas os campos enviados serão atualizados
    """
    
    restaurante = Session.query(Restaurante).filter(Restaurante.restaurante_id == path.restaurante_id).first()

    if not restaurante:
        return {"erro": "Restaurante não encontrado"}, HTTPStatus.NOT_FOUND
    
    try:
        dados_update = body.model_dump(exclude_unset=True)

        for campo, valor in dados_update.items():
            setattr(restaurante, campo, valor)
        
        Session.commit()
        return RestauranteViewSchema.model_validate(restaurante).model_dump(), HTTPStatus.OK

    except IntegrityError:
        Session.rollback()
    
        return {"status": "error", "mensagem": "Não é possível editar restaurante"}, HTTPStatus.CONFLICT
    
    except Exception as e:
        Session.rollback()

        return {"status": "error", "mensagem": str(e)}, HTTPStatus.INTERNAL_SERVER_ERROR
    
    finally:
        Session.remove()


@restaurantes_bp.post('/buscar-proximidade')
def buscar_restaurantes(body:BuscaRestaurantesProximidadeRequest):
    """Busca restaurantes próximos e os salva no banco de dados.

    """
    resultado = OpenStreetMapService.buscar_restaurantes_proximidade(
        latitude=body.latitude,
        longitude=body.longitude,
        raio_km=body.raio_km,
        tipo=body.tipo
    )
    if resultado["sucesso"]:
        sync = sincronizar_restaurantes_overpass(resultado['restaurantes'])
            
        return {
                'sucesso': True,
                'total': len(resultado['restaurantes']),
                'sincronizacao': {
                    'sincronizados': sync['sincronizados'],
                    'duplicados': sync['duplicados']
                },
                'bbox_utilizado': resultado.get('bbox_utilizado'),
                'mensagem': f"Sincronizou {sync['sincronizados']} restaurantes com sucesso"
            }, HTTPStatus.OK
    else:
        return resultado, HTTPStatus.BAD_REQUEST
    