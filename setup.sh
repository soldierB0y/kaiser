#!/bin/bash

# setup.sh - Instalador para Term-AI
# Autor: Antigravity AI

# Colores para la terminal
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Iniciando instalación de Term-AI...${NC}"

# 1. Definir rutas
BIN_DIR="$HOME/.local/bin"
INSTALL_PATH="$BIN_DIR/term_ai.py"
INTEGRATION_PATH="$HOME/.term_ai_integration.sh"

# Crear directorio bin si no existe
mkdir -p "$BIN_DIR"

# 2. Copiar archivos
echo -e "${YELLOW}📦 Copiando scripts...${NC}"
cp term_ai.py "$INSTALL_PATH"
chmod +x "$INSTALL_PATH"
cp shell_integration.sh "$INTEGRATION_PATH"

# Ajustar la ruta en el script de integración si es necesario
sed -i "s|/usr/local/bin/term_ai.py|$INSTALL_PATH|g" "$INTEGRATION_PATH"

# 3. Detectar Shell y configurar
CURRENT_SHELL=$(basename "$SHELL")
CONFIG_FILE=""

if [ "$CURRENT_SHELL" == "zsh" ]; then
    CONFIG_FILE="$HOME/.zshrc"
elif [ "$CURRENT_SHELL" == "bash" ]; then
    CONFIG_FILE="$HOME/.bashrc"
else
    echo -e "${RED}⚠️ Shell no soportada automáticamente ($CURRENT_SHELL).${NC}"
    echo -e "Por favor, añade 'source $INTEGRATION_PATH' manualmente a tu archivo de configuración."
fi

if [ -n "$CONFIG_FILE" ]; then
    if ! grep -q "term_ai_integration.sh" "$CONFIG_FILE"; then
        echo -e "${YELLOW}📝 Añadiendo configuración a $CONFIG_FILE...${NC}"
        echo "" >> "$CONFIG_FILE"
        echo "# Term-AI Integration" >> "$CONFIG_FILE"
        echo "source $INTEGRATION_PATH" >> "$CONFIG_FILE"
    else
        echo -e "${GREEN}✅ Configuración ya presente en $CONFIG_FILE.${NC}"
    fi
fi

# 4. Verificar Ollama
echo -e "${YELLOW}🔍 Verificando servicio Ollama...${NC}"
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo -e "${GREEN}✅ Ollama está activo.${NC}"
else
    echo -e "${RED}❌ Ollama no parece estar corriendo en localhost:11434.${NC}"
    echo -e "Asegúrate de iniciar Ollama antes de usar Term-AI."
fi

# 5. Finalizar
echo -e "\n${GREEN}✨ ¡Instalación completada!${NC}"
echo -e "Por favor, reinicia tu terminal o ejecuta: ${BLUE}source $CONFIG_FILE${NC}"
echo -e "Uso: ${BLUE}ai <comando>${NC} (ejemplo: ai ls -la)"
