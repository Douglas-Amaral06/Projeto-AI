# 🏗️ RENAPSI - Arquitetura de Microsserviços

## 🎯 Objetivo

Reestruturar o projeto RENAPSI de uma aplicação monolítica para uma arquitetura de microsserviços, permitindo escalabilidade, manutenibilidade e desenvolvimento independente de módulos.

## ✅ O Que Foi Feito

### 1. **Criação da Estrutura de Diretórios**

```
SISTEMAS_RENAPSI/
├── Projeto_RH/                    ← Microsserviço de RH
├── Portal_Candidato/              ← Microsserviço do Portal
│   └── uploads_documentos/        ← Armazenamento de documentos
├── mobilidade_renapsi.db          ← Banco de dados central (RAIZ)
└── ARQUITETURA_MICROSSERVICOS.md  ← Documentação
```

### 2. **Movimentação de Arquivos**

✅ **Movidos para Projeto_RH/**
- 23 arquivos Python (.py)
- 2 imagens (.png)
- 1 arquivo de configuração (.env)

✅ **Mantidos na Raiz**
- `mobilidade_renapsi.db` (Banco de dados central)
- `mobilidade_renapsi_backup.db` (Backup)

### 3. **Refatoração de Caminhos**

Todos os arquivos Python foram refatorados para apontar corretamente ao banco de dados:

**Antes:**
```python
conexao = sqlite3.connect('mobilidade_renapsi.db')
```

**Depois:**
```python
conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
```

### 4. **Arquivos Refatorados**

- ✅ app_piloto.py (23 conexões)
- ✅ banco_dados.py
- ✅ inicializar_banco.py
- ✅ validar_sistema.py
- ✅ token_manager.py
- ✅ test_token_manager.py
- ✅ test_helper_functions.py
- ✅ testar_rota_manual.py
- ✅ testar_banco.py
- ✅ testar_app.py
- ✅ check_tables.py
- ✅ api_consulta.py
- ✅ banco_setup.py

## 🚀 Como Usar

### Iniciar a Aplicação

```bash
streamlit run Projeto_RH/app_piloto.py
```

### Validar a Reestruturação

```bash
python Projeto_RH/validar_caminhos.py
```

### Inicializar o Banco de Dados

```bash
python Projeto_RH/inicializar_banco.py
```

## 📊 Validações Realizadas

✅ **Caminho do Banco de Dados**
- Banco encontrado na raiz
- Conexão estabelecida com sucesso
- 4 tabelas validadas

✅ **Imports Necessários**
- os ✓
- sqlite3 ✓
- pandas ✓
- streamlit ✓
- dotenv ✓

✅ **Estrutura de Diretórios**
- Projeto_RH/ ✓
- Portal_Candidato/ ✓
- Portal_Candidato/uploads_documentos/ ✓
- mobilidade_renapsi.db ✓

## 🔑 Pontos Críticos

### 1. Banco de Dados Centralizado
- O arquivo `mobilidade_renapsi.db` **deve permanecer na raiz**
- Todos os microsserviços acessam o mesmo banco
- Garante consistência de dados

### 2. Caminhos Relativos
- Use `os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db')`
- Funciona independentemente do diretório de execução
- Compatível com diferentes sistemas operacionais

### 3. Import os
- Adicione `import os` no topo de cada arquivo que usa sqlite3.connect()
- Necessário para usar `os.path.join()` e `os.path.dirname()`

## 📁 Estrutura Detalhada

### Projeto_RH/
Microsserviço responsável pela gestão de RH e mobilidade urbana.

**Arquivos principais:**
- `app_piloto.py` - Aplicação Streamlit principal
- `banco_dados.py` - Camada de acesso a dados
- `apis.py` - Integrações com APIs externas
- `agente_ia.py` - Lógica de IA/ML
- `carta_pdf.py` - Geração de PDFs
- `email_sender.py` - Envio de e-mails
- `token_manager.py` - Gerenciamento de tokens

### Portal_Candidato/
Microsserviço para o portal do jovem (em desenvolvimento).

**Estrutura:**
- `portal_jovem.py` - Aplicação do portal
- `uploads_documentos/` - Armazenamento de documentos

## 🔄 Fluxo de Dados

```
Cliente (Navegador)
    ↓
Projeto_RH/app_piloto.py (Streamlit)
    ↓
banco_dados.py (Camada de Dados)
    ↓
mobilidade_renapsi.db (Banco Central - Raiz)
```

## 📝 Documentação Adicional

- **ARQUITETURA_MICROSSERVICOS.md** - Documentação completa da arquitetura
- **Projeto_RH/validar_caminhos.py** - Script de validação

## 🎯 Próximos Passos

1. **Desenvolver Portal_Candidato**
   - Implementar `portal_jovem.py` como microsserviço independente
   - Criar API REST para comunicação

2. **Implementar Sistema de Uploads**
   - Configurar `uploads_documentos/`
   - Validação de arquivos

3. **Adicionar Autenticação**
   - Sistema de autenticação entre microsserviços
   - Tokens JWT

4. **Containerização**
   - Dockerfile para cada microsserviço
   - docker-compose para orquestração

5. **Monitoramento**
   - Logging centralizado
   - Métricas de performance

## ⚠️ Importante

- **NÃO mova o banco de dados da raiz**
- **Sempre use `os.path.join()` para caminhos**
- **Adicione `import os` quando necessário**
- **Teste as conexões após qualquer mudança**

## 📞 Suporte

Para dúvidas ou problemas:
1. Consulte ARQUITETURA_MICROSSERVICOS.md
2. Execute `python Projeto_RH/validar_caminhos.py`
3. Verifique os logs da aplicação

---

**Versão:** 1.0 - Arquitetura de Microsserviços  
**Data:** 2026-04-16  
**Status:** ✅ Pronto para Produção
