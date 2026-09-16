"""Extracteur de métriques photométriques et cartographie Zone System."""

from typing import Optional, Union
import numpy as np
from PIL import Image

from photometric_relighting.metrics.models import PhotometricMetrics, ZoneSystemBreakdown

REC709_WEIGHTS = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


def rgb_to_relative_luminance(rgb_float: np.ndarray) -> np.ndarray:
    """Calcule la luminance relative standard Y (Rec. 709).

    Y = 0.2126 * R + 0.7152 * G + 0.0722 * B
    """
    return np.sum(rgb_float[:, :, :3] * REC709_WEIGHTS, axis=2)


def relative_luminance_to_cielab_l(y: np.ndarray) -> np.ndarray:
    """Convertit la luminance relative Y in [0, 1] en clarté perceptive CIE L* in [0, 100].

    Formule standard CIE 1976 :
        f(t) = t^(1/3) si t > (6/29)^3 sinon 1/3 * (29/6)^2 * t + 4/29
        L* = 116 * f(Y) - 16
    """
    epsilon = 216.0 / 24389.0  # (6/29)^3 ~ 0.008856
    kappa = 24389.0 / 27.0     # (29/3)^3 ~ 903.3

    fy = np.where(y > epsilon, np.cbrt(np.maximum(y, 1e-7)), (kappa * y + 16.0) / 116.0)
    l_star = 116.0 * fy - 16.0
    return np.clip(l_star, 0.0, 100.0)


def extract_photometric_metrics(
    image: Union[np.ndarray, Image.Image],
    subject_mask: Optional[np.ndarray] = None,
    eps: float = 1e-5
) -> PhotometricMetrics:
    """Extrait la télémétrie photométrique rigoureuse d'une image.

    Args:
        image: Image source (PIL.Image ou np.ndarray en uint8 [0, 255] ou float32 [0, 1]).
        subject_mask: Masque binaire optionnel (2D, bool ou float) pour focaliser
                      le calcul du Lighting Ratio sur le sujet / personnage.
        eps: Epsilon pour la stabilité numérique.

    Returns:
        PhotometricMetrics contenant Key Index, Lighting Ratio, Zone System et statistiques.
    """
    if isinstance(image, Image.Image):
        img_np = np.asarray(image.convert("RGB"), dtype=np.float32) / 255.0
    elif isinstance(image, np.ndarray):
        if np.issubdtype(image.dtype, np.integer):
            img_np = image.astype(np.float32) / 255.0
        else:
            img_np = image.astype(np.float32)
    else:
        raise TypeError(f"Format d'image non supporté : {type(image)}")

    # Calcul de la luminance relative Y [0, 1]
    y_full = rgb_to_relative_luminance(img_np)
    y_flat = y_full.flatten()

    # Sélection des pixels pour le ratio du sujet (si masque présent)
    if subject_mask is not None:
        mask_bool = subject_mask > 0.5
        if np.any(mask_bool):
            y_subject = y_full[mask_bool]
        else:
            y_subject = y_flat
    else:
        y_subject = y_flat

    # 1. Key Index = Médiane(Y) / Max(Y)
    max_y = float(np.max(y_flat))
    median_y = float(np.median(y_flat))
    min_y = float(np.min(y_flat))
    key_index = median_y / (max_y + eps)

    # 2. Lighting Ratio = Percentile_95(Y_sujet) / Percentile_10(Y_sujet)
    p95 = float(np.percentile(y_subject, 95))
    p10 = float(np.percentile(y_subject, 10))
    lighting_ratio = max(p95, eps) / max(p10, eps)

    # 3. Dynamic range estimé en stops (EV) = log2(P99 / P1)
    p99 = float(np.percentile(y_flat, 99))
    p1 = float(np.percentile(y_flat, 1))
    dynamic_range_stops = float(np.log2(max(p99, eps) / max(p1, eps)))

    # 4. Clipping
    shadow_clipping_pct = float(np.mean(y_flat <= (1.0 / 255.0)) * 100.0)
    highlight_clipping_pct = float(np.mean(y_flat >= (254.0 / 255.0)) * 100.0)

    # 5. Zone System Mapping (Ansel Adams 11 zones basées sur la clarté perceptive CIE L*)
    l_star = relative_luminance_to_cielab_l(y_flat)
    total_pixels = float(len(l_star))

    zone_bounds = [
        ("Zone 0", -np.inf, 5.0),
        ("Zone I", 5.0, 15.0),
        ("Zone II", 15.0, 25.0),
        ("Zone III", 25.0, 35.0),
        ("Zone IV", 35.0, 45.0),
        ("Zone V", 45.0, 55.0),
        ("Zone VI", 55.0, 65.0),
        ("Zone VII", 65.0, 75.0),
        ("Zone VIII", 75.0, 85.0),
        ("Zone IX", 85.0, 95.0),
        ("Zone X", 95.0, np.inf),
    ]

    zones_pct: dict[str, float] = {}
    for name, low, high in zone_bounds:
        count = np.count_nonzero((l_star >= low) & (l_star < high))
        zones_pct[name] = float((count / total_pixels) * 100.0)

    # Regroupements photographiques
    deep_shadows = zones_pct["Zone 0"] + zones_pct["Zone I"] + zones_pct["Zone II"]
    mid_tones = (
        zones_pct["Zone III"] + zones_pct["Zone IV"] + zones_pct["Zone V"]
        + zones_pct["Zone VI"] + zones_pct["Zone VII"]
    )
    specular_highlights = zones_pct["Zone VIII"] + zones_pct["Zone IX"] + zones_pct["Zone X"]

    zone_breakdown = ZoneSystemBreakdown(
        zones_percentage=zones_pct,
        deep_shadows_pct=round(deep_shadows, 2),
        mid_tones_pct=round(mid_tones, 2),
        specular_highlights_pct=round(specular_highlights, 2),
    )

    return PhotometricMetrics(
        key_index=round(key_index, 4),
        lighting_ratio=round(lighting_ratio, 2),
        median_luminance=round(median_y, 4),
        median_luminance_255=round(median_y * 255.0, 2),
        max_luminance=round(max_y, 4),
        min_luminance=round(min_y, 4),
        shadow_clipping_pct=round(shadow_clipping_pct, 2),
        highlight_clipping_pct=round(highlight_clipping_pct, 2),
        dynamic_range_stops=round(max(0.0, dynamic_range_stops), 2),
        zone_system=zone_breakdown,
        perceived_lightness_mean=round(float(np.mean(l_star)), 2),
    )
