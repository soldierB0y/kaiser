# 🤖 Term-AI: Asistente Inteligente de Terminal

Term-AI es un componente de software ligero diseñado para interceptar comandos de Linux y sus salidas, proporcionando explicaciones contextuales instantáneas directamente en tu shell mediante la API local de **Ollama**.

Este proyecto utiliza una base de conocimientos local personalizada (`linuxCommands.txt`) para asegurar que las explicaciones sean precisas y sigan las recomendaciones de tu propia guía de comandos.

## ✨ Características

- **Análisis en Tiempo Real**: Obtén feedback inmediato después de la ejecución de cualquier comando.
- **Base de Conocimientos Local**: Integración directa con tu manual de comandos personalizado.
- **Privacidad Total**: Todo el procesamiento es local. Tus datos nunca salen de tu máquina.
- **No Intrusivo**: No altera el comportamiento estándar de Linux; el feedback es un añadido visual.
- **Filtro Inteligente**: Ignora comandos ruidosos o interactivos (como `nano`, `top`, `vim`) para optimizar el rendimiento.
- **Estética Premium**: Salida formateada con colores ANSI e itálicas para una distinción visual clara.

## 🛠️ Stack Tecnológico

- **Lenguaje**: Python 3.x
- **Backend de IA**: Ollama (API local)
- **Integración de Shell**: Bash / Zsh
- **Comunicación**: Librería `requests` de Python

## 📋 Requisitos Previos

1.  **Ollama**: Debe estar instalado y ejecutándose en el puerto predeterminado (11434).
2.  **Modelo**: El proyecto está configurado para usar `qwen2.5-coder:7b` (ajustable en `term_ai.py`).
3.  **Python 3**: Con la librería `requests` instalada (`pip install requests`).

## 🚀 Instalación

Para instalar Term-AI en tu sistema, sigue estos pasos:

1.  Dale permisos de ejecución al instalador:
    ```bash
    chmod +x setup.sh
    ```

2.  Ejecuta el script de instalación:
    ```bash
    ./setup.sh
    ```

3.  Recarga tu configuración de shell:
    ```bash
    source ~/.bashrc  # Si usas Bash
    # O
    source ~/.zshrc   # Si usas Zsh
    ```

## ⌨️ Uso

Una vez instalado, simplemente antepón el comando `ai` a cualquier instrucción que quieras ejecutar y analizar:

```bash
ai ls /directorio/inexistente
ai uname -a
ai "Cómo puedo listar solo archivos .txt?"
```

### 💬 Chat Directo
Si pasas una frase entre comillas que no sea un comando ejecutable (ej. `ai "explícame qué es un kernel"`), Term-AI entrará en modo chat directo sin intentar ejecutar nada en tu sistema.

### ⚙️ Configuración Interactiva
Ahora puedes configurar el sistema sin editar archivos manualmente. Simplemente ejecuta:
```bash
ai config
```
Esto te permitirá cambiar el modelo, la URL de Ollama, los tiempos de espera y la lista de comandos excluidos de forma interactiva.

### Exclusión de Comandos
El sistema ignorará automáticamente comandos definidos en la lista de exclusión (ej. `top`, `vim`, `ssh`) para evitar saturar la IA con salidas innecesarias o flujos interactivos.

## ⚙️ Configuración

Aunque puedes editar el archivo `~/.term_ai_config.json` manualmente, la forma recomendada es usar el comando interactivo:

```bash
ai config
```

| Variable | Descripción | Valor por Defecto |
| :--- | :--- | :--- |
| `OLLAMA_URL` | Dirección del servidor Ollama. | `"http://localhost:11434/api/generate"` |
| `DEFAULT_MODEL` | Modelo de IA a utilizar. | `"qwen2.5-coder:7b"` |
| `TIMEOUT` | Tiempo máximo de espera para la respuesta de la IA (segundos). | `30` |
| `MAX_OUTPUT_CHARS` | Límite de caracteres de la salida del comando que se envían a la IA. | `2000` |
| `EXCLUDED_COMMANDS` | Lista de comandos que nunca serán analizados por la IA. | `["top", "nano", "vim", ...]` |
| `KNOWLEDGE_BASE` | Ruta al archivo de manual local. | `"/ruta/a/linuxCommands.txt"` |

> [!TIP]
> Si cambias el modelo en Ollama, asegúrate de haberlo descargado previamente usando `ollama pull <nombre-del-modelo>`.

## 📁 Estructura del Proyecto

- `term_ai.py`: El cerebro del proyecto. Gestiona la lógica y comunicación con Ollama.
- `shell_integration.sh`: Proporciona la función `ai_wrapper` y el alias para tu shell.
- `setup.sh`: Script de automatización para una instalación rápida y segura.
- `linuxCommands.txt`: Tu manual local de referencia.
- `plan.txt`: El diseño técnico original del proyecto.


