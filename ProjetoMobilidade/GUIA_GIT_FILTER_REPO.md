# 🚀 Guia — Git Filter-Repo (Ferramenta Recomendada)

**Data:** Abril 2026  
**Ferramenta:** git-filter-repo (Recomendada pelo Git)  
**Vantagens:** Mais rápida, mais segura, melhor tratamento de erros  
**Status:** ✅ RECOMENDADA

---

## 📋 Por que Git Filter-Repo?

| Aspecto | git filter-branch | git filter-repo |
|--------|------------------|-----------------|
| **Velocidade** | Lenta | ⚡ Rápida |
| **Segurança** | ⚠️ Gotchas | ✅ Segura |
| **Erros** | Difíceis de debugar | ✅ Claros |
| **Recomendação** | ❌ Descontinuada | ✅ Oficial |
| **Windows** | ⚠️ Problemas | ✅ Funciona bem |

---

## 🔧 Instalação

### Passo 1: Instalar git-filter-repo

```bash
# Opção 1: Via pip (Recomendado)
pip install git-filter-repo

# Opção 2: Via Chocolatey (Windows)
choco install git-filter-repo

# Opção 3: Via Homebrew (macOS)
brew install git-filter-repo

# Verificar instalação
git filter-repo --version
```

### Passo 2: Verificar Instalação

```bash
# Deve retornar a versão
git filter-repo --version
# Exemplo: git-filter-repo version 2.38.0
```

---

## 🚀 Execução

### Passo 1: Criar Backup

```bash
# Criar backup do repositório
cp -r . .backup
# Ou no PowerShell:
Copy-Item -Recurse . .backup
```

### Passo 2: Remover Arquivos do Histórico

```bash
# Remover .env
git filter-repo --path .env --invert-paths

# Remover email_sender.py
git filter-repo --path email_sender.py --invert-paths

# Remover app_piloto.py
git filter-repo --path app_piloto.py --invert-paths

# Remover migrar_dados.py
git filter-repo --path migrar_dados.py --invert-paths

# Remover SECURITY.md
git filter-repo --path SECURITY.md --invert-paths

# Remover AUDITORIA_SEGURANCA_COMPLETA.md
git filter-repo --path AUDITORIA_SEGURANCA_COMPLETA.md --invert-paths

# Remover seguranca_erros.py
git filter-repo --path seguranca_erros.py --invert-paths

# Remover encriptacao_dados.py
git filter-repo --path encriptacao_dados.py --invert-paths
```

### Passo 3: Force Push

```bash
# ⚠️ CUIDADO: Isso reescreverá o histórico remoto!
git push -f origin main
```

### Passo 4: Verificar Limpeza

```bash
# Verificar se .env foi removido
git log --all --full-history -- .env
# Resultado esperado: (nada)

# Verificar se há credenciais
git log -p --all | grep -i "DATABASE_URL\|EMAIL_SENHA\|password"
# Resultado esperado: (nada)
```

---

## 📝 Script Automatizado (PowerShell)

Crie um arquivo `limpar_com_filter_repo.ps1`:

