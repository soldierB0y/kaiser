#!/usr/bin/env python3
import sys
import json
import re
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
    "MAX_INPUT_CHARS": 5000,       # Máx. caracteres leídos del output del comando
    "MAX_RESPONSE_TOKENS": 500,    # Máx. tokens que la IA puede generar (num_predict)
    "MAX_HISTORY": 5,  # Número de interacciones previas a recordar
    "LANGUAGE": "es",  # Idioma de las respuestas (es/en)
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
    """Displays an animated loading spinner with elapsed time counter while waiting for AI responses."""
    def __init__(self, message="Thinking", delay=0.1):
        self.message = message
        self.delay = delay
        self.running = False
        self.thread = None
        self.start_time = None
        self.spinners = {
            "dots": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        }
        self.current_spinner = self.spinners["dots"]
    
    def start(self):
        self.running = True
        self.start_time = time.time()
        self.thread = threading.Thread(target=self._animate, daemon=True)
        self.thread.start()
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        elapsed = int(time.time() - self.start_time)
        # Mantener el tiempo final en pantalla
        sys.stdout.write(f"\r{GREEN}✓{RESET} {self.message} ({elapsed}s){RESET}\033[K\n")
        sys.stdout.flush()
    
    def _animate(self):
        spinner_cycle = cycle(self.current_spinner)
        while self.running:
            frame = next(spinner_cycle)
            elapsed = int(time.time() - self.start_time)
            sys.stdout.write(f"\r{CYAN}{frame} {self.message}... ({elapsed}s){RESET}")
            sys.stdout.flush()
            time.sleep(self.delay)

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                user_config = json.load(f)
            # Migrar clave antigua MAX_OUTPUT_CHARS -> MAX_INPUT_CHARS
            if "MAX_OUTPUT_CHARS" in user_config and "MAX_INPUT_CHARS" not in user_config:
                user_config["MAX_INPUT_CHARS"] = user_config.pop("MAX_OUTPUT_CHARS")
            elif "MAX_OUTPUT_CHARS" in user_config:
                user_config.pop("MAX_OUTPUT_CHARS")
            return {**DEFAULT_CONFIG, **user_config}
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
        elif key == "LANGUAGE":
            new_val = input(f"{BOLD}{key}{RESET} (es/en) [{value}]: ").strip().lower()
            if new_val in ["es", "en"]:
                config[key] = new_val
            elif new_val:
                print(f"{YELLOW}⚠️ Idioma no soportado. Se mantiene {value}.{RESET}")
        else:
            new_val = input(f"{BOLD}{key}{RESET} [{value}]: ").strip()
            if new_val:
                if isinstance(value, int):
                    try:
                        config[key] = int(new_val)
                    except ValueError:
                        print(f"{YELLOW}⚠️ Valor inválido para {key}, se mantiene {value}.{RESET}")
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

def strip_thinking(text):
    """Remove <think>...</think> blocks from model output (reasoning models like Gemma4, Qwen3)."""
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    return cleaned.strip()

def ask_ai(messages, config):
    payload = {
        "model": config["DEFAULT_MODEL"],
        "messages": messages,
        "stream": False,
        "think": False,
        "options": {
            "num_predict": config["MAX_RESPONSE_TOKENS"]
        }
    }
    
    spinner = LoadingSpinner(message=f"{BLUE}Analyzing with {config['DEFAULT_MODEL']}")
    spinner.start()
    
    try:
        response = requests.post(config["OLLAMA_URL"], json=payload, timeout=config["TIMEOUT"])
        response.raise_for_status()
        result = response.json()
        spinner.stop()
        
        # Extract token information and performance metrics
        input_tokens = result.get("prompt_eval_count", 0)
        output_tokens = result.get("eval_count", 0)
        eval_duration = result.get("eval_duration", 0) # Nanoseconds
        
        tps = 0.0
        if output_tokens > 0 and eval_duration > 0:
            # Convert nanoseconds to seconds
            duration_sec = eval_duration / 1_000_000_000
            tps = output_tokens / duration_sec

        # Handle both new and old Ollama API response formats
        if "message" in result and "content" in result["message"]:
            content = result["message"]["content"]
        elif "response" in result:
            # Old API format
            content = result["response"] if result["response"] else "La IA no generó una respuesta."
        else:
            return f"Respuesta inesperada del servidor: {json.dumps(result)}", 0, 0, 0.0
        
        # Limpiar bloques de pensamiento de modelos de razonamiento
        content = strip_thinking(content)
        if not content:
            content = "(La IA usó todos los tokens en razonamiento interno. Aumenta MAX_RESPONSE_TOKENS.)"
        
        return content, input_tokens, output_tokens, tps
    except requests.exceptions.Timeout:
        spinner.stop()
        return f"❌ Error de tiempo: Ollama tardó más de {config['TIMEOUT']} segundos", 0, 0, 0.0
    except requests.exceptions.ConnectionError as e:
        spinner.stop()
        return f"❌ No se puede conectar a Ollama en {config['OLLAMA_URL']}: {e}", 0, 0, 0.0
    except requests.exceptions.RequestException as e:
        spinner.stop()
        return f"❌ Error de solicitud: {e}", 0, 0, 0.0
    except json.JSONDecodeError as e:
        spinner.stop()
        return f"❌ Error al procesar respuesta JSON: {e}", 0, 0, 0.0
    except Exception as e:
        spinner.stop()
        return f"❌ Error inesperado: {type(e).__name__}: {e}", 0, 0, 0.0

