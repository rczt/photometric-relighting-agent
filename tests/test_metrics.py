"""Tests unitaires pour l'extracteur de métriques photométriques."""

import numpy as np
import pytest

from photometric_relighting.metrics import extract_photometric_metrics


def test_zone_system_sum_100_percent():
    """Vérifie que la somme des pourcentages des 11 zones vaut exactement 100%."""
    img = np.random.uniform(0.0, 1.0, (100, 100, 3)).astype(np.float32)
    metrics = extract_photometric_metrics(img)
    total_pct = sum(metrics.zone_system.zones_percentage.values())
    assert pytest.approx(total_pct, abs=1e-3) == 100.0


def test_key_index_dark_image():
    """Vérifie qu'une image très sombre produit un Key Index < 0.20."""
    # Image très sombre avec un seul pixel blanc (pour max = 1.0)
    img = np.full((50, 50, 3), 0.05, dtype=np.float32)
    img[0, 0] = [1.0, 1.0, 1.0]
    metrics = extract_photometric_metrics(img)
    assert metrics.key_index < 0.15


def test_lighting_ratio_calculation():
    """Vérifie le ratio entre P95 et P10."""
    # Crée une image où P95 est autour de 0.8 et P10 autour de 0.1
    vals = np.linspace(0.05, 0.85, 1000).astype(np.float32)
    img = np.tile(vals[:, None, None], (1, 10, 3))
    metrics = extract_photometric_metrics(img)
    assert metrics.lighting_ratio > 4.0