```powershell
# Script PowerShell para usar git-filter-repo

Write-Host "🚀 LIMPEZA COM GIT-FILTER-REPO" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se git-filter-repo está instalado
try {
    git filter-repo --version | Out-Null
    Write-Host "✅ git-filter-repo encontrado" -ForegroundColor Green
} catch {
    Write-Host "❌ git-filter-repo não está instalado!" -ForegroundColor Red
    Write-Host "Instale com: pip install git-filter-repo" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Arquivos a remover
$arquivos = @(
    ".env",
    "email_sender.py",
    "app_piloto.py",
    "migrar_dados.py",
    "SECURITY.md",
    "AUDITORIA_SEGURANCA_COMPLETA.md",
    "seguranca_erros.py",
    "encriptacao_dados.py"
)

Write-Host "Arquivos que serão removidos:" -ForegroundColor Yellow
foreach ($arquivo in $arquivos) {
    Write-Host "  - $arquivo"
}
Write-Host ""

# Confirmar
$resposta = Read-Host "Deseja continuar? (s/n)"
if ($resposta -ne "s") {
    Write-Host "Operação cancelada." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Iniciando limpeza..." -ForegroundColor Cyan
Write-Host ""

# Remover cada arquivo
foreach ($arquivo in $arquivos) {
    Write-Host "Removendo: $arquivo" -ForegroundColor Yellow
    
    try {
        git filter-repo --path $arquivo --invert-paths --force 2>&1 | Out-Null
        Write-Host "  ✅ Removido" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠️  Erro: $_" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Verificando se credenciais foram removidas..." -ForegroundColor Cyan

# Verificar se .env foi removido
$resultado = git log --all --full-history -- .env 2>&1
if ($resultado -match "commit") {
    Write-Host "  ⚠️  .env ainda está no histórico!" -ForegroundColor Yellow
} else {
    Write-Host "  ✅ .env removido do histórico" -ForegroundColor Green
}

Write-Host ""
Write-Host "Pronto para fazer force push?" -ForegroundColor Cyan
$resposta = Read-Host "Fazer force push para origin/main? (s/n)"

if ($resposta -eq "s") {
    Write-Host ""
    Write-Host "Fazendo force push..." -ForegroundColor Cyan
    
    try {
        git push -f origin main 2>&1
        Write-Host ""
        Write-Host "✅ Force push concluído com sucesso!" -ForegroundColor Green
    } catch {
        Write-Host "❌ Erro ao fazer force push!" -ForegroundColor Red
        Write-Host "Tente manualmente: git push -f origin main" -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "Force push não foi executado." -ForegroundColor Yellow
    Write-Host "Para fazer depois, execute: git push -f origin main" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ Limpeza concluída!" -ForegroundColor Green
```

Execute com:
```bash
powershell -ExecutionPolicy Bypass -File limpar_com_filter_repo.ps1
```

---

## ✅ Verificação Pós-Limpeza

### 1. Verificar Remoção de Arquivos

```bash
# Verificar se .env foi removido
git log --all --full-history -- .env
# Resultado esperado: (nada)

# Verificar se email_sender.py foi removido
git log --all --full-history -- email_sender.py
# Resultado esperado: (nada)
```

### 2. Verificar Remoção de Credenciais

```bash
# Procurar por DATABASE_URL
git log -p --all | grep -i "DATABASE_URL"
# Resultado esperado: (nada)

# Procurar por EMAIL_SENHA
git log -p --all | grep -i "EMAIL_SENHA"
# Resultado esperado: (nada)

# Procurar por senhas
git log -p --all | grep -i "password\|senha"
# Resultado esperado: (nada)
```

### 3. Verificar Tamanho do Repositório

```bash
# Verificar tamanho
git count-objects -v

# Antes: ~50MB (com credenciais)
# Depois: ~30MB (sem credenciais)
```

---

## 🔄 Comunicação com Colaboradores

Após fazer force push, comunique:

```
Atenção: O histórico Git foi reescrito para remover credenciais expostas.

Para sincronizar seu repositório local:

1. Faça backup do seu trabalho atual
2. Execute: git fetch origin
3. Execute: git reset --hard origin/main
4. Execute: git clean -fd

Se tiver branches locais não sincronizadas, salve-as antes!
```

---

## 🆘 Se Algo Der Errado

### Restaurar do Backup

```bash
# Se tudo deu errado, restaure do backup
rm -rf .git
cp -r .backup/.git .

# Ou restaure tudo
rm -rf *
cp -r .backup/* .
```

### Desfazer Force Push

```bash
# Se fez force push por engano
# Contacte o administrador do repositório

# Opção: Recriar o repositório
git init
git add .
git commit -m "Repositório recriado"
git push -f origin main
```

---

## 📊 Checklist

- [ ] git-filter-repo instalado
- [ ] Backup criado
- [ ] Credenciais invalidadas
- [ ] `.env` local atualizado
- [ ] Colaboradores comunicados
- [ ] Arquivos removidos do histórico
- [ ] Force push realizado
- [ ] Verificação pós-limpeza concluída
- [ ] Colaboradores sincronizaram

---

## 📞 Suporte

**Dúvidas?**
- Leia: `GUIA_LIMPEZA_GIT_HISTORY.md`
- Leia: `PLANO_REMEDIACAO_URGENTE.md`

**Problemas?**
- Verifique se git-filter-repo está instalado
- Verifique se está no diretório correto
- Verifique se tem permissão de escrita

---

**Status:** 🟢 PRONTO PARA EXECUÇÃO  
**Ferramenta:** git-filter-repo (Recomendada)  
**Risco:** ⚠️ ALTO (Reescreverá histórico)

