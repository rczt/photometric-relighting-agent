"""Tests unitaires pour l'opérateur ASC CDL."""

import numpy as np
from PIL import Image
import pytest

from photometric_relighting.cdl import CDLParameters, apply_cdl


def test_cdl_identity():
    """Vérifie que les paramètres d'identité ne modifient pas l'image."""
    img = np.random.uniform(0.1, 0.9, (64, 64, 3)).astype(np.float32)
    identity = CDLParameters()
    result = apply_cdl(img, identity)
    np.testing.assert_allclose(result, img, atol=1e-5)


def test_cdl_slope():
    """Vérifie l'impact du slope (multiplication linéaire)."""
    img = np.full((10, 10, 3), 0.5, dtype=np.float32)
    params = CDLParameters(slope=(1.5, 1.5, 1.5))
    result = apply_cdl(img, params)
    np.testing.assert_allclose(result, 0.75, atol=1e-5)


def test_cdl_offset():
    """Vérifie l'impact de l'offset (décalage du piédestal)."""
    img = np.full((10, 10, 3), 0.3, dtype=np.float32)
    params = CDLParameters(offset=(0.1, 0.1, 0.1))
    result = apply_cdl(img, params)
    np.testing.assert_allclose(result, 0.4, atol=1e-5)


def test_cdl_power():
    """Vérifie l'élévation à la puissance gamma."""
    img = np.full((10, 10, 3), 0.5, dtype=np.float32)
    params = CDLParameters(power=(2.0, 2.0, 2.0))
    result = apply_cdl(img, params)
    np.testing.assert_allclose(result, 0.25, atol=1e-5)


def test_cdl_saturation_zero_makes_grayscale():
    """Vérifie que la saturation 0 rend l'image strictement monochromatique (R=G=B)."""
    img = np.random.uniform(0.0, 1.0, (32, 32, 3)).astype(np.float32)
    params = CDLParameters(saturation=0.0)
    result = apply_cdl(img, params)
    # R, G et B doivent être identiques
    np.testing.assert_allclose(result[:, :, 0], result[:, :, 1], atol=1e-5)
    np.testing.assert_allclose(result[:, :, 1], result[:, :, 2], atol=1e-5)


def test_cdl_pil_support():
    """Vérifie le support natif des objets PIL Image."""
    pil_img = Image.new("RGB", (32, 32), color=(100, 150, 200))
    params = CDLParameters(slope=(1.1, 1.0, 0.9))
    result = apply_cdl(pil_img, params)
    assert isinstance(result, Image.Image)
    assert result.size == (32, 32)
