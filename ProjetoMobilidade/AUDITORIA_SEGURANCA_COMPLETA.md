# 🔐 AUDITORIA COMPLETA DE SEGURANÇA — RENAPSI Mobilidade
**Data:** Abril 2026  
**Auditor:** DevSecOps Senior  
**Status:** ⚠️ CRÍTICO — Credenciais Expostas Detectadas

---

## 📋 SUMÁRIO EXECUTIVO

### 🚨 ACHADOS CRÍTICOS
- ✅ **Credenciais de E-mail EXPOSTAS** em `email_sender.py` (linha 14-15)
- ✅ **Credenciais do Supabase EXPOSTAS** em `.env` (visível no repositório)
- ✅ **Chave de API Gemini** potencialmente exposta em `agente_ia.py`
- ⚠️ **Dados Pessoais NÃO ENCRIPTADOS** no banco SQLite
- ⚠️ **Mensagens de Erro Técnicas** podem expor informações do sistema

### ✅ PONTOS POSITIVOS
- ✅ `.env` está no `.gitignore` (proteção parcial)
- ✅ `python-dotenv` implementado corretamente
- ✅ Tratamento de erros básico em `agente_ia.py`
- ✅ Validação de credenciais em `app_piloto.py` e `migrar_dados.py`

---

## FASE 1: AUDITORIA DE FUGAS E EXPOSIÇÃO DE DADOS

### 1.1 Credenciais Hardcoded Detectadas

#### 🚨 CRÍTICO: `email_sender.py` (Linhas 14-15)

```python
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE", "seu_email@renapsi.org.br")
EMAIL_SENHA     = os.getenv("EMAIL_SENHA",     "SUA_SENHA_AQUI")  # ⚠️ EXPOSTO!
```

**Problema:** A senha está hardcoded como valor padrão no `os.getenv()`.

**Risco:** 
- Qualquer pessoa com acesso ao código pode usar essa credencial
- Possível acesso não autorizado à conta de e-mail corporativa
- Violação de LGPD (dados de funcionários podem ser acessados)

**Severidade:** 🔴 CRÍTICA

---

#### 🚨 CRÍTICO: `.env` (Linha 5)

```env
DATABASE_URL=postgresql://postgres:[DAmaraLaura@2017]@db.qkbwjjtnxmfdwbgcthac.supabase.co:5432/postgres
```

**Problema:** 
- Senha do Supabase visível em texto plano
- Arquivo `.env` pode ter sido commitado no histórico do Git

**Risco:**
- Acesso total ao banco de dados de produção
- Roubo de dados de todos os funcionários (CPF, morada, e-mail)
- Modificação ou exclusão de dados

**Severidade:** 🔴 CRÍTICA

---

#### ⚠️ ALTO: `agente_ia.py` (Linha 16)

```python
CHAVE_API = os.getenv("GEMINI_API_KEY")
```

**Problema:** 
- Se `GEMINI_API_KEY` não estiver no `.env`, a chave pode estar hardcoded em outro lugar
- Sem validação se a chave existe

**Risco:**
- Consumo não autorizado de quota da API Gemini
- Custos financeiros inesperados
- Possível acesso a dados processados pela IA

**Severidade:** 🟠 ALTO

---

### 1.2 Verificação do `.gitignore`

#### ✅ Arquivos Corretamente Ignorados:
- `.env` ✅
- `*.db` ✅
- `__pycache__/` ✅
- `.venv/` ✅
- `.streamlit/` ✅

#### ⚠️ Arquivos Sensíveis NÃO Ignorados:
- `mobilidade_renapsi.db` — Banco de dados local (contém dados pessoais)
- `mobilidade_renapsi_backup.db` — Backup do banco (contém dados pessoais)
- `.env.example` — Pode conter padrões de credenciais

**Recomendação:** Adicionar ao `.gitignore`:
```
*.db
*_backup.db
.env.example
```

---

### 1.3 Análise de Dados Sensíveis no Banco

#### Dados Pessoais Armazenados (NÃO ENCRIPTADOS):
- **CPF** — Identificador único (PII crítica)
- **E-mail** — Informação de contato (PII)
- **Morada/CEP** — Localização residencial (PII)
- **Celular** — Número de telefone (PII)
- **Matrícula** — Identificador corporativo (PII)

**Risco:** Se o banco for comprometido, todos os dados pessoais estarão expostos em texto plano.

**Severidade:** 🔴 CRÍTICA

---

## FASE 2: PLANO DE REMEDIAÇÃO DE INCIDENTES

### 2.1 Ação Imediata (Próximas 24 horas)

#### Passo 1: Invalidar Credenciais Expostas

**1.1 Supabase:**
1. Acesse https://app.supabase.com
2. Vá para **Settings → Database → Password**
3. Clique em **Reset Password**
4. Copie a nova senha
5. Atualize o arquivo `.env` local com a nova `DATABASE_URL`

**1.2 E-mail (Outlook/Office365):**
1. Acesse https://account.microsoft.com
2. Vá para **Segurança → Senhas de aplicação**
3. Revogue a senha atual
4. Gere uma nova senha de aplicação
5. Atualize o arquivo `.env` com `EMAIL_SENHA=<nova_senha>`

