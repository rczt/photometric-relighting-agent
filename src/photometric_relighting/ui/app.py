"""Interface Gradio pour le Studio de Relighting Photométrique Neuro-Symbolique."""

import time
from typing import Optional, Tuple
import gradio as gr
import numpy as np
from PIL import Image, ImageDraw

from photometric_relighting.agent.loop import PhotometricFeedbackLoop
from photometric_relighting.agent.models import PhotometricTarget
from photometric_relighting.cdl.models import CDLParameters
from photometric_relighting.cdl.operator import apply_cdl
from photometric_relighting.comfy.client import ComfyClient
from photometric_relighting.metrics.extractor import extract_photometric_metrics
from photometric_relighting.ui.zone_viewer import (
    render_metrics_card_html,
    render_zone_system_html,
)


def create_demo_scene() -> Image.Image:
    """Crée une scène synthétique de démonstration (portrait studio avec dégradé doux)."""
    w, h = 512, 512
    img = Image.new("RGB", (w, h), color=(140, 140, 145))
    draw = ImageDraw.Draw(img)

    # Dégradé de fond
    for y in range(h):
        shade = int(120 + 50 * np.cos(y / h * np.pi))
        draw.line([(0, y), (w, y)], fill=(shade, shade, int(shade * 1.05)))

    # Silhouette sujet (visage / buste)
    draw.ellipse([160, 100, 352, 340], fill=(185, 160, 145), outline=(130, 110, 95), width=2)
    # Highlight clé (key light douce)
    draw.ellipse([210, 130, 290, 230], fill=(220, 205, 195))
    # Ombre côté opposé (fill light)
    draw.ellipse([180, 250, 332, 480], fill=(100, 95, 105))

    return img


def check_comfy_status(server_address: str) -> str:
    """Vérifie si ComfyUI est en ligne."""
    client = ComfyClient(server_address=server_address)
    if client.check_connection():
        return f"🟢 Connecté à ComfyUI ({server_address})"
    return f"🔴 ComfyUI hors-ligne ({server_address})"


def run_agentic_relighting(
    input_image: Optional[Image.Image],
    preset_choice: str,
    custom_key: float,
    custom_ratio: float,
    custom_sat: float,
    max_iters: int,
    progress=gr.Progress(track_tqdm=True),
) -> Tuple[Optional[Image.Image], str, str, str, str]:
    """Exécute la boucle fermée neuro-symbolique."""
    if input_image is None:
        input_image = create_demo_scene()

    progress(0.1, desc="Initialisation de la cible photométrique...")

    if preset_choice == "Personnalisé (Custom)":
        target = PhotometricTarget(
            name="Profil Personnalisé",
            description="Cible définie manuellement par l'utilisateur.",
            target_key_index=float(custom_key),
            target_lighting_ratio=float(custom_ratio),
            target_saturation=float(custom_sat),
        )
    else:
        preset_map = {
            "Low-Key Dramatique (8:1)": "low_key_dramatic",
            "Film Noir / Chiaroscuro (12:1)": "film_noir",
            "High-Key Lumineux / Beauté (2.5:1)": "high_key_fashion",
            "Cinématique Équilibré (4:1)": "balanced_cinematic",
        }
        target = PhotometricTarget.get_preset(preset_map.get(preset_choice, "low_key_dramatic"))

    progress(0.3, desc="Lancement de la boucle fermée de rétroaction...")
    loop = PhotometricFeedbackLoop()
    final_img, result = loop.run(input_image, target=target, max_iterations=int(max_iters))
    progress(0.9, desc="Finalisation de la télémétrie...")

    # Rendu des composants visuels
    initial_card = render_metrics_card_html(result.initial_metrics, title="Télémétrie Initiale")
    final_card = render_metrics_card_html(result.final_metrics, title="Télémétrie Finale (Étalonnée)")
    zone_html = render_zone_system_html(result.final_metrics)

    # Trace du raisonnement itératif
    trace_lines = [f"### 🤖 Trace de la Boucle Agentique ({result.iterations_count} passes) :"]
    for s in result.steps:
        status_icon = "🎯" if s.converged else "🔄"
        trace_lines.append(f"\n**Passe {s.iteration + 1}** {status_icon} :")
        trace_lines.append(f"- **Raisonnement :** {s.reasoning}")
        trace_lines.append(
            f"- **Action CDL :** `Slope={s.cdl_params.slope[0]:.2f}, Offset={s.cdl_params.offset[0]:.3f}, "
            f"Power={s.cdl_params.power[0]:.2f}, Sat={s.cdl_params.saturation:.2f}`"
        )
        trace_lines.append(
            f"- **Métriques :** Key Index={s.metrics.key_index:.3f}, Ratio={s.metrics.lighting_ratio:.1f}:1, "
            f"Clipping Ombres={s.metrics.shadow_clipping_pct:.1f}%"
        )

    trace_md = "\n".join(trace_lines)
    return final_img, initial_card, final_card, zone_html, trace_md


def run_manual_cdl(
    image: Optional[Image.Image],
    slope: float,
    offset: float,
    power: float,
    sat: float,
) -> Tuple[Optional[Image.Image], str, str]:
    """Applique en temps réel les réglages manuels ASC CDL."""
    if image is None:
        image = create_demo_scene()

    params = CDLParameters(
        slope=(slope, slope, slope),
        offset=(offset, offset, offset),
        power=(power, power, power),
        saturation=sat,
    )
    graded = apply_cdl(image, params)
    metrics = extract_photometric_metrics(graded)

    metrics_card = render_metrics_card_html(metrics, title="Métriques en direct")
    zone_html = render_zone_system_html(metrics)
    return graded, metrics_card, zone_html


