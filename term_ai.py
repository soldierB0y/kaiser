#!/usr/bin/env python3
import sys
import json
import requests
import argparse
import os
import time
import threading
from itertools import cycle

# Configuración por defecto
CONFIG_PATH = os.path.expanduser("~/.term_ai_config.json")
DEFAULT_CONFIG = {
    "OLLAMA_URL": "http://localhost:11434/api/generate",
    "DEFAULT_MODEL": "qwen2.5-coder:7b",
    "TIMEOUT": 30,
    "MAX_OUTPUT_CHARS": 2000,
    "EXCLUDED_COMMANDS": [
        "top", "htop", "nano", "vim", "vi", "less", "more", "man", 
        "cat", "ssh", "watch", "tail", "journalctl"
    ],
    "KNOWLEDGE_BASE": os.path.expanduser("~/Data/projects/Info/linuxCommands.txt")
}

# Códigos de escape ANSI para colores
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
ITALIC = "\033[3m"
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[96m"

class LoadingSpinner:
    """Displays an animated loading spinner while waiting for AI responses."""
    def __init__(self, message="Thinking", delay=0.1):
        self.message = message
        self.delay = delay
        self.running = False
        self.thread = None
        # Spinners: dots, line, arrow, dots2, moon, circle
        self.spinners = {
            "dots": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
            "line": ["-", "\\", "|", "/"],
            "arrow": ["←", "↖", "↑", "↗", "→", "↘", "↓", "↙"],
            "dots2": ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"],
            "moon": ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"],
            "dots3": ["⠋", "⠙", "⠚", "⠞", "⠖", "⠦", "⠴", "⠲", "⠳", "⠓"],
        }
        self.current_spinner = self.spinners["dots"]
    
    def start(self):
        """Start the loading spinner animation."""
        self.running = True
        self.thread = threading.Thread(target=self._animate, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the loading spinner animation."""
        self.running = False
        if self.thread:
            self.thread.join()
        # Clear the line
        sys.stdout.write("\r" + " " * (len(self.message) + 15) + "\r")
        sys.stdout.flush()
    
    def _animate(self):
        """Animation loop."""
        spinner_cycle = cycle(self.current_spinner)
        while self.running:
            frame = next(spinner_cycle)
            sys.stdout.write(f"\r{CYAN}{frame} {self.message}...{RESET}")
            sys.stdout.flush()
            time.sleep(self.delay)

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        except (json.JSONDecodeError, IOError):
            return DEFAULT_CONFIG
    return DEFAULT_CONFIG

def save_config(config):
    try:
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=4)
        print(f"{GREEN}✅ Configuración guardada en {CONFIG_PATH}{RESET}")
    except Exception as e:
        print(f"{BOLD}❌ Error al guardar configuración: {e}{RESET}")

def interactive_config():
    config = load_config()
    print(f"\n{BLUE}{BOLD}⚙️ Configuración Interactiva de Term-AI{RESET}")
    print("Presiona Enter para mantener el valor actual.\n")
    
    for key, value in config.items():
        if key == "EXCLUDED_COMMANDS":
            current = ", ".join(value)
            new_val = input(f"{BOLD}{key}{RESET} [{current}]: ").strip()
            if new_val:
                config[key] = [cmd.strip() for cmd in new_val.split(",")]
        else:
            new_val = input(f"{BOLD}{key}{RESET} [{value}]: ").strip()
            if new_val:
                # Intentar convertir a int si el original era int
                if isinstance(value, int):
                    try:
                        config[key] = int(new_val)
                    except ValueError:
                        print(f"Valor inválido para {key}, se mantiene el anterior.")
                else:
                    config[key] = new_val
    
    save_config(config)

def get_local_context(command, knowledge_base):
    """Busca el comando en el archivo de manual para obtener contexto adicional."""
    if not os.path.exists(knowledge_base):
        return ""
    
    base_cmd = command.split()[0] if command else ""
    try:
        search_pattern = f"$ {base_cmd}"
        with open(knowledge_base, 'r', encoding='latin-1') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if search_pattern in line:
                    start = max(0, i - 10)
                    end = min(len(lines), i + 5)
                    return "".join(lines[start:end])
        return ""
    except (IOError, UnicodeDecodeError):
        return ""

def ask_ai(prompt, system_prompt, config):
    payload = {
        "model": config["DEFAULT_MODEL"],
        "prompt": prompt,
        "system": system_prompt,
        "stream": False
    }
    
    # Start loading spinner
    spinner = LoadingSpinner(message=f"{BLUE}Analyzing with {config['DEFAULT_MODEL']}")
    spinner.start()
    
    try:
        response = requests.post(config["OLLAMA_URL"], json=payload, timeout=config["TIMEOUT"])
        response.raise_for_status()
        result = response.json()
        spinner.stop()
        return result.get("response", "No se pudo obtener una respuesta de la IA.")
    except requests.exceptions.RequestException as e:
        spinner.stop()
        return f"Error al conectar con Ollama: {e}"

def main():
    parser = argparse.ArgumentParser(description="Analizador de comandos Linux mediante Ollama.")
    parser.add_argument("command", nargs='?', help="El comando o pregunta para la IA.")
    parser.add_argument("--config", action="store_true", help="Abrir configuración interactiva.")
    parser.add_argument("--chat", action="store_true", help="Hablar directamente con la IA.")
    args = parser.parse_args()
    
    config = load_config()

    if args.config:
        interactive_config()
        return

    if not args.command:
        parser.print_help()
        return

    if args.chat:
        print(f"\n{BLUE}{BOLD}💬 Chat Directo con IA:{RESET}")
        system_prompt = "Eres un asistente técnico experto en terminales Linux. Responde de forma clara y útil."
        explanation = ask_ai(args.command, system_prompt, config)
        print(f"{ITALIC}{explanation}{RESET}\n")
        return

    # Modo análisis de comando (por defecto)
    base_command = args.command.split()[0] if args.command else ""
    if base_command in config["EXCLUDED_COMMANDS"]:
        return

    # Leer el output desde STDIN
    output = sys.stdin.read(config["MAX_OUTPUT_CHARS"])
    
    local_context = get_local_context(args.command, config["KNOWLEDGE_BASE"])
    
    system_prompt = (
        "Eres un asistente técnico experto en terminales Linux. "
        "Analiza el comando y su salida. Si hay un error, explica por qué ocurrió y cómo solucionarlo. "
        "Si el comando tuvo éxito, resume brevemente qué hizo. "
        "Sé muy conciso (máximo 3-4 líneas). Usa un tono técnico pero directo."
    )
    
    prompt = f"Comando ejecutado: {args.command}\n"
    if local_context:
        prompt += f"\nContexto del Manual:\n{local_context}\n"
    prompt += f"\nSalida del sistema:\n{output}"

    explanation = ask_ai(prompt, system_prompt, config)
    
    print(f"\n{BLUE}{BOLD}🤖 IA Feedback:{RESET}")
    print(f"{ITALIC}{explanation}{RESET}\n")

if __name__ == "__main__":
    main()
