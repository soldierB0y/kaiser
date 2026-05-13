#  Kaiser: Asistente Inteligente de Terminal

Kaiser es un componente de software ligero diseñado para interceptar comandos de Linux y sus salidas, proporcionando explicaciones contextuales instantáneas directamente en tu shell mediante la API local de **Ollama**.

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

Para instalar Kaiser en tu sistema, sigue estos pasos:

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
ai "explica el error paso a paso" cat archivo_inexistente.txt
```

### 💬 Chat y Preguntas Específicas
Term-AI es inteligente detectando tu intención:

1.  **Chat Directo**: Si solo pasas una frase entre comillas (ej. `ai "qué es systemd"`), te responderá directamente.
2.  **Análisis con Pregunta**: Si pasas una frase entre comillas seguida de un comando (ej. `ai "por qué falló?" ls /root`), ejecutará el comando y analizará el resultado respondiendo específicamente a tu pregunta.
3.  **Análisis Estándar**: Si solo pasas el comando (ej. `ai ls`), analizará el resultado de forma general.

### ⚙️ Configuración Interactiva
Ahora puedes configurar el sistema sin editar archivos manualmente. Simplemente ejecuta:
```bash
ai config
```
Esto te permitirá cambiar el modelo, la URL de Ollama, los tiempos de espera y la lista de comandos excluidos de forma interactiva.

### 🧠 Memoria y Historial
Kaiser recuerda las últimas interacciones para que puedas hacer preguntas de seguimiento. Además, puedes gestionar este historial:

- **Ver todas las entradas**:
  ```bash
  ai --history
  ```
- **Ver solo la última interacción**:
  ```bash
  ai --last
  ```
- **Borrar historial**:
  ```bash
  ai --clear-history
  ```

### ⚙️ Configuración
Puedes configurar Kaiser de tres maneras:

1.  **Comando Interactivo (Recomendado)**:
    ```bash
    ai config
    ```
2.  **Restablecer a valores de fábrica**:
    ```bash
    ai --reset-config
    ```
3.  **Edición manual**: Editando el archivo `~/.term_ai_config.json`.

| Variable | Descripción | Valor por Defecto |
| :--- | :--- | :--- |
| `OLLAMA_URL` | Dirección del endpoint de chat de Ollama. | `"http://localhost:11434/api/chat"` |
| `DEFAULT_MODEL` | Modelo de IA a utilizar. | `"qwen2.5-coder:7b"` |
| `TIMEOUT` | Tiempo máximo de espera para la respuesta (segundos). | `30` |
| `MAX_INPUT_CHARS` | Límite de caracteres leídos de la salida del comando. | `2000` |
| `MAX_RESPONSE_TOKENS` | Límite de tokens que la IA puede generar (concisión). | `500` |
| `MAX_HISTORY` | Número de interacciones previas a recordar. | `5` |
| `EXCLUDED_COMMANDS` | Lista de comandos ignorados. | `["top", "nano", "vim", ...]` |
| `KNOWLEDGE_BASE` | Ruta al archivo de manual local. | `"/ruta/a/linuxCommands.txt"` |

> [!TIP]
> **Modelos de Razonamiento**: Kaiser detecta automáticamente modelos como `gemma4` o `qwen3` y desactiva internamente los bloques `<think>` para entregarte la respuesta final directamente, optimizando tu presupuesto de tokens.

## 📁 Estructura del Proyecto

- `term_ai.py`: El motor en Python que gestiona la lógica y la API.
- `shell_integration.sh`: Script de integración (Bash/Zsh).
- `setup.sh`: Instalador automatizado.
- `linuxCommands.txt`: Base de conocimientos local.
- `plan.txt`: Hoja de ruta técnica.