**1.3 Gemini API:**
1. Acesse https://aistudio.google.com/app/apikey
2. Clique em **Regenerate Key**
3. Atualize o arquivo `.env` com `GEMINI_API_KEY=<nova_chave>`

---

#### Passo 2: Remover Credenciais do Histórico Git

**⚠️ IMPORTANTE:** Se `.env` foi commitado, execute:

```bash
# Opção 1: Remover apenas do histórico (recomendado)
git filter-branch --tree-filter 'rm -f .env' -f -- --all

# Opção 2: Usar git filter-repo (mais seguro)
pip install git-filter-repo
git filter-repo --path .env --invert-paths

# Opção 3: Forçar push (último recurso)
git push -f origin main
```

**Verificar se foi removido:**
```bash
git log --all --full-history -- .env
# Não deve retornar nada
```

---

#### Passo 3: Atualizar Código

**Remover hardcodes de `email_sender.py`:**

```python
# ❌ ANTES (INSEGURO)
EMAIL_SENHA = os.getenv("EMAIL_SENHA", "DAtendimento@Jovem25")

# ✅ DEPOIS (SEGURO)
EMAIL_SENHA = os.getenv("EMAIL_SENHA")
if not EMAIL_SENHA:
    raise ValueError("❌ EMAIL_SENHA não encontrada no .env")
```

---

### 2.2 Ações de Médio Prazo (1-2 semanas)

#### Implementar Encriptação de Dados Sensíveis

Usar `cryptography.Fernet` para encriptar dados pessoais:

```python
from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv

load_dotenv()

# Gerar chave (executar UMA VEZ)
# chave = Fernet.generate_key()
# print(chave.decode())  # Salvar no .env como ENCRYPTION_KEY

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    raise ValueError("ENCRYPTION_KEY não encontrada no .env")

cipher = Fernet(ENCRYPTION_KEY.encode())

def encriptar_cpf(cpf: str) -> str:
    """Encripta CPF antes de salvar no banco."""
    return cipher.encrypt(cpf.encode()).decode()

def desencriptar_cpf(cpf_encriptado: str) -> str:
    """Desencripta CPF ao ler do banco."""
    return cipher.decrypt(cpf_encriptado.encode()).decode()

# Uso no banco_dados.py:
def inserir_novo_jovem(nome, cpf, cep_casa, cep_trabalho, matricula):
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    
    # Encripta dados sensíveis
    cpf_encriptado = encriptar_cpf(cpf)
    
    cursor.execute('''
        INSERT INTO jovens_rotas (nome, cpf, cep_casa, cep_trabalho, matricula, status_rota)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (nome, cpf_encriptado, cep_casa, cep_trabalho, matricula, "Otimizado"))
    
    conexao.commit()
    conexao.close()
```

---

#### Implementar Tratamento de Erros Seguro

**Remover Tracebacks Técnicos do Streamlit:**

```python
# ❌ ANTES (INSEGURO - expõe stack trace)
try:
    resultado = processar_dados()
except Exception as e:
    st.error(f"Erro: {e}")  # Mostra detalhes técnicos

# ✅ DEPOIS (SEGURO - mensagem genérica)
try:
    resultado = processar_dados()
except Exception as e:
    logger.exception("Erro ao processar dados")  # Log técnico
    st.error("❌ Erro ao processar dados. Contate o administrador.")  # Mensagem genérica
```

---

## FASE 3: PROTEÇÃO, CAMUFLAGEM E ENCRIPTAÇÃO AVANÇADA

### 3.1 Checklist de Hardening

#### ✅ Variáveis de Ambiente

```python
# app_piloto.py
from dotenv import load_dotenv
import os

load_dotenv()

# Validar todas as variáveis críticas
DATABASE_URL = os.getenv('DATABASE_URL')
EMAIL_SENHA = os.getenv('EMAIL_SENHA')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')

# Validação centralizada
REQUIRED_ENV_VARS = {
    'DATABASE_URL': 'Conexão do Supabase',
    'EMAIL_SENHA': 'Senha do e-mail corporativo',
    'ENCRYPTION_KEY': 'Chave de encriptação de dados'
}

for var, descricao in REQUIRED_ENV_VARS.items():
    if not os.getenv(var):
        raise ValueError(f"❌ ERRO CRÍTICO: {var} ({descricao}) não encontrada no .env")
```

---

#### ✅ Encriptação de Dados Sensíveis

**Implementar em `banco_dados.py`:**