def build_studio_app() -> gr.Blocks:
    """Construit l'interface du Photometric Relighting Studio."""
    with gr.Blocks(title="Neuro-Symbolic Photometric Relighting Studio") as demo:
        gr.Markdown("# 🎬 Neuro-Symbolic Photometric Relighting Studio")
        gr.Markdown(
            "Contrôle photométrique agentique en boucle fermée : découplage du transport lumineux "
            "et application d'opérateurs formels ASC CDL guidés par métriques objectives (Zone System, Key Index, Lighting Ratio)."
        )

        with gr.Row():
            server_addr = gr.Textbox(label="Serveur ComfyUI (Local)", value="127.0.0.1:8188", scale=3)
            check_btn = gr.Button("🔌 Vérifier la connexion", scale=1)
            conn_status = gr.Markdown("⚪ Statut : Non testé", scale=2)

        check_btn.click(fn=check_comfy_status, inputs=[server_addr], outputs=[conn_status])

        with gr.Tabs():
            with gr.TabItem("🤖 Mode 1 : Boucle Fermée Agentique (ReAct)"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 1. Image Source / Plaque Rééclairée")
                        input_image = gr.Image(label="Image d'entrée (Neutre ou IC-Light)", type="pil")
                        demo_btn = gr.Button("🖼️ Charger une scène de démonstration")
                        demo_btn.click(fn=create_demo_scene, outputs=[input_image])

                        gr.Markdown("### 2. Intention Photométrique & Cible")
                        preset_dropdown = gr.Dropdown(
                            label="Preset Artistique",
                            choices=[
                                "Low-Key Dramatique (8:1)",
                                "Film Noir / Chiaroscuro (12:1)",
                                "High-Key Lumineux / Beauté (2.5:1)",
                                "Cinématique Équilibré (4:1)",
                                "Personnalisé (Custom)",
                            ],
                            value="Low-Key Dramatique (8:1)",
                        )

                        with gr.Group():
                            custom_key = gr.Slider(
                                label="Key Index Cible", minimum=0.05, maximum=0.70, step=0.01, value=0.16
                            )
                            custom_ratio = gr.Slider(
                                label="Lighting Ratio Cible (P95/P10)",
                                minimum=1.5,
                                maximum=20.0,
                                step=0.5,
                                value=8.0,
                            )
                            custom_sat = gr.Slider(
                                label="Saturation Cible", minimum=0.0, maximum=1.5, step=0.05, value=0.9
                            )

                        max_iters_slider = gr.Slider(
                            label="Nombre max d'itérations", minimum=1, maximum=6, step=1, value=4
                        )

                        launch_agent_btn = gr.Button("🚀 Lancer la Boucle Agentique", variant="primary", size="lg")

                    with gr.Column(scale=1):
                        gr.Markdown("### 3. Rendu Final Étalonné (ASC CDL)")
                        final_image_output = gr.Image(label="Rendu Final Optimisé", type="pil", interactive=False)

                        with gr.Row():
                            initial_card_output = gr.HTML()
                            final_card_output = gr.HTML()

                        zone_html_output = gr.HTML()
                        trace_output = gr.Markdown()

                launch_agent_btn.click(
                    fn=run_agentic_relighting,
                    inputs=[
                        input_image,
                        preset_dropdown,
                        custom_key,
                        custom_ratio,
                        custom_sat,
                        max_iters_slider,
                    ],
                    outputs=[
                        final_image_output,
                        initial_card_output,
                        final_card_output,
                        zone_html_output,
                        trace_output,
                    ],
                )

            with gr.TabItem("🎛️ Mode 2 : Étalonnage Manuel ASC CDL"):
                with gr.Row():
                    with gr.Column(scale=1):
                        manual_input_image = gr.Image(label="Image Source", type="pil")
                        manual_demo_btn = gr.Button("🖼️ Charger la scène démo")
                        manual_demo_btn.click(fn=create_demo_scene, outputs=[manual_input_image])

                        gr.Markdown("### 🎚️ Paramètres ASC CDL Déterministes")
                        slope_slider = gr.Slider(
                            label="Slope (Gain / Hautes Lumières)", minimum=0.2, maximum=3.0, step=0.05, value=1.0
                        )
                        offset_slider = gr.Slider(
                            label="Offset (Piédestal / Ombres)", minimum=-0.25, maximum=0.25, step=0.01, value=0.0
                        )
                        power_slider = gr.Slider(
                            label="Power (Gamma / Tons Moyens)", minimum=0.3, maximum=3.0, step=0.05, value=1.0
                        )
                        sat_slider = gr.Slider(
                            label="Saturation", minimum=0.0, maximum=2.0, step=0.05, value=1.0
                        )

                        apply_manual_btn = gr.Button("⚡ Appliquer la transformation CDL", variant="secondary")

                    with gr.Column(scale=1):
                        manual_output_image = gr.Image(label="Image Résultat", type="pil", interactive=False)
                        manual_metrics_card = gr.HTML()
                        manual_zone_html = gr.HTML()

                apply_manual_btn.click(
                    fn=run_manual_cdl,
                    inputs=[manual_input_image, slope_slider, offset_slider, power_slider, sat_slider],
                    outputs=[manual_output_image, manual_metrics_card, manual_zone_html],
                )

    return demo


def main():
    demo = build_studio_app()
    demo.launch(server_name="127.0.0.1", server_port=7860, theme=gr.themes.Soft())


if __name__ == "__main__":
    main()
