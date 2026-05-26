from http import HTTPStatus
import requests
import os


BASE_URL = os.getenv("SECONDARY_API_BASE_URL", "http://127.0.0.1:8001")
TIMEOUT = int(os.getenv("SECONDARY_API_TIMEOUT", "30"))

# BASE_URL = "http://127.0.0.1:8001"
# TIMEOUT = 30

class OpenStreetMapService:
    """Serviço que integra com OpenStreetMap via API Secundária"""
    @staticmethod
    def buscar_restaurantes_proximidade(latitude: float, longitude: float, raio_km: float = 5, tipo: str = "restaurant"):
        """Busca restaurantes próximos via API Secundária"""
        try:
            response = requests.post(
                f"{BASE_URL}/contexto/restaurantes/buscar",
                json={
                    "latitude": latitude,
                    "longitude": longitude,
                    "raio_km": raio_km,
                    "tipo": tipo
                },
                timeout=TIMEOUT
            )
            
            if response.status_code == HTTPStatus.OK:
                return response.json()
            else:
                return {"sucesso": False, "erro": f"Status {response.status_code}"}
                
        except Exception as e:
            return {"sucesso": False, "erro": str(e)}

    @staticmethod
    def obter_endereco(latitude: float, longitude: float):
        try:
            response = requests.post(
                f"{BASE_URL}/contexto/restaurantes/endereco",
                json={"latitude": latitude, "longitude": longitude},
                timeout=TIMEOUT
            )
            return response.json() if response.status_code == HTTPStatus.OK else {"sucesso": False}
        except Exception as e:
            return {"sucesso": False, "erro": str(e)}

    @staticmethod
    def calcular_distancia(lat1: float, lng1: float, lat2: float, lng2: float):
        try:
            response = requests.post(
                f"{BASE_URL}/contexto/restaurantes/distancia",
                json={
                    "lat_origem": lat1,
                    "lng_origem": lng1,
                    "lat_destino": lat2,
                    "lng_destino": lng2
                },
                timeout=TIMEOUT
            )
            return response.json() if response.status_code == HTTPStatus.OK else {"sucesso": False}
        except Exception as e:
            return {"sucesso": False, "erro": str(e)}