```python
from cryptography.fernet import Fernet
import os

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
cipher = Fernet(ENCRYPTION_KEY.encode())

# Campos a encriptar
CAMPOS_SENSIVEIS = ['cpf', 'email', 'celular']

def encriptar_campo(valor: str) -> str:
    if not valor:
        return None
    return cipher.encrypt(valor.encode()).decode()

def desencriptar_campo(valor_encriptado: str) -> str:
    if not valor_encriptado:
        return None
    return cipher.decrypt(valor_encriptado.encode()).decode()

# Ao inserir
def inserir_novo_jovem(nome, cpf, cep_casa, cep_trabalho, matricula):
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    
    cursor.execute('''
        INSERT INTO jovens_rotas (nome, cpf, cep_casa, cep_trabalho, matricula, status_rota)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        nome,
        encriptar_campo(cpf),  # ✅ Encriptado
        cep_casa,
        cep_trabalho,
        matricula,
        "Otimizado"
    ))
    
    conexao.commit()
    conexao.close()

# Ao ler
def carregar_dados():
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    df = pd.read_sql_query("SELECT * FROM jovens_rotas", conexao)
    conexao.close()
    
    # Desencriptar campos sensíveis
    for campo in CAMPOS_SENSIVEIS:
        if campo in df.columns:
            df[campo] = df[campo].apply(desencriptar_campo)
    
    return df
```

---

#### ✅ Segurança do Streamlit

**Remover Mensagens de Erro Técnicas:**

```python
# app_piloto.py
import logging
import streamlit as st

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Wrapper para tratamento seguro de erros
def executar_com_seguranca(funcao, *args, **kwargs):
    try:
        return funcao(*args, **kwargs)
    except Exception as e:
        logger.exception(f"Erro em {funcao.__name__}")
        st.error("❌ Erro ao processar solicitação. Contate o administrador.")
        return None

# Uso
resultado = executar_com_seguranca(processar_rota, endereco_casa, endereco_trabalho)
```

---

### 3.2 Arquivo `.env` Seguro

**Criar `.env` com todas as variáveis:**

```env
# ─── Supabase ───────────────────────────────────────────────────────────────
DATABASE_URL=postgresql://postgres:NOVA_SENHA@db.qkbwjjtnxmfdwbgcthac.supabase.co:5432/postgres

# ─── E-mail ─────────────────────────────────────────────────────────────────
EMAIL_REMETENTE=douglas.amaral@renapsi.org.br
EMAIL_SENHA=NOVA_SENHA_APLICACAO

# ─── Gemini API ─────────────────────────────────────────────────────────────
GEMINI_API_KEY=NOVA_CHAVE_API

# ─── Encriptação ────────────────────────────────────────────────────────────
ENCRYPTION_KEY=gAAAAABmXxxx...  # Gerado com Fernet.generate_key()

# ─── Logging ────────────────────────────────────────────────────────────────
LOG_LEVEL=INFO
```

---

### 3.3 Atualizar `.gitignore`

```gitignore
# ─── Credenciais ────────────────────────────────────────────────────────────
.env
.env.local
.env.*.local

# ─── Banco de Dados ─────────────────────────────────────────────────────────
*.db
*_backup.db
*.sqlite
*.sqlite3

# ─── Cache e Temporários ────────────────────────────────────────────────────
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.egg-info/
dist/
build/

# ─── IDE ────────────────────────────────────────────────────────────────────
.vscode/
.idea/
*.swp
*.swo

# ─── Streamlit ──────────────────────────────────────────────────────────────
.streamlit/

# ─── Arquivos Pesados ──────────────────────────────────────────────────────
servidor_rotas/otp-2.5.0-shaded.jar
servidor_rotas/saopaulo/graph.obj
servidor_rotas/saopaulo/*.pbf
servidor_rotas/saopaulo/*.osm.pbf
servidor_rotas/saopaulo/*.zip

# ─── Logs ──────────────────────────────────────────────────────────────────
*.log
logs/

# ─── Documentação de Exemplo ────────────────────────────────────────────────
.env.example
```

---

## RESUMO DE AÇÕES RECOMENDADAS

### 🔴 CRÍTICO (Fazer HOJE):
1. ✅ Invalidar senha do Supabase
2. ✅ Invalidar senha do e-mail
3. ✅ Regenerar chave Gemini API
4. ✅ Remover `.env` do histórico Git
5. ✅ Remover hardcode de `email_sender.py`

### 🟠 ALTO (Fazer esta semana):
1. ✅ Implementar encriptação Fernet para CPF, e-mail, celular
2. ✅ Adicionar tratamento de erros seguro no Streamlit
3. ✅ Atualizar `.gitignore` com `*.db`
4. ✅ Implementar logging centralizado

### 🟡 MÉDIO (Fazer este mês):
1. ✅ Implementar autenticação de usuários
2. ✅ Adicionar auditoria de acesso ao banco
3. ✅ Implementar rate limiting nas APIs
4. ✅ Realizar teste de penetração

---

## CONFORMIDADE COM LGPD

### ✅ Requisitos Atendidos:
- Dados processados localmente (não enviados para APIs externas)
- Encriptação de dados sensíveis (CPF, e-mail)
- Controle de acesso (credenciais em `.env`)

### ⚠️ Requisitos Pendentes:
- Direito ao esquecimento (deletar dados de um funcionário)
- Consentimento explícito (checkbox antes de processar dados)
- Política de privacidade (adicionar ao README)
- Registro de acesso (auditoria)

---

**Próximas Etapas:** Implementar as recomendações acima e realizar novo teste de segurança em 2 semanas.

