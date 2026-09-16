"""Critique photométrique (symbolique / analytique ou multimodal VLM)."""

import abc
import json
import re
from typing import Optional, Tuple
from PIL import Image
import numpy as np

from photometric_relighting.agent.models import PhotometricTarget
from photometric_relighting.cdl.models import CDLParameters
from photometric_relighting.metrics.models import PhotometricMetrics


class BasePhotometricCritic(abc.ABC):
    """Interface abstraite pour un critique photométrique."""

    @abc.abstractmethod
    def evaluate(
        self,
        current_metrics: PhotometricMetrics,
        target: PhotometricTarget,
        current_cdl: CDLParameters,
        image: Optional[Image.Image] = None,
        iteration: int = 0
    ) -> Tuple[CDLParameters, str, bool]:
        """Évalue les métriques actuelles et prédit un nouveau vecteur ASC CDL.

        Returns:
            Tuple[CDLParameters, str, bool] :
                - Nouveaux paramètres CDL ajustés
                - Raisonnement explicatif
                - Statut de convergence (True si les objectifs sont atteints)
        """
        pass


class RuleBasedPhotometricCritic(BasePhotometricCritic):
    """Critique expert symbolique / analytique fondé sur les lois de la sensitométrie.

    Ajuste déterministement :
    - Slope : maintien des hautes lumières et gain global
    - Offset : contrôle du piédestal et de l'écrêtage des ombres
    - Power (gamma) : contrôle de la courbure des tons moyens et du ratio de contraste
    - Saturation : contrôle de la pureté chromatique
    """

    def __init__(
        self,
        key_tolerance: float = 0.03,
        ratio_tolerance: float = 0.8
    ) -> None:
        self.key_tolerance = key_tolerance
        self.ratio_tolerance = ratio_tolerance

    def evaluate(
        self,
        current_metrics: PhotometricMetrics,
        target: PhotometricTarget,
        current_cdl: CDLParameters,
        image: Optional[Image.Image] = None,
        iteration: int = 0
    ) -> Tuple[CDLParameters, str, bool]:
        reasons = []

        # 1. Analyse du Key Index
        key_ok = True
        key_diff = 0.0
        if target.target_key_index is not None:
            key_diff = current_metrics.key_index - target.target_key_index
            if abs(key_diff) > self.key_tolerance:
                key_ok = False

        # 2. Analyse du Lighting Ratio
        ratio_ok = True
        ratio_diff = 0.0
        if target.target_lighting_ratio is not None:
            ratio_diff = target.target_lighting_ratio - current_metrics.lighting_ratio
            if abs(ratio_diff) > self.ratio_tolerance:
                ratio_ok = False

        # 3. Analyse du clipping
        clipping_ok = (
            current_metrics.shadow_clipping_pct <= target.max_shadow_clipping_pct
            and current_metrics.highlight_clipping_pct <= target.max_highlight_clipping_pct
        )

        # Si tous les critères sont satisfaits
        if key_ok and ratio_ok and clipping_ok:
            reason = (
                f"✅ Objectif atteint à l'itération {iteration} : "
                f"Key={current_metrics.key_index:.3f} (cible={target.target_key_index}), "
                f"Ratio={current_metrics.lighting_ratio:.1f}:1 (cible={target.target_lighting_ratio}:1), "
                f"Clipping ombres={current_metrics.shadow_clipping_pct:.1f}%."
            )
            return current_cdl, reason, True

        # Copie des paramètres actuels pour modification progressive
        slope_r, slope_g, slope_b = current_cdl.slope
        offset_r, offset_g, offset_b = current_cdl.offset
        power_r, power_g, power_b = current_cdl.power
        sat = current_cdl.saturation

        # Raisonnement photométrique et ajustements :
        if key_diff > self.key_tolerance:
            # L'image est trop claire par rapport à la cible (ex: medium-key vers low-key)
            reasons.append(
                f"L'ambiance est trop claire (Key Index: {current_metrics.key_index:.2f} > cible {target.target_key_index:.2f})."
            )
            # Augmenter Power pour écraser les tons moyens (comprimer la distribution)
            power_factor = 1.0 + min(0.35, key_diff * 0.8)
            power_r *= power_factor
            power_g *= power_factor
            power_b *= power_factor

            # Si le clipping ombres est faible, on peut baisser légèrement l'offset
            if current_metrics.shadow_clipping_pct < (target.max_shadow_clipping_pct * 0.5):
                offset_drop = min(0.04, key_diff * 0.1)
                offset_r -= offset_drop
                offset_g -= offset_drop
                offset_b -= offset_drop
                reasons.append(f"Abaissement du piédestal (Offset -{offset_drop:.3f}) pour densifier les noirs.")
            
            # Ajustement slope pour préserver la brillance des hautes lumières
            if current_metrics.highlight_clipping_pct < target.max_highlight_clipping_pct:
                slope_boost = 1.05
                slope_r *= slope_boost
                slope_g *= slope_boost
                slope_b *= slope_boost
                reasons.append("Léger gain sur le Slope pour préserver les reflets spéculaires / rim light.")

        elif key_diff < -self.key_tolerance:
            # L'image est trop sombre (ex: vers high-key)
            reasons.append(
                f"L'ambiance est trop sombre (Key Index: {current_metrics.key_index:.2f} < cible {target.target_key_index:.2f})."
            )
            power_factor = max(0.65, 1.0 + key_diff * 0.6)
            power_r *= power_factor
            power_g *= power_factor
            power_b *= power_factor

            offset_boost = min(0.05, abs(key_diff) * 0.1)
            offset_r += offset_boost
            offset_g += offset_boost
            offset_b += offset_boost
            reasons.append(f"Débouchage des ombres (Offset +{offset_boost:.3f}, Power réduit).")

        # Ajustement du ratio de contraste (Lighting Ratio)
        if ratio_diff > self.ratio_tolerance:
            # Contraste insuffisant : augmenter le contraste
            reasons.append(
                f"Le ratio de contraste est trop faible ({current_metrics.lighting_ratio:.1f}:1 contre {target.target_lighting_ratio}:1 ciblé)."
            )
            power_r *= 1.12
            power_g *= 1.12
            power_b *= 1.12
            slope_r *= 1.08
            slope_g *= 1.08
            slope_b *= 1.08
        elif ratio_diff < -self.ratio_tolerance:
            # Contraste excessif : adoucir
            reasons.append(
                f"Le contraste est trop dur ({current_metrics.lighting_ratio:.1f}:1 > cible {target.target_lighting_ratio}:1)."
            )
            power_r *= 0.90
            power_g *= 0.90
            power_b *= 0.90

        # Protection contre l'écrêtage excessif des ombres
        if current_metrics.shadow_clipping_pct > target.max_shadow_clipping_pct:
            excess = current_metrics.shadow_clipping_pct - target.max_shadow_clipping_pct
            rescue_offset = min(0.06, excess * 0.015)
            offset_r += rescue_offset
            offset_g += rescue_offset
            offset_b += rescue_offset
            reasons.append(f"Alerte écrêtage ombres ({current_metrics.shadow_clipping_pct:.1f}%) : relèvement du piédestal.")

        # Protection contre l'écrêtage des hautes lumières
        if current_metrics.highlight_clipping_pct > target.max_highlight_clipping_pct:
            slope_damp = 0.92
            slope_r *= slope_damp
            slope_g *= slope_damp
            slope_b *= slope_damp
            reasons.append(f"Alerte écrêtage blancs ({current_metrics.highlight_clipping_pct:.1f}%) : atténuation du Slope.")

        # Saturation cible
        if target.target_saturation is not None:
            sat = target.target_saturation

        # Bornage de sécurité des paramètres CDL
        new_params = CDLParameters(
            slope=(
                round(float(np.clip(slope_r, 0.2, 3.0)), 3),
                round(float(np.clip(slope_g, 0.2, 3.0)), 3),
                round(float(np.clip(slope_b, 0.2, 3.0)), 3),
            ),
            offset=(
                round(float(np.clip(offset_r, -0.3, 0.3)), 3),
                round(float(np.clip(offset_g, -0.3, 0.3)), 3),
                round(float(np.clip(offset_b, -0.3, 0.3)), 3),
            ),
            power=(
                round(float(np.clip(power_r, 0.2, 3.5)), 3),
                round(float(np.clip(power_g, 0.2, 3.5)), 3),
                round(float(np.clip(power_b, 0.2, 3.5)), 3),
            ),
            saturation=round(float(np.clip(sat, 0.0, 2.5)), 3),
        )

        reasoning_text = " ".join(reasons)
        return new_params, reasoning_text, False


