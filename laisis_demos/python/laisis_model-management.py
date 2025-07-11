import subprocess
import os
import signal
import sys
import threading
import time
import json

OLLAMA_PID_FILE = ".ollama.pid"
ACTIVE_MODEL_FILE = ".laisis_active_model"

MODEL_NAME = None
if os.path.exists(ACTIVE_MODEL_FILE):
    with open(ACTIVE_MODEL_FILE, "r") as f:
        MODEL_NAME = f.read().strip()

# Progress spinner for downloads
def spinner(stop_event):
    spin = ['|', '/', '-', '\\']
    i = 0
    while not stop_event.is_set():
        print(f"\r[INFO] Downloading... {spin[i % len(spin)]}", end="")
        i += 1
        time.sleep(0.2)
    print("\r[✓] Download complete.         ")

# Start Ollama server
def start_ollama():
    result = subprocess.run(["lsof", "-i", ":11434"], capture_output=True, text=True)
    if result.stdout.strip():
        print("[INFO] Ollama server is already running.")
        return

    print("[INFO] Starting Ollama server...")
    process = subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    with open(OLLAMA_PID_FILE, "w") as f:
        f.write(str(process.pid))
    print(f"[✓] Ollama server started (PID: {process.pid})")

# Stop Ollama server
def stop_ollama():
    if os.path.exists(OLLAMA_PID_FILE):
        with open(OLLAMA_PID_FILE, "r") as f:
            pid = int(f.read())
        try:
            os.kill(pid, signal.SIGTERM)
            print("[✓] Ollama server stopped.")
            os.remove(OLLAMA_PID_FILE)
        except Exception as e:
            print(f"[✗] Error stopping Ollama: {e}")
    else:
        print("[INFO] No Ollama server PID found.")

# Download model
def download_model(model_name):
    global MODEL_NAME
    print(f"[INFO] Downloading model '{model_name}'...")

    process = subprocess.Popen(["ollama", "pull", model_name])
    process.wait()

    if process.returncode == 0:
        with open(ACTIVE_MODEL_FILE, "w") as f:
            f.write(model_name.strip())
        MODEL_NAME = model_name.strip()
        print(f"[✓] Model '{model_name}' installed and set as active.")
    else:
        print(f"[✗] Failed to download model.")

# Delete model
def delete_model():
    global MODEL_NAME
    if not os.path.exists(ACTIVE_MODEL_FILE):
        print("[ERROR] No active model to delete.")
        return
    with open(ACTIVE_MODEL_FILE, "r") as f:
        model_name = f.read().strip()
    process = subprocess.run(["ollama", "rm", model_name], capture_output=True, text=True)
    if process.returncode == 0:
        os.remove(ACTIVE_MODEL_FILE)
        MODEL_NAME = None
        print(f"[✓] Model '{model_name}' removed.")
    else:
        print(f"[✗] Failed to remove model:\n{process.stderr}")

# Start model and check readiness
def start_model(port=11434):
    if not MODEL_NAME:
        print("[ERROR] No model selected.")
        return
    model_name = MODEL_NAME
    print(f"[INFO] Starting model '{model_name}' on port {port}...")

    try:
        process = subprocess.Popen(
            ["curl", "-s", "-X", "POST", f"http://localhost:{port}/api/generate",
             "-d", f'{{"model": "{model_name}", "prompt": "Say READY"}}'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        full_response = ""
        for line in process.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                full_response += data.get("response", "")
                if data.get("done", False):
                    break
            except json.JSONDecodeError:
                print("[✗] Invalid line (not JSON):", line)

        print("[✓] Model response:", full_response.strip())

    except Exception as e:
        print(f"[✗] Failed to start model: {e}")


def stop_model():
    print("[INFO] To stop the model, stopping Ollama server...")
    stop_ollama()

# Chat with the model
def chat_with_model():
    if not MODEL_NAME:
        print("[ERROR] No model selected.")
        return
    model_name = MODEL_NAME
    print(f"[INFO] Starting chat with model '{model_name}'. Type 'exit' to stop.")
    while True:
        user_input = input("You: ")
        if user_input.strip().lower() == "exit":
            print("[INFO] Exiting chat.")
            break
        try:
            process = subprocess.Popen(
                ["curl", "-s", "-X", "POST", "http://localhost:11434/api/generate",
                 "-d", f'{{"model": "{model_name}", "prompt": "{user_input}"}}'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            full_response = ""
            for line in process.stdout:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    full_response += data.get("response", "")
                    if data.get("done", False):
                        break
                except json.JSONDecodeError:
                    # fallback: print raw line if JSON fails
                    print("[?] Raw:", line)
            
            process.wait()
            print("AI:", full_response.strip())

        except Exception as e:
            print(f"[✗] Failed to communicate with model: {e}")

# Main command loop
def main():
    print("LAISIS - Local AI Software Integration System")
    print("Commands: install ollama, start ollama, stop ollama")
    print("          download model <name>, delete model")
    print("          start model <port>, stop model, chat model, exit")

    while True:
        cmd = input(">> ").strip().lower()

        if cmd == "install ollama":
            print("[INFO] Please install Ollama manually from https://ollama.com/download")

        elif cmd == "start ollama":
            start_ollama()

        elif cmd == "stop ollama":
            stop_ollama()

        elif cmd.startswith("download model"):
            parts = cmd.split()
            if len(parts) >= 3:
                model_name = parts[2]
                download_model(model_name)
            else:
                print("[ERROR] Usage: download model <name>")

        elif cmd == "delete model":
            delete_model()

        elif cmd.startswith("start model"):
            parts = cmd.split()
            if len(parts) == 3 and parts[2].isdigit():
                port = int(parts[2])
                start_model(port)
            else:
                print("[ERROR] Usage: start model <port>")

        elif cmd == "stop model":
            stop_model()

        elif cmd == "chat model":
            chat_with_model()

        elif cmd == "exit":
            print("Exiting LAISIS.")
            break

        else:
            print("[ERROR] Unknown command.")

        

if __name__ == "__main__":
    main()