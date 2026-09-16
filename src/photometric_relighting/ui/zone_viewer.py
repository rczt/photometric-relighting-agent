"""Générateur de rendu HTML pour le Zone System d'Ansel Adams et la télémétrie."""

from photometric_relighting.metrics.models import PhotometricMetrics


def render_zone_system_html(metrics: PhotometricMetrics) -> str:
    """Génère un composant HTML stylisé pour afficher la répartition des 11 zones Ansel Adams."""
    breakdown = metrics.zone_system
    zones = breakdown.zones_percentage

    # Définition des couleurs de dégradé par zone (du noir au blanc)
    zone_colors = {
        "Zone 0": "#0a0a0a",
        "Zone I": "#1a1a1a",
        "Zone II": "#2c2c2c",
        "Zone III": "#424242",
        "Zone IV": "#5a5a5a",
        "Zone V": "#757575",
        "Zone VI": "#949494",
        "Zone VII": "#b5b5b5",
        "Zone VIII": "#d6d6d6",
        "Zone IX": "#f0f0f0",
        "Zone X": "#ffffff",
    }

    zone_labels = {
        "Zone 0": "0 - Noir pur / Écrêtage",
        "Zone I": "I - Noir profond",
        "Zone II": "II - Premiers détails ombres",
        "Zone III": "III - Ombres texturées",
        "Zone IV": "IV - Tons moyens sombres / Peau sombre",
        "Zone V": "V - Gris neutre 18% (Pivot Ansel Adams)",
        "Zone VI": "VI - Peau claire moyenne",
        "Zone VII": "VII - Peau très claire",
        "Zone VIII": "VIII - Blanc texturé avec détails",
        "Zone IX": "IX - Blanc éclatant sans texture",
        "Zone X": "X - Blanc pur spéculaire / Sources",
    }

    rows_html = []
    for z_name, pct in zones.items():
        color = zone_colors.get(z_name, "#757575")
        text_color = "#ffffff" if z_name in ["Zone 0", "Zone I", "Zone II", "Zone III", "Zone IV"] else "#111111"
        label = zone_labels.get(z_name, z_name)
        bar_width = max(1.0, min(100.0, pct * 2.5))  # Accentuation pour lisibilité

        rows_html.append(f"""
        <div style="display: flex; align-items: center; margin-bottom: 4px; font-family: monospace; font-size: 11px;">
            <div style="width: 210px; color: #ccc;">{label}</div>
            <div style="flex-grow: 1; background: #222; border-radius: 3px; height: 16px; margin: 0 10px; overflow: hidden; border: 1px solid #333;">
                <div style="width: {bar_width}%; background: {color}; height: 100%; border-radius: 2px;"></div>
            </div>
            <div style="width: 45px; text-align: right; font-weight: bold; color: #fff;">{pct:.1f}%</div>
        </div>
        """)

    content = "".join(rows_html)

    summary_html = f"""
    <div style="background: #18191c; border: 1px solid #30333a; border-radius: 8px; padding: 14px; margin-top: 10px;">
        <h4 style="margin: 0 0 10px 0; color: #eee; font-family: sans-serif;">📊 Cartographie Zone System (Ansel Adams)</h4>
        {content}
        <div style="display: flex; justify-content: space-around; margin-top: 12px; padding-top: 8px; border-top: 1px solid #2d3039; font-family: sans-serif; font-size: 12px;">
            <span style="color: #64b5f6;">🌑 Ombres profondes (0-II) : <b>{breakdown.deep_shadows_pct:.1f}%</b></span>
            <span style="color: #81c784;">🌓 Tons moyens (III-VII) : <b>{breakdown.mid_tones_pct:.1f}%</b></span>
            <span style="color: #ffb74d;">🌕 Hautes lumières (VIII-X) : <b>{breakdown.specular_highlights_pct:.1f}%</b></span>
        </div>
    </div>
    """
    return summary_html


def render_metrics_card_html(metrics: PhotometricMetrics, title: str = "Télémétrie Photométrique") -> str:
    """Génère un badge récapitulatif pour les métriques clés."""
    key_color = "#81c784" if metrics.key_index < 0.25 else ("#ffb74d" if metrics.key_index < 0.45 else "#e57373")

    return f"""
    <div style="background: #18191c; border: 1px solid #30333a; border-radius: 8px; padding: 12px; font-family: sans-serif;">
        <h4 style="margin: 0 0 8px 0; color: #eee;">⚡ {title}</h4>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 13px;">
            <div style="background: #23252b; padding: 8px; border-radius: 6px;">
                <div style="color: #888; font-size: 11px;">Key Index (Médiane / Max)</div>
                <div style="font-size: 16px; font-weight: bold; color: {key_color};">{metrics.key_index:.3f}</div>
            </div>
            <div style="background: #23252b; padding: 8px; border-radius: 6px;">
                <div style="color: #888; font-size: 11px;">Lighting Ratio (P95 / P10)</div>
                <div style="font-size: 16px; font-weight: bold; color: #64b5f6;">{metrics.lighting_ratio:.1f} : 1</div>
            </div>
            <div style="background: #23252b; padding: 8px; border-radius: 6px;">
                <div style="color: #888; font-size: 11px;">Médiane (0-255)</div>
                <div style="font-size: 15px; font-weight: bold; color: #eee;">{metrics.median_luminance_255:.1f}</div>
            </div>
            <div style="background: #23252b; padding: 8px; border-radius: 6px;">
                <div style="color: #888; font-size: 11px;">Plage Dynamique (EV)</div>
                <div style="font-size: 15px; font-weight: bold; color: #eee;">{metrics.dynamic_range_stops:.1f} stops</div>
            </div>
            <div style="background: #23252b; padding: 8px; border-radius: 6px;">
                <div style="color: #888; font-size: 11px;">Écrêtage Noirs (Zone 0)</div>
                <div style="font-size: 14px; font-weight: bold; color: {'#e57373' if metrics.shadow_clipping_pct > 2.0 else '#81c784'};">
                    {metrics.shadow_clipping_pct:.2f}%
                </div>
            </div>
            <div style="background: #23252b; padding: 8px; border-radius: 6px;">
                <div style="color: #888; font-size: 11px;">Écrêtage Blancs (Zone X)</div>
                <div style="font-size: 14px; font-weight: bold; color: {'#e57373' if metrics.highlight_clipping_pct > 2.0 else '#81c784'};">
                    {metrics.highlight_clipping_pct:.2f}%
                </div>
            </div>
        </div>
    </div>
    """
