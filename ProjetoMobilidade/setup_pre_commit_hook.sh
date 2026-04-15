#!/bin/bash
# Script para configurar pre-commit hook que detecta credenciais

echo "🔒 Configurando pre-commit hook para detectar credenciais..."

# Criar diretório de hooks se não existir
mkdir -p .git/hooks

# Criar arquivo pre-commit
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Padrões de credenciais a detectar
PATTERNS=(
    "password"
    "secret"
    "token"
    "DATABASE_URL"
    "EMAIL_SENHA"
    "EMAIL_PASSWORD"
    "GEMINI_API_KEY"
    "API_KEY"
    "ENCRYPTION_KEY"
    "DAmaraLaura"
    "DAtendimento"
    "douglas.amaral@renapsi"
)

# Verificar se há credenciais no commit
FOUND_CREDENTIALS=0

for pattern in "${PATTERNS[@]}"; do
    if git diff --cached | grep -i "$pattern" > /dev/null; then
        echo -e "${RED}❌ ERRO: Padrão '$pattern' detectado no commit!${NC}"
        FOUND_CREDENTIALS=1
    fi
done

if [ $FOUND_CREDENTIALS -eq 1 ]; then
    echo -e "${RED}❌ Commit bloqueado: Credenciais detectadas!${NC}"
    echo -e "${YELLOW}⚠️  Remova as credenciais antes de fazer commit.${NC}"
    echo ""
    echo "Dicas:"
    echo "  1. Use variáveis de ambiente (.env)"
    echo "  2. Nunca commite .env"
    echo "  3. Use os.getenv() para ler credenciais"
    echo ""
    exit 1
fi

echo -e "${GREEN}✅ Nenhuma credencial detectada. Commit permitido.${NC}"
exit 0
EOF

# Tornar o hook executável
chmod +x .git/hooks/pre-commit

echo -e "\n✅ Pre-commit hook configurado com sucesso!"
echo "📝 O hook detectará credenciais antes de cada commit."
echo ""
echo "Para testar:"
echo "  git commit -m 'test: verificar hook'"