def main():
    parser = argparse.ArgumentParser(
        description="Analizador de comandos Linux con memoria mediante Ollama.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
FUNCIONES DISPONIBLES:

  1. CHAT DIRECTO CON IA (--chat)
     Conversa libremente con la IA sin procesar comandos.
     Uso: ai --chat "Tu pregunta aquí"
     Ejemplo: ai --chat "¿Cómo funciona Docker?"

  2. ANÁLISIS DE COMANDOS (modo por defecto)
     Analiza un comando Linux y su salida. Canaliza la salida del comando.
     Uso: comando | ai "comando"
     Ejemplo: ls -la | ai "ls"

  3. ANÁLISIS CON PREGUNTA PERSONALIZADA (--prompt)
     Analiza un comando pero responde a una pregunta específica.
     Uso: comando | ai "comando" --prompt "Tu pregunta"
     Ejemplo: ps aux | ai "ps aux" --prompt "¿Qué procesos están corriendo?"

  4. CONFIGURACIÓN INTERACTIVA (--config)
     Abre el configurador interactivo para personalizar opciones.
     Uso: ai --config
     Personaliza: URL de Ollama, modelo, timeout, límites, etc.

  5. BORRAR HISTORIAL (--clear-history)
     Borra todo el historial de conversaciones guardado.
     Uso: ai --clear-history

  6. VER HISTORIAL (--history)
     Muestra todas las interacciones guardadas.
     Uso: ai --history

  7. VER ÚLTIMA ENTRADA (--last)
     Muestra solo la última interacción con la IA.
     Uso: ai --last

  8. RESTABLECER CONFIGURACIÓN (--reset-config)
     Vuelve a los valores por defecto de la aplicación.
     Uso: ai --reset-config

CONFIGURACIÓN:
  El archivo de config se guarda en: ~/.term_ai_config.json
  El historial se guarda en: ~/.term_ai_history.json

EJEMPLOS COMPLETOS:

  # Conversar con la IA
  $ ai --chat "Explícame qué es un shell script"

  # Analizar comando
  $ echo "archivos" | ai "ls"

  # Preguntar específicamente sobre la salida
  $ ps aux | ai "ps" --prompt "¿Qué proceso está usando más memoria?"

  # Cambiar configuración
  $ ai --config

  # Limpiar historial
  $ ai --clear-history

  # Ver historial completo
  $ ai --history

  # Ver última interacción
  $ ai --last

  # Restablecer valores
  $ ai --reset-config
        """
    )
    parser.add_argument("command", nargs='?', help="El comando o pregunta para la IA.")
    parser.add_argument("--config", action="store_true", help="Abrir configuración interactiva.")
    parser.add_argument("--reset-config", action="store_true", help="Restablecer configuración a los valores por defecto.")
    parser.add_argument("--history", action="store_true", help="Mostrar el historial de conversaciones.")
    parser.add_argument("--last", action="store_true", help="Mostrar la última entrada del historial.")
    parser.add_argument("--chat", action="store_true", help="Hablar directamente con la IA.")
    parser.add_argument("--prompt", help="Pregunta específica para el análisis del comando.")
    parser.add_argument("--clear-history", action="store_true", help="Borrar el historial de conversación.")
    args = parser.parse_args()
    
    if args.clear_history:
        if os.path.exists(HISTORY_PATH):
            os.remove(HISTORY_PATH)
        print(f"{GREEN}✨ Historial borrado.{RESET}")
        return

    if args.history or args.last:
        history = load_history()
        if not history:
            print(f"{YELLOW}📭 El historial está vacío.{RESET}")
            return
        
        print(f"\n{BLUE}{BOLD}📜 Historial de Term-AI:{RESET}")
        
        # Cada interacción tiene 2 mensajes (user y assistant)
        entries = []
        for i in range(0, len(history), 2):
            if i + 1 < len(history):
                entries.append((history[i], history[i+1]))
        
        to_show = [entries[-1]] if args.last else entries
        
        for i, (user, assistant) in enumerate(to_show):
            idx = len(entries) - 1 if args.last else i
            print(f"{CYAN}{BOLD}┌── [Entrada {idx + 1}] ─────────────────────────────────{RESET}")
            
            # Mostrar contenido del usuario (truncar visualmente si es gigante)
            u_content = user['content']
            if len(u_content) > 1000 and not args.last:
                u_content = u_content[:1000] + f"\n{YELLOW}[... Contenido truncado en vista previa ...]{RESET}"
            
            print(f"{GREEN}{BOLD}│ Usuario:{RESET} {u_content}")
            print(f"{BLUE}{BOLD}│ IA:{RESET} {ITALIC}{assistant['content']}{RESET}")
            print(f"{CYAN}└─────────────────────────────────────────────────────{RESET}\n")
        return

    if args.reset_config:
        if os.path.exists(CONFIG_PATH):
            os.remove(CONFIG_PATH)
            print(f"{GREEN}🔄 Configuración restablecida a valores por defecto.{RESET}")
        else:
            print(f"{YELLOW}⚠️ No se encontró archivo de configuración personalizado.{RESET}")
        return

    config = load_config()
    history = load_history()

    if args.config:
        interactive_config()
        return

    if not args.command:
        parser.print_help()
        return

    lang = config.get("LANGUAGE", "es").lower()
    token_limit = config["MAX_RESPONSE_TOKENS"]
    
    if lang == "en":
        system_prompt = (
            f"You are a technical expert assistant in Linux terminals. "
            f"IMPORTANT: Your response MUST be complete in a maximum of {token_limit} tokens. "
            f"Be extremely concise and direct. Do not use long lists or extensive explanations. "
            f"Always finish with a complete sentence."
        )
        analysis_system = (
            f"You are a technical expert assistant in Linux terminals. "
            f"Analyze the command and its output based on context and history. "
            f"IMPORTANT: Your response MUST be complete in a maximum of {token_limit} tokens. "
            f"Be extremely concise (max 3-4 lines). Always finish with a complete sentence."
        )
        chat_label = "Direct Chat with AI"
        feedback_label = "AI Feedback"
        tokens_label = "Tokens - Input"
        output_label = "Output"
    else:
        system_prompt = (
            f"Eres un asistente técnico experto en terminales Linux. "
            f"IMPORTANTE: Tu respuesta DEBE ser completa en máximo {token_limit} tokens. "
            f"Sé extremadamente conciso y directo. No uses listas largas ni explicaciones extensas. "
            f"Termina siempre con una oración completa."
        )
        analysis_system = (
            f"Eres un asistente técnico experto en terminales Linux. "
            f"Analiza el comando y su salida basándote en el contexto y el historial. "
            f"IMPORTANTE: Tu respuesta DEBE ser completa en máximo {token_limit} tokens. "
            f"Sé extremadamente conciso (máximo 3-4 líneas). Termina siempre con una oración completa."
        )
        chat_label = "Chat Directo con IA"
        feedback_label = "IA Feedback"
        tokens_label = "Tokens - Entrada"
        output_label = "Salida"
    
    if args.chat:
        print(f"\n{BLUE}{BOLD}💬 {chat_label}:{RESET}")
        
        # Intentar obtener contexto manual incluso en chat
        local_context = get_local_context(args.command, config["KNOWLEDGE_BASE"])
        user_content = args.command
        if local_context:
            if lang == "en":
                user_content = f"Manual Context:\n{local_context}\n\nQuestion: {args.command}"
            else:
                user_content = f"Contexto Manual:\n{local_context}\n\nPregunta: {args.command}"

        messages = [{"role": "system", "content": system_prompt}] + history
        messages.append({"role": "user", "content": user_content})
        
        explanation, input_tokens, output_tokens, tps = ask_ai(messages, config)
        print(f"{ITALIC}{explanation}{RESET}\n")
        print(f"{CYAN}📊 {tokens_label}: {input_tokens} | {output_label}: {output_tokens} ({tps:.1f} t/s){RESET}\n")
        
        # Guardar en el historial (usamos el content completo para que --last sea veraz)
        history.append({"role": "user", "content": user_content})
        history.append({"role": "assistant", "content": explanation})
        save_history(history, config["MAX_HISTORY"])
        return

    # Modo análisis de comando
    base_command = args.command.split()[0] if args.command else ""
    if base_command in config["EXCLUDED_COMMANDS"]:
        return

    output = sys.stdin.read(config["MAX_INPUT_CHARS"])
    local_context = get_local_context(args.command, config["KNOWLEDGE_BASE"])
    
    if args.prompt:
        if lang == "en":
            analysis_system += f" Answer this specific doubt: '{args.prompt}'."
        else:
            analysis_system += f" Responde a esta duda específica: '{args.prompt}'."

    user_content = f"Comando: {args.command}\n"
    if args.prompt:
        user_content += f"Pregunta: {args.prompt}\n"
    if local_context:
        user_content += f"Contexto Manual:\n{local_context}\n"
    user_content += f"Salida:\n{output}"

    messages = [{"role": "system", "content": analysis_system}] + history
    messages.append({"role": "user", "content": user_content})

    explanation, input_tokens, output_tokens, tps = ask_ai(messages, config)
    
    print(f"{BLUE}{BOLD}🤖 {feedback_label}:{RESET}")
    print(f"{ITALIC}{explanation}{RESET}\n")
    print(f"{CYAN}📊 {tokens_label}: {input_tokens} | {output_label}: {output_tokens} ({tps:.1f} t/s){RESET}\n")

    # Guardar en el historial la versión completa para que --history sea útil
    history.append({"role": "user", "content": user_content})
    history.append({"role": "assistant", "content": explanation})
    save_history(history, config["MAX_HISTORY"])

if __name__ == "__main__":
    main()
