# 🔒 Guia de Segurança — RENAPSI Mobilidade

## Proteção de Credenciais

### 1. Arquivo `.env`

O arquivo `.env` contém credenciais sensíveis e **NUNCA deve ser commitado** no repositório Git.

#### Como criar o arquivo `.env`:

1. Copie o arquivo `.env.example`:
   ```bash
   cp .env.example .env
   ```

2. Edite o arquivo `.env` com suas credenciais reais:
   ```env
   DATABASE_URL=postgresql://postgres:sua_senha@db.seu_projeto.supabase.co:5432/postgres
   ```

3. Certifique-se de que `.env` está no `.gitignore`:
   ```
   .env
   ```

### 2. Variáveis de Ambiente

O projeto utiliza `python-dotenv` para carregar variáveis de ambiente de forma segura.

#### Variáveis Obrigatórias:

- **DATABASE_URL**: String de conexão do Supabase
  - Formato: `postgresql://usuario:senha@host:porta/banco_dados`
  - Exemplo: `postgresql://postgres:minha_senha@db.qkbwjjtnxmfdwbgcthac.supabase.co:5432/postgres`

#### Variáveis Opcionais:

- **SMTP_USER**: E-mail para envio de cartas
- **SMTP_PASSWORD**: Senha do e-mail
- **SMTP_SERVER**: Servidor SMTP (ex: smtp.office365.com)
- **SMTP_PORT**: Porta SMTP (ex: 587)

### 3. Instalação de Dependências

Certifique-se de que `python-dotenv` está instalado:

```bash
pip install python-dotenv
```

Ou adicione ao `requirements.txt`:

```
python-dotenv>=1.0.0
```

### 4. Tratamento de Erros

O código valida se as variáveis de ambiente estão presentes:

```python
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError(
        "❌ ERRO CRÍTICO: Variável DATABASE_URL não encontrada!\n"
        "Certifique-se de que o arquivo .env existe na raiz do projeto."
    )
```

### 5. Boas Práticas

✅ **Faça:**
- Armazene credenciais no arquivo `.env`
- Use `os.getenv()` para acessar variáveis
- Adicione `.env` ao `.gitignore`
- Valide se as variáveis existem antes de usar
- Use variáveis de ambiente em produção

❌ **Não Faça:**
- Hardcode credenciais no código
- Commit do arquivo `.env`
- Compartilhe o arquivo `.env` por e-mail ou chat
- Use a mesma senha em múltiplos ambientes
- Exponha credenciais em logs ou mensagens de erro

### 6. Rotação de Credenciais

Se suas credenciais forem expostas:

1. **Imediatamente:**
   - Altere a senha no Supabase
   - Atualize o arquivo `.env` local
   - Revogue tokens de API se necessário

2. **Depois:**
   - Verifique o histórico do Git para remover credenciais expostas
   - Use `git filter-branch` ou `git filter-repo` se necessário
   - Notifique a equipe sobre a mudança

### 7. Verificação de Segurança

Para verificar se há credenciais expostas no repositório:

```bash
# Procurar por padrões de credenciais
git log -p | grep -i "password\|secret\|token\|DATABASE_URL"

# Usar ferramentas como git-secrets
git secrets --scan
```

### 8. Conformidade com LGPD

- ✅ Dados processados localmente quando possível
- ✅ Credenciais protegidas com `.env`
- ✅ Sem compartilhamento de dados sensíveis com APIs externas
- ✅ Anonimização de dados em APIs públicas

---

**Última atualização:** Abril 2026
**Responsável:** Equipe de Segurança RENAPSI
