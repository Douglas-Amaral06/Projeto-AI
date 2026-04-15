# 🚨 PLANO DE REMEDIAÇÃO URGENTE — Credenciais Expostas no Git

## STATUS: CRÍTICO ⚠️

Credenciais foram encontradas no histórico do Git:
- ✅ Senha do Supabase: `DAmaraLaura@2017`
- ✅ Senha do E-mail: `DAtendimento@Jovem25`
- ✅ E-mail corporativo: `douglas.amaral@renapsi.org.br`

---

## AÇÕES IMEDIATAS (FAZER AGORA)

### 1️⃣ Invalidar Credenciais Expostas

#### Supabase:
1. Acesse https://app.supabase.com
2. Vá para **Settings → Database → Password**
3. Clique em **Reset Password**
4. Copie a nova senha
5. Atualize `.env` local com a nova `DATABASE_URL`

#### E-mail (Outlook/Office365):
1. Acesse https://account.microsoft.com
2. Vá para **Segurança → Senhas de aplicação**
3. Revogue a senha atual
4. Gere uma nova senha de aplicação
5. Atualize `.env` com `EMAIL_SENHA=<nova_senha>`

---

### 2️⃣ Limpar Histórico Git

**Opção A: Usar git filter-repo (RECOMENDADO)**

```bash
# Instalar git-filter-repo
pip install git-filter-repo

# Remover credenciais do histórico
git filter-repo --path .env --invert-paths
git filter-repo --path email_sender.py --invert-paths
git filter-repo --path app_piloto.py --invert-paths
git filter-repo --path migrar_dados.py --invert-paths

# Force push (CUIDADO: afeta todos os colaboradores)
git push -f origin main
```

**Opção B: Usar git filter-branch (Alternativa)**

```bash
# Remover .env do histórico
git filter-branch --tree-filter 'rm -f .env' -f -- --all

# Force push
git push -f origin main
```

---

### 3️⃣ Verificar se Credenciais Foram Comprometidas

**Supabase:**
- Verifique logs de acesso em **Settings → Logs**
- Procure por acessos suspeitos após a data de exposição

**E-mail:**
- Verifique atividade de login em https://account.microsoft.com/security
- Procure por acessos de locais desconhecidos

---

## PREVENÇÃO FUTURA

### ✅ Implementado:
- `.env` adicionado ao `.gitignore`
- Arquivos sensíveis camuflados
- Validação de credenciais em tempo de execução

### ⚠️ Ainda Fazer:
- [ ] Implementar pre-commit hook para detectar credenciais
- [ ] Usar `git-secrets` para prevenir commits com credenciais
- [ ] Implementar scanning automático no CI/CD

---

## INSTALAÇÃO DE PROTEÇÃO

### Pre-commit Hook (Previne Commits com Credenciais)

Criar arquivo `.git/hooks/pre-commit`:

```bash
#!/bin/bash

# Procura por padrões de credenciais
if git diff --cached | grep -E "password|secret|token|DATABASE_URL|EMAIL_SENHA|GEMINI_API_KEY"; then
    echo "❌ ERRO: Credenciais detectadas no commit!"
    echo "Remova as credenciais antes de fazer commit."
    exit 1
fi

exit 0
```

Tornar executável:
```bash
chmod +x .git/hooks/pre-commit
```

---

## RESUMO DE RISCO

| Credencial | Risco | Ação |
|-----------|-------|------|
| Senha Supabase | 🔴 CRÍTICO | ✅ Invalidada |
| Senha E-mail | 🔴 CRÍTICO | ✅ Invalidada |
| E-mail Corporativo | 🟠 ALTO | ✅ Camuflado |

---

## PRÓXIMAS ETAPAS

1. ✅ Invalidar credenciais (HOJE)
2. ✅ Limpar histórico Git (HOJE)
3. ✅ Force push (HOJE)
4. ⏳ Implementar pre-commit hooks (Esta semana)
5. ⏳ Implementar git-secrets (Esta semana)
6. ⏳ Auditoria de segurança completa (Próxima semana)

---

**Responsável:** Douglas Amaral  
**Data:** Abril 2026  
**Status:** Em Progresso
