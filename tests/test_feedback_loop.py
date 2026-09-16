"""Tests unitaires pour la boucle de rétroaction agentique."""

import numpy as np
from PIL import Image
import pytest

from photometric_relighting.agent import PhotometricFeedbackLoop, PhotometricTarget


def test_feedback_loop_execution():
    """Vérifie l'exécution complète de la boucle fermée sans erreur."""
    # Créer un dégradé simulé
    x = np.linspace(0, 1, 128)
    y = np.linspace(0, 1, 128)
    xx, yy = np.meshgrid(x, y)
    grad = (0.5 * np.sin(xx * np.pi) + 0.5 * np.cos(yy * np.pi) * 0.5 + 0.25).astype(np.float32)
    img = np.dstack([grad, grad, grad])

    loop = PhotometricFeedbackLoop()
    target = PhotometricTarget.get_preset("low_key_dramatic")
    final_img, result = loop.run(img, target=target, max_iterations=3)

    assert isinstance(final_img, Image.Image)
    assert result.iterations_count > 0
    assert len(result.steps) == result.iterations_count
    assert result.final_metrics is not None
