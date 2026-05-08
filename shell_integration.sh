# shell_integration.sh
# Función para envolver comandos y enviarlos al motor de IA

AI_PYTHON_SCRIPT="/usr/local/bin/term_ai.py"

ai_wrapper() {
    # Evitar envolver si el comando es nulo
    if [ -z "$1" ]; then
        return
    fi

    # Soporte para configuración interactiva
    if [ "$1" == "config" ]; then
        python3 "$AI_PYTHON_SCRIPT" --config
        return
    fi

    local custom_prompt=""
    local cmd=""

    # Caso: ai "pregunta" comando (múltiples args, el primero no es un comando ejecutable)
    if [ $# -gt 1 ] && ! command -v "$1" >/dev/null 2>&1; then
        custom_prompt="$1"
        shift
        cmd="$*"
    # Caso: ai "pregunta" (un solo argumento que no es comando -> Chat directo)
    elif [ $# -eq 1 ] && ! command -v "$1" >/dev/null 2>&1; then
        python3 "$AI_PYTHON_SCRIPT" --chat "$1"
        return
    else
        # Caso normal: ai comando (o ai comando args)
        cmd="$*"
    fi

    local tmp_output
    tmp_output=$(mktemp /tmp/ai_term.XXXXXX)

    # Ejecutar y capturar (STDOUT y STDERR)
    eval "$cmd" 2>&1 | tee "$tmp_output"
    
    local exit_status=${PIPESTATUS[0]}

    # Procesar con IA
    if [ -f "$AI_PYTHON_SCRIPT" ]; then
        if [ -n "$custom_prompt" ]; then
            python3 "$AI_PYTHON_SCRIPT" --prompt "$custom_prompt" "$cmd" < "$tmp_output"
        else
            python3 "$AI_PYTHON_SCRIPT" "$cmd" < "$tmp_output"
        fi
    fi

    rm "$tmp_output"
    return $exit_status
}

# Alias sugerido para uso manual o integración
# Para hacer esto "transparente", el usuario puede usar este alias:
# alias ls='ai_wrapper ls'
# O simplemente usar 'ai' como prefijo:
alias ai='ai_wrapper'
