"""Boucle fermée de rétroaction photométrique (Closed-Loop ReAct)."""

import time
from typing import Optional, Tuple, Union
import numpy as np
from PIL import Image

from photometric_relighting.agent.critic import BasePhotometricCritic, RuleBasedPhotometricCritic
from photometric_relighting.agent.models import (
    FeedbackLoopResult,
    FeedbackStep,
    PhotometricTarget,
)
from photometric_relighting.cdl.models import CDLParameters
from photometric_relighting.cdl.operator import apply_cdl
from photometric_relighting.metrics.extractor import extract_photometric_metrics
from photometric_relighting.metrics.models import PhotometricMetrics


class PhotometricFeedbackLoop:
    """Orchestrateur de la boucle agentique neuro-symbolique fermée."""

    def __init__(self, critic: Optional[BasePhotometricCritic] = None) -> None:
        self.critic = critic or RuleBasedPhotometricCritic()

    def run(
        self,
        base_image: Union[np.ndarray, Image.Image],
        target: PhotometricTarget,
        max_iterations: int = 4,
        subject_mask: Optional[np.ndarray] = None,
    ) -> Tuple[Image.Image, FeedbackLoopResult]:
        """Exécute la boucle de rétroaction itérative.

        Args:
            base_image: Image rééclairée initiale (entrée neutre ou sortie IC-Light).
            target: Spécification des métriques et intention visée.
            max_iterations: Nombre maximum de passes autorisées (défaut : 4).
            subject_mask: Masque optionnel du sujet pour le calcul du Lighting Ratio.

        Returns:
            Tuple[Image.Image, FeedbackLoopResult] :
                - Image finale étalonnée en PIL.Image
                - Rapport complet de la boucle (métriques, étapes, CDL final)
        """
        start_time = time.time()

        # Conversion initiale en PIL Image pour uniformiser
        if isinstance(base_image, np.ndarray):
            if np.issubdtype(base_image.dtype, np.floating):
                pil_base = Image.fromarray(
                    np.round(np.clip(base_image, 0.0, 1.0) * 255.0).astype(np.uint8)
                )
            else:
                pil_base = Image.fromarray(base_image.astype(np.uint8))
        else:
            pil_base = base_image.convert("RGB")

        # Paramètres CDL initiaux neutres (Identité)
        current_cdl = CDLParameters(
            slope=(1.0, 1.0, 1.0),
            offset=(0.0, 0.0, 0.0),
            power=(1.0, 1.0, 1.0),
            saturation=1.0,
        )

        steps = []
        current_image = pil_base
        initial_metrics: Optional[PhotometricMetrics] = None
        converged = False

        for it in range(max_iterations):
            # 1. Application du vecteur CDL courant sur l'image source de base
            current_image = apply_cdl(pil_base, current_cdl)

            # 2. Télémétrie : extraction des métriques
            metrics = extract_photometric_metrics(current_image, subject_mask=subject_mask)
            if it == 0:
                initial_metrics = metrics

            # 3. Évaluation par le critique
            next_cdl, reasoning, is_converged = self.critic.evaluate(
                current_metrics=metrics,
                target=target,
                current_cdl=current_cdl,
                image=current_image,
                iteration=it,
            )

            # Enregistrement de l'étape
            step = FeedbackStep(
                iteration=it,
                metrics=metrics,
                cdl_params=current_cdl,
                reasoning=reasoning,
                converged=is_converged,
            )
            steps.append(step)

            if is_converged:
                converged = True
                break

            # Mise à jour pour la prochaine itération
            current_cdl = next_cdl

        # Si arrêt par nombre max d'itérations, appliquer la dernière proposition CDL
        if not converged:
            current_image = apply_cdl(pil_base, current_cdl)
            final_metrics = extract_photometric_metrics(current_image, subject_mask=subject_mask)
        else:
            final_metrics = steps[-1].metrics

        elapsed = round(time.time() - start_time, 3)

        summary = (
            f"Boucle terminée en {len(steps)} itération(s) ({elapsed}s). "
            f"Statut : {'CONVERGÉ ✅' if converged else 'LIMITE ATTEINTE ⚠️'}.\n"
            f"- Key Index : {initial_metrics.key_index:.3f} ➔ {final_metrics.key_index:.3f} (cible: {target.target_key_index})\n"
            f"- Ratio de contraste : {initial_metrics.lighting_ratio:.1f}:1 ➔ {final_metrics.lighting_ratio:.1f}:1 (cible: {target.target_lighting_ratio}:1)\n"
            f"- CDL Final : Slope={current_cdl.slope}, Offset={current_cdl.offset}, Power={current_cdl.power}, Sat={current_cdl.saturation}"
        )

        result = FeedbackLoopResult(
            initial_metrics=initial_metrics,
            final_metrics=final_metrics,
            final_cdl=current_cdl,
            steps=steps,
            converged=converged,
            iterations_count=len(steps),
            elapsed_seconds=elapsed,
            summary=summary,
        )

        return current_image, result