class VLMPromptBuilder:
    """Générateur de prompt ReAct pour modèles Vision-Language (VLM)."""

    @staticmethod
    def build_system_prompt() -> str:
        return (
            "Tu es un directeur de la photographie et coloriste expert (ASC/BSC). "
            "Tu évalues une image rééclairée et ses métriques objectives d'exposition. "
            "Ton rôle est d'ajuster des paramètres formels ASC CDL (Slope, Offset, Power, Saturation) "
            "pour atteindre l'intention esthétique demandée sans détruire l'image.\n\n"
            "Règles d'action :\n"
            "- Slope [R, G, B] : Gain / hautes lumières (typiquement [0.5, 2.0]).\n"
            "- Offset [R, G, B] : Piédestal / ombres profondes (typiquement [-0.15, +0.15]).\n"
            "- Power [R, G, B] : Gamma / courbure des tons moyens (typiquement [0.5, 2.5]).\n"
            "- Saturation : Facteur scalaire (0.0 = N&B, 1.0 = standard).\n\n"
            "Réponds STRICTEMENT au format JSON avec deux clés : 'reasoning' (ton explication) "
            "et 'cdl' ({'slope': [r,g,b], 'offset': [r,g,b], 'power': [r,g,b], 'saturation': s})."
        )

    @staticmethod
    def build_user_prompt(
        current_metrics: PhotometricMetrics,
        target: PhotometricTarget,
        current_cdl: CDLParameters,
        iteration: int
    ) -> str:
        return (
            f"### Itération : {iteration}\n"
            f"### Intention artistique demandée :\n"
            f"- Nom : {target.name}\n"
            f"- Description : {target.description}\n"
            f"- Cible Key Index : {target.target_key_index}\n"
            f"- Cible Lighting Ratio : {target.target_lighting_ratio}:1\n\n"
            f"### Télémétrie photométrique actuelle :\n"
            f"{current_metrics.to_summary_text()}\n\n"
            f"### Paramètres CDL actuels :\n"
            f"{current_cdl.model_dump_json(indent=2)}\n\n"
            f"Fournis ton analyse critique et les nouveaux paramètres CDL."
        )
