"""Client d'interaction avec l'API ComfyUI (HTTP REST et WebSockets)."""

import io
import time
import urllib.parse
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from PIL import Image
import requests


class ComfyClient:
    """Client générique pour soumettre des workflows et récupérer les images produites par ComfyUI."""

    def __init__(
        self,
        server_address: str = "127.0.0.1:8188",
        client_id: Optional[str] = None
    ) -> None:
        cleaned_addr = server_address.strip()
        if cleaned_addr.startswith("http://"):
            cleaned_addr = cleaned_addr[7:]
        elif cleaned_addr.startswith("https://"):
            cleaned_addr = cleaned_addr[8:]
        cleaned_addr = cleaned_addr.rstrip("/")

        self.server_address = cleaned_addr
        self.client_id = client_id or str(uuid.uuid4())
        self.base_http_url = f"http://{cleaned_addr}"
        self.base_ws_url = f"ws://{cleaned_addr}/ws?clientId={self.client_id}"

    def check_connection(self, timeout: float = 3.0) -> bool:
        """Vérifie si le serveur ComfyUI est joignable."""
        try:
            response = requests.get(f"{self.base_http_url}/system_stats", timeout=timeout)
            return response.status_code == 200
        except Exception:
            return False

    def queue_prompt(self, workflow_prompt: Dict[str, Any]) -> Dict[str, Any]:
        """Soumet un workflow à la file d'attente ComfyUI."""
        url = f"{self.base_http_url}/prompt"
        payload = {
            "prompt": workflow_prompt,
            "client_id": self.client_id,
        }
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()

    def get_history(self, prompt_id: str) -> Dict[str, Any]:
        """Récupère l'historique et les outputs d'un prompt exécuté."""
        url = f"{self.base_http_url}/history/{prompt_id}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()

    def get_image(self, filename: str, subfolder: str = "", folder_type: str = "output") -> bytes:
        """Télécharge une image produite depuis le serveur ComfyUI."""
        params = {
            "filename": filename,
            "subfolder": subfolder,
            "type": folder_type,
        }
        url = f"{self.base_http_url}/view?{urllib.parse.urlencode(params)}"
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        return response.content

    def upload_image(
        self,
        image: Union[Image.Image, bytes, Path, str],
        filename: str = "input_image.png",
        subfolder: str = "",
        overwrite: bool = True
    ) -> Dict[str, Any]:
        """Envoie une image vers le répertoire d'entrée de ComfyUI (utile pour les nœuds de relighting)."""
        url = f"{self.base_http_url}/upload/image"

        if isinstance(image, (str, Path)):
            with open(image, "rb") as f:
                raw_bytes = f.read()
        elif isinstance(image, Image.Image):
            buf = io.BytesIO()
            image.save(buf, format="PNG")
            raw_bytes = buf.getvalue()
        elif isinstance(image, bytes):
            raw_bytes = image
        else:
            raise TypeError(f"Type d'image non supporté : {type(image)}")

        files = {"image": (filename, raw_bytes, "image/png")}
        data = {
            "overwrite": "true" if overwrite else "false",
            "subfolder": subfolder,
        }

        response = requests.post(url, files=files, data=data, timeout=60)
        response.raise_for_status()
        return response.json()

    def wait_for_prompt(
        self,
        prompt_id: str,
        timeout: int = 300,
        poll_interval: float = 1.0,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """Attend la fin de l'exécution d'un prompt ComfyUI par polling d'historique."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            history = self.get_history(prompt_id)
            if prompt_id in history:
                prompt_data = history[prompt_id]
                status = prompt_data.get("status", {})
                if status.get("completed", False) or "outputs" in prompt_data:
                    return prompt_data
            if progress_callback:
                progress_callback(f"Génération en cours... ({int(time.time() - start_time)}s)")
            time.sleep(poll_interval)
        raise TimeoutError(f"Le prompt ComfyUI {prompt_id} a dépassé le délai maximal de {timeout}s.")

    def extract_images_from_history(self, history_data: Dict[str, Any]) -> List[Image.Image]:
        """Extrait et télécharge toutes les images d'un historique ComfyUI en objets PIL Image."""
        images: List[Image.Image] = []
        outputs = history_data.get("outputs", {})
        for _, node_output in outputs.items():
            if "images" in node_output:
                for img_info in node_output["images"]:
                    filename = img_info.get("filename")
                    subfolder = img_info.get("subfolder", "")
                    folder_type = img_info.get("type", "output")
                    if filename:
                        raw_bytes = self.get_image(filename, subfolder, folder_type)
                        image = Image.open(io.BytesIO(raw_bytes))
                        images.append(image)
        return images
