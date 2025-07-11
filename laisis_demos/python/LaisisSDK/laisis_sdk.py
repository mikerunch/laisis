import requests
import json
import os

class LAISIS:
    def __init__(self, port=11434):
        self.port = port
        self.model = self._load_active_model()

    def _load_active_model(self) -> str:
        model_file = ".laisis_active_model"
        if os.path.exists(model_file):
            with open(model_file, "r") as f:
                model_name = f.read().strip()
                if model_name:
                    return model_name
        print("[WARN] No active model found. Default 'mistral' will be used.")
        return "mistral"

    def send_message(self, message: str) -> str:
        url = f"http://localhost:{self.port}/api/generate"
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "prompt": message,
            "stream": True
        }

        try:
            response = requests.post(url, json=payload, headers=headers, stream=True)
            full_response = ""
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    full_response += data.get("response", "")
                    if data.get("done", False):
                        break
                except json.JSONDecodeError:
                    print("[✗] Invalid JSON line:", line)
            return full_response.strip()

        except Exception as e:
            print(f"[✗] Error sending to Lokey: {e}")
            return "[ERROR]"