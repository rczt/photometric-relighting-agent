"""Modèles Pydantic pour la représentation et validation des paramètres ASC CDL."""

from typing import Tuple
from pydantic import BaseModel, Field


class CDLParameters(BaseModel):
    """Paramètres standard de correction couleur ASC CDL (American Society of Cinematographers Color Decision List).

    Formule par canal :
        out = clamp((in * slope + offset), 0, inf) ** power
    Suivi de la saturation globale :
        out_sat = Luma + saturation * (out - Luma)
    """

    slope: Tuple[float, float, float] = Field(
        default=(1.0, 1.0, 1.0),
        description="Pente / Gain pour les canaux RGB (>= 0). Modifie l'exposition sans déplacer le point noir."
    )
    offset: Tuple[float, float, float] = Field(
        default=(0.0, 0.0, 0.0),
        description="Décalage / Piédestal pour les canaux RGB. Élève ou abaisse uniformément les niveaux."
    )
    power: Tuple[float, float, float] = Field(
        default=(1.0, 1.0, 1.0),
        description="Exposant / Gamma pour les canaux RGB (> 0). Ajuste la courbure des tons moyens."
    )
    saturation: float = Field(
        default=1.0,
        ge=0.0,
        description="Facteur global de saturation (>= 0). 0 = noir et blanc, 1 = neutre, >1 = hypersaturé."
    )

    def to_dict(self) -> dict:
        """Exporte les paramètres sous forme de dictionnaire."""
        return self.model_dump()
