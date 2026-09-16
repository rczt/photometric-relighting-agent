"""Opérateur vectorisé pour l'application des transformations ASC CDL."""

from typing import Union
import numpy as np
from PIL import Image

from photometric_relighting.cdl.models import CDLParameters

# Poids de luminance standard Rec.709
REC709_WEIGHTS = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


def apply_cdl(
    image: Union[np.ndarray, Image.Image],
    params: CDLParameters,
    clamp_output: bool = True
) -> Union[np.ndarray, Image.Image]:
    """Applique la transformation ASC CDL vectorisée sur une image RVB.

    Formule mathématique :
        1. V = clamp(Entrée * Slope + Offset, 0, inf)
        2. V = V ** Power
        3. Y = 0.2126*R + 0.7152*G + 0.0722*B
        4. Sortie = Y + Saturation * (V - Y)

    Args:
        image: Image d'entrée sous forme de np.ndarray (uint8 [0, 255] ou float32 [0.0, 1.0])
               ou sous forme d'objet PIL.Image.
        params: Instance de CDLParameters spécifiant Slope, Offset, Power et Saturation.
        clamp_output: Si True, force les valeurs de sortie dans l'intervalle [0.0, 1.0].

    Returns:
        L'image traitée dans le même type que l'entrée (PIL.Image ou np.ndarray).
    """
    is_pil = isinstance(image, Image.Image)
    if is_pil:
        img_np = np.asarray(image.convert("RGB"), dtype=np.float32) / 255.0
    elif isinstance(image, np.ndarray):
        if np.issubdtype(image.dtype, np.integer):
            img_np = image.astype(np.float32) / 255.0
        else:
            img_np = image.astype(np.float32).copy()
    else:
        raise TypeError(f"Format d'image non supporté : {type(image)}")

    if img_np.ndim != 3 or img_np.shape[2] < 3:
        raise ValueError("L'image doit être au format RVB à 3 canaux.")

    # Ne traiter que les canaux RVB (ignorer le canal alpha si présent)
    rgb = img_np[:, :, :3]

    slope = np.array(params.slope, dtype=np.float32).reshape(1, 1, 3)
    offset = np.array(params.offset, dtype=np.float32).reshape(1, 1, 3)
    power = np.array(params.power, dtype=np.float32).reshape(1, 1, 3)
    sat = float(params.saturation)

    # 1. Slope & Offset avec clamp inférieur à 0
    val = np.maximum(rgb * slope + offset, 0.0)

    # 2. Power
    # Éviter 0^0 ou instabilité numérique
    val = np.power(val, power)

    # 3. Saturation basée sur la luminance Rec.709
    luma = np.sum(val * REC709_WEIGHTS, axis=2, keepdims=True)
    val = luma + sat * (val - luma)

    # 4. Clamping final
    if clamp_output:
        val = np.clip(val, 0.0, 1.0)

    if img_np.shape[2] > 3:
        # Réinjecter canal alpha si existant
        output = np.dstack([val, img_np[:, :, 3:]])
    else:
        output = val

    if is_pil:
        out_uint8 = np.round(output * 255.0).astype(np.uint8)
        return Image.fromarray(out_uint8, mode="RGB")
    elif isinstance(image, np.ndarray) and np.issubdtype(image.dtype, np.integer):
        return np.round(output * 255.0).astype(image.dtype)
    return output
