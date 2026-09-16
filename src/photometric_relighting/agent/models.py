"""Modèles de données pour la boucle de rétroaction agentique."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from PIL import Image

from photometric_relighting.cdl.models import CDLParameters
from photometric_relighting.metrics.models import PhotometricMetrics


class PhotometricTarget(BaseModel):
    """Cible photométrique définie par l'utilisateur ou déduite de la consigne."""

    name: str = Field(default="Custom Target", description="Nom du profil ou preset photométrique.")
    description: str = Field(default="", description="Description en langage naturel de l'intention artistique.")
    target_key_index: Optional[float] = Field(
        default=None,
        description="Indice de Key cible (ex: 0.15 pour low-key, 0.55 pour high-key)."
    )
    target_lighting_ratio: Optional[float] = Field(
        default=None,
        description="Lighting Ratio cible P95/P10 (ex: 8.0 pour un contraste 8:1)."
    )
    max_shadow_clipping_pct: float = Field(
        default=2.0,
        description="Pourcentage maximal toléré de pixels écrêtés au noir absolu."
    )
    max_highlight_clipping_pct: float = Field(
        default=1.5,
        description="Pourcentage maximal toléré de pixels écrêtés au blanc pur."
    )
    target_saturation: Optional[float] = Field(
        default=1.0,
        description="Saturation cible (ex: 0.85 pour un style cinéma désaturé)."
    )

    @classmethod
    def get_preset(cls, preset_name: str) -> "PhotometricTarget":
        """Renvoie une configuration prédéfinie selon des normes cinématographiques courantes."""
        presets = {
            "low_key_dramatic": cls(
                name="Low-Key Dramatique (8:1)",
                description="Ambiance sombre et contrastée, ombres denses mais lisibles, hautes lumières piquées.",
                target_key_index=0.16,
                target_lighting_ratio=8.0,
                max_shadow_clipping_pct=2.5,
                target_saturation=0.9,
            ),
            "film_noir": cls(
                name="Film Noir / Chiaroscuro (12:1)",
                description="Éclairage clair-obscur radical inspiré du cinéma expressionniste et du film noir.",
                target_key_index=0.12,
                target_lighting_ratio=12.0,
                max_shadow_clipping_pct=4.0,
                target_saturation=0.4,
            ),
            "high_key_fashion": cls(
                name="High-Key Lumineux / Beauté",
                description="Ombres très débouchées, tons moyens lumineux et enveloppants, ratio doux.",
                target_key_index=0.55,
                target_lighting_ratio=2.5,
                max_shadow_clipping_pct=0.2,
                target_saturation=1.05,
            ),
            "balanced_cinematic": cls(
                name="Cinématique Équilibré (4:1)",
                description="Contraste cinématographique naturel, dynamique préservée, respect des tons chair.",
                target_key_index=0.30,
                target_lighting_ratio=4.0,
                max_shadow_clipping_pct=1.0,
                target_saturation=0.95,
            ),
        }
        return presets.get(preset_name.lower(), presets["low_key_dramatic"])


class FeedbackStep(BaseModel):
    """Étape individuelle au sein de la boucle de rétroaction."""

    iteration: int = Field(description="Numéro de l'itération (0 = initial).")
    metrics: PhotometricMetrics = Field(description="Métriques mesurées à cette itération.")
    cdl_params: CDLParameters = Field(description="Paramètres CDL appliqués.")
    reasoning: str = Field(description="Raisonnement textuel du critique (VLM ou règle experte).")
    converged: bool = Field(default=False, description="Indique si les critères ont été atteints à cette passe.")


class FeedbackLoopResult(BaseModel):
    """Résultat global de l'exécution de la boucle fermée."""

    initial_metrics: PhotometricMetrics
    final_metrics: PhotometricMetrics
    final_cdl: CDLParameters
    steps: List[FeedbackStep]
    converged: bool
    iterations_count: int
    elapsed_seconds: float
    summary: str
