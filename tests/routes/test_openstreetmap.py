import json

import responses
import uuid
import logging
from pydantic import ValidationError

from http import HTTPStatus
from sqlalchemy.exc import IntegrityError

from schemas.restaurante import RestauranteViewSchema
from utils.openstreetmap import OpenStreetMapService

@responses.activate
def test_buscar_restaurantes_proximidade_returns_payload_on_200():
    fake_payload = {
        "sucesso": True,
        "restaurantes": [
            {
                "id_osm": "123",
                "nome": "Pizza Place",
                "latitude": -23.55,
                "longitude": -46.63
            }
        ],
        "bbox_utilizado": "-23.6,-46.7,-23.5,-46.6"
    }

    responses.add(
        responses.POST,
        "http://127.0.0.1:8001/contexto/restaurantes/buscar",
        json=fake_payload,
        status=200
    )

    result = OpenStreetMapService.buscar_restaurantes_proximidade(
        latitude=-23.55,
        longitude=-46.63,
        raio_km=5,
        tipo="restaurant"
    )
    assert result["sucesso"] is True
    assert len(result["restaurantes"]) == 1
    assert result["restaurantes"][0]["nome"] == "Pizza Place"
    assert result["bbox_utilizado"] == "-23.6,-46.7,-23.5,-46.6"

@responses.activate
def test_buscar_restaurantes_proximidade_sends_correct_payload():
    
    # make sure the answer is 200
    responses.add(
        responses.POST,
        "http://127.0.0.1:8001/contexto/restaurantes/buscar",
        json={
            "sucesso": True,
            "restaurantes": [],
        }
    )

    OpenStreetMapService.buscar_restaurantes_proximidade(
        latitude=-23.55,
        longitude=-46.63,
        raio_km=10,
        tipo="pizza"
    )
    
    assert len(responses.calls) == 1
    body = json.loads(responses.calls[0].request.body)

    assert body["latitude"]  == -23.55
    assert body["longitude"] == -46.63
    assert body["raio_km"]   == 10
    assert body["tipo"]      == "pizza"
    assert len(body.keys())  == 4