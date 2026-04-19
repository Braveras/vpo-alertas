import hashlib
from dataclasses import dataclass


@dataclass
class Listing:
    titulo: str
    url: str
    fuente: str
    fecha: str

    @property
    def id(self) -> str:
        return hashlib.sha1(self.url.encode()).hexdigest()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "titulo": self.titulo,
            "url": self.url,
            "fuente": self.fuente,
            "fecha": self.fecha,
        }
