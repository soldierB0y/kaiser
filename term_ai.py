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
HISTORY_PATH = os.path.expanduser("~/.term_ai_history.json")

DEFAULT_CONFIG = {
    "OLLAMA_URL": "http://localhost:11434/api/chat",
    "DEFAULT_MODEL": "qwen2.5-coder:7b",
    "TIMEOUT": 30,
    "MAX_OUTPUT_CHARS": 2000,
    "MAX_HISTORY": 5,  # Número de interacciones previas a recordar
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
        self.spinners = {
            "dots": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        }
        self.current_spinner = self.spinners["dots"]
    
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._animate, daemon=True)
        self.thread.start()
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        sys.stdout.write("\r" + " " * (len(self.message) + 15) + "\r")
        sys.stdout.flush()
    
    def _animate(self):
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
        except:
            return DEFAULT_CONFIG
    return DEFAULT_CONFIG

def save_config(config):
    try:
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=4)
        print(f"{GREEN}✅ Configuración guardada en {CONFIG_PATH}{RESET}")
    except Exception as e:
        print(f"{BOLD}❌ Error al guardar configuración: {e}{RESET}")

def load_history():
    if os.path.exists(HISTORY_PATH):
        try:
            with open(HISTORY_PATH, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(history, max_len):
    try:
        # Mantener solo las últimas N interacciones (2 mensajes por interacción: user y assistant)
        keep_last = max_len * 2
        history = history[-keep_last:]
        with open(HISTORY_PATH, 'w') as f:
            json.dump(history, f, indent=4)
    except Exception:
        pass

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
                if isinstance(value, int):
                    try:
                        config[key] = int(new_val)
                    except ValueError:
                        print(f"Valor inválido para {key}, se mantiene el anterior.")
                else:
                    config[key] = new_val
    
    save_config(config)

def get_local_context(command, knowledge_base):
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
    except:
        return ""

def ask_ai(messages, config):
    payload = {
        "model": config["DEFAULT_MODEL"],
        "messages": messages,
        "stream": False
    }
    
    spinner = LoadingSpinner(message=f"{BLUE}Analyzing with {config['DEFAULT_MODEL']}")
    spinner.start()
    
    try:
        response = requests.post(config["OLLAMA_URL"], json=payload, timeout=config["TIMEOUT"])
        response.raise_for_status()
        result = response.json()
        spinner.stop()
        return result.get("message", {}).get("content", "No se pudo obtener una respuesta de la IA.")
    except requests.exceptions.RequestException as e:
        spinner.stop()
        return f"Error al conectar con Ollama: {e}"

def main():
    parser = argparse.ArgumentParser(description="Analizador de comandos Linux con memoria mediante Ollama.")
    parser.add_argument("command", nargs='?', help="El comando o pregunta para la IA.")
    parser.add_argument("--config", action="store_true", help="Abrir configuración interactiva.")
    parser.add_argument("--chat", action="store_true", help="Hablar directamente con la IA.")
    parser.add_argument("--prompt", help="Pregunta específica para el análisis del comando.")
    parser.add_argument("--clear-history", action="store_true", help="Borrar el historial de conversación.")
    args = parser.parse_args()
    
    if args.clear_history:
        if os.path.exists(HISTORY_PATH):
            os.remove(HISTORY_PATH)
        print(f"{GREEN}✨ Historial borrado.{RESET}")
        return

    config = load_config()
    history = load_history()

    if args.config:
        interactive_config()
        return

    if not args.command:
        parser.print_help()
        return

    system_prompt = "Eres un asistente técnico experto en terminales Linux. Sé conciso y directo."
    
    if args.chat:
        print(f"\n{BLUE}{BOLD}💬 Chat Directo con IA:{RESET}")
        messages = [{"role": "system", "content": system_prompt}] + history
        messages.append({"role": "user", "content": args.command})
        
        explanation = ask_ai(messages, config)
        print(f"{ITALIC}{explanation}{RESET}\n")
        
        history.append({"role": "user", "content": args.command})
        history.append({"role": "assistant", "content": explanation})
        save_history(history, config["MAX_HISTORY"])
        return

    # Modo análisis de comando
    base_command = args.command.split()[0] if args.command else ""
    if base_command in config["EXCLUDED_COMMANDS"]:
        return

    output = sys.stdin.read(config["MAX_OUTPUT_CHARS"])
    local_context = get_local_context(args.command, config["KNOWLEDGE_BASE"])
    
    analysis_system = (
        "Eres un asistente técnico experto en terminales Linux. "
        "Analiza el comando y su salida basándote en el contexto y el historial. "
    )
    if args.prompt:
        analysis_system += f"Responde a esta duda específica: '{args.prompt}'. "
    
    analysis_system += "Sé muy conciso (máximo 4-5 líneas)."

    user_content = f"Comando: {args.command}\n"
    if args.prompt:
        user_content += f"Pregunta: {args.prompt}\n"
    if local_context:
        user_content += f"Contexto Manual:\n{local_context}\n"
    user_content += f"Salida:\n{output}"

    messages = [{"role": "system", "content": analysis_system}] + history
    messages.append({"role": "user", "content": user_content})

    explanation = ask_ai(messages, config)
    
    print(f"\n{BLUE}{BOLD}🤖 IA Feedback:{RESET}")
    print(f"{ITALIC}{explanation}{RESET}\n")

    # Guardar en el historial una versión resumida para no saturar el contexto futuro
    history.append({"role": "user", "content": f"Comando ejecutado: {args.command}"})
    history.append({"role": "assistant", "content": explanation})
    save_history(history, config["MAX_HISTORY"])

if __name__ == "__main__":
    main()
