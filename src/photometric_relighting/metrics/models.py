"""Modèles Pydantic pour les métriques et la télémétrie photométrique."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ZoneSystemBreakdown(BaseModel):
    """Répartition de l'énergie lumineuse selon le Zone System d'Ansel Adams (Zones 0 à X)."""

    zones_percentage: Dict[str, float] = Field(
        description="Pourcentage de pixels dans chacune des 11 zones (Zone 0 à Zone X)."
    )
    deep_shadows_pct: float = Field(
        description="Pourcentage de pixels dans les Zones 0 à II (ombres profondes / bouchées)."
    )
    mid_tones_pct: float = Field(
        description="Pourcentage de pixels dans les Zones III à VII (tons moyens et textures)."
    )
    specular_highlights_pct: float = Field(
        description="Pourcentage de pixels dans les Zones VIII à X (hautes lumières et reflets spéculaires)."
    )


class PhotometricMetrics(BaseModel):
    """Télémétrie photométrique complète extraite d'une image."""

    key_index: float = Field(
        description="Indice de Key = Médiane(Y) / Max(Y). Low-key typique < 0.20, High-key > 0.45."
    )
    lighting_ratio: float = Field(
        description="Ratio d'éclairage = Percentile_95(Y) / Percentile_10(Y). Ex: 8.0 pour un contraste 8:1."
    )
    median_luminance: float = Field(
        description="Luminance médiane normalisée dans [0.0, 1.0]."
    )
    median_luminance_255: float = Field(
        description="Luminance médiane projetée sur l'échelle standard [0, 255]."
    )
    max_luminance: float = Field(
        description="Luminance maximale observée dans [0.0, 1.0]."
    )
    min_luminance: float = Field(
        description="Luminance minimale observée dans [0.0, 1.0]."
    )
    shadow_clipping_pct: float = Field(
        description="Pourcentage de pixels complètement écrêtés au noir (Y <= 0.005 / 255)."
    )
    highlight_clipping_pct: float = Field(
        description="Pourcentage de pixels complètement écrêtés au blanc (Y >= 254 / 255)."
    )
    dynamic_range_stops: float = Field(
        description="Plage dynamique effective estimée en stops photographiques (EV)."
    )
    zone_system: ZoneSystemBreakdown = Field(
        description="Cartographie détaillée des zones d'exposition Ansel Adams."
    )
    perceived_lightness_mean: float = Field(
        description="Clarté perçue moyenne CIE L* (0 à 100)."
    )

    def to_summary_text(self) -> str:
        """Génère un résumé textuel formaté pour l'injection dans le prompt du VLM."""
        return (
            f"- Key Index: {self.key_index:.3f}\n"
            f"- Lighting Ratio (P95/P10): {self.lighting_ratio:.1f}:1\n"
            f"- Médiane de luminance: {self.median_luminance_255:.1f} / 255 ({self.median_luminance:.3f})\n"
            f"- Ombres profondes (Zones 0-II): {self.zone_system.deep_shadows_pct:.1f}%\n"
            f"- Tons moyens (Zones III-VII): {self.zone_system.mid_tones_pct:.1f}%\n"
            f"- Hautes lumières (Zones VIII-X): {self.zone_system.specular_highlights_pct:.1f}%\n"
            f"- Clipping ombres absolues (Zone 0): {self.shadow_clipping_pct:.2f}%\n"
            f"- Clipping hautes lumières: {self.highlight_clipping_pct:.2f}%\n"
            f"- Plage dynamique estimée: {self.dynamic_range_stops:.1f} stops (EV)"
        )
