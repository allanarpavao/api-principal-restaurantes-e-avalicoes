from datetime import datetime
from typing import List
from typing import Optional
from sqlalchemy import Float, ForeignKey, DateTime, Integer, func
from sqlalchemy import String
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
import uuid

from models import Base
from models.avaliacao import Avaliacao

class Restaurante(Base):
    __tablename__ = "restaurantes"

    # criacao do restaurante id
    restaurante_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
    # conexao com Overpass
    id_osm: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True, index=True)
    
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    endereco: Mapped[str] = mapped_column(String(50), nullable=False)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cuisine: Mapped[str] = mapped_column(String(100), nullable=True)
    telefone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    
    data_criacao: Mapped[Optional[datetime]] = mapped_column(DateTime(), default=lambda: datetime.now(), server_default=func.now()) 

    # relacionamento
    avaliacoes: Mapped[list['Avaliacao']] = relationship("Avaliacao", back_populates="restaurante", cascade='all, delete-orphan')