# Design Document — redesign-e-selecao-rota

## Overview

Este documento descreve a arquitetura e os detalhes de implementação para três melhorias integradas no sistema de gestão de Vale-Transporte da RENAPSI:

1. **Backend hardening** — logging centralizado, persistência completa de SLA e data de roteirização, geocodificação real no modo de edição, validação de CPF e centralização de conexões SQLite.
2. **Redesign visual futurista** — tema dark/glassmorphism com acentos neon, mapa CartoDB dark, painel de IA com borda roxa.
3. **Override manual de rota** — painel de personalização de rota com persistência no banco de dados e indicador visual de rota personalizada.

O sistema é uma aplicação Streamlit single-page (`app_piloto.py`) com backend SQLite, motor de rotas via OSRM/Nominatim (`apis.py`) e agente de IA via Gemini (`agente_ia.py`).

---

## Architecture

### Visão Geral dos Módulos

```
┌─────────────────────────────────────────────────────────────┐
│                      app_piloto.py                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Dashboard   │  │  Pesquisar   │  │  Cadastrar Jovem │  │
│  │  Principal   │  │  Consultas   │  │                  │  │
│  └──────────────┘  └──────┬───────┘  └────────┬─────────┘  │
│                           │                   │             │
│              ┌────────────▼───────────────────▼──────────┐  │
│              │         banco_dados.py (centralizado)      │  │
│              │  buscar_jovem_por_id / cpf / nome / mat    │  │
│              │  salvar_roteirizacao / override / limpar   │  │
│              │  carregar_contestacoes                     │  │
│              └────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         │                          │
         ▼                          ▼
    apis.py                   agente_ia.py
  motor_de_rotas_gratuito()  analisar_rota_com_ia()
  obter_coordenadas_reais()
  buscar_endereco_viacep()
```

### Fluxo de Roteirização com SLA

```
app_piloto.py (Painel_Detalhes)
  │
  ├─ t_inicio = time.perf_counter()
  ├─ resultado = motor_de_rotas_gratuito(end_casa, end_trab)   ← apis.py
  ├─ t_fim = time.perf_counter()
  ├─ sla = round(t_fim - t_inicio, 2)
  └─ banco_dados.salvar_roteirizacao(id_jovem, sla)
       └─ UPDATE jovens_rotas SET sla_segundos=?, data_ultima_roteirizacao=? WHERE id=?
```

### Fluxo de Override Manual

```
Painel_Detalhes (modo visualização)
  │
  ├─ [override_manual == 1] → exibe valores do override + badge "🔧 Rota Personalizada"
  ├─ [override_manual == 0] → exibe rotas calculadas pelo Motor_de_Rotas
  │
  └─ st.expander("🔧 Personalizar Rota")
       ├─ st.radio(opções calculadas + "Personalizada")
       ├─ st.selectbox(bilhete)
       ├─ st.number_input(tarifa)
       ├─ [Confirmar] → banco_dados.salvar_override_rota(id, rota, bilhete, tarifa)
       └─ [Limpar Override] → banco_dados.limpar_override_rota(id)
```

---

## Components and Interfaces

### 1. Logging — Padrão por Módulo

Cada módulo inicializa seu próprio logger no topo do arquivo:

```python
import logging
logger = logging.getLogger(__name__)
```

Todos os blocos `except` passam a usar:

```python
except Exception:
    logger.exception("Descrição do contexto onde o erro ocorreu")
    return <valor_de_fallback>
```

Módulos afetados: `app_piloto.py`, `apis.py`, `agente_ia.py`, `banco_dados.py`.

### 2. Validação de CPF — `validar_cpf(cpf: str) -> tuple[bool, str]`

Função pura em `banco_dados.py` (ou inline em `app_piloto.py`):

```python
def validar_cpf(cpf: str) -> tuple[bool, str]:
    digitos = ''.join(filter(str.isdigit, cpf))
    if len(digitos) != 11:
        return False, "CPF deve conter exatamente 11 dígitos numéricos."
    if len(set(digitos)) == 1:
        return False, "CPF inválido: todos os dígitos são iguais."
    return True, ""
```

### 3. Geocodificação Real no Modo de Edição

Substituição do bloco `random.randint` em `app_piloto.py`:

```python
# ANTES (remover):
st.session_state.coord_temp = f"-23.{random.randint(...)}, -46.{random.randint(...)}"

# DEPOIS:
endereco_busca = f"{cep_input} {rua_input} {num_input}, São Paulo"
lat, lon = obter_coordenadas_reais(endereco_busca)
if lat is not None:
    st.session_state.coord_temp = f"{lat}, {lon}"
else:
    st.warning("Endereço não encontrado. Verifique o CEP e número informados.")
```

### 4. Novas Funções em `banco_dados.py`

#### Funções de Leitura

```python
def buscar_jovem_por_id(id_jovem: int) -> dict | None
def buscar_jovem_por_cpf(cpf: str) -> pd.DataFrame
def buscar_jovem_por_nome(nome: str) -> pd.DataFrame
def buscar_jovem_por_matricula(matricula: str) -> pd.DataFrame
def carregar_contestacoes() -> pd.DataFrame
```

#### Funções de Escrita

```python
def salvar_roteirizacao(id_jovem: int, sla_segundos: float) -> None
    # UPDATE jovens_rotas SET sla_segundos=?, data_ultima_roteirizacao=? WHERE id=?
    # data_ultima_roteirizacao = datetime.now().strftime("%d/%m/%Y às %Hh%Mm")

def salvar_override_rota(id_jovem: int, rota: str, bilhete: str, tarifa: float) -> None
    # UPDATE jovens_rotas SET rota_selecionada=?, bilhete_selecionado=?,
    #   tarifa_selecionada=?, override_manual=1 WHERE id=?

def limpar_override_rota(id_jovem: int) -> None
    # UPDATE jovens_rotas SET rota_selecionada=NULL, bilhete_selecionado=NULL,
    #   tarifa_selecionada=NULL, override_manual=0 WHERE id=?
```

#### Migração de Schema — `atualizar_banco_geral()` (expandida)

```python
colunas_novas = [
    ("data_ultima_roteirizacao", "TEXT"),
    ("sla_segundos", "REAL"),
    ("rota_selecionada", "TEXT"),
    ("bilhete_selecionado", "TEXT"),
    ("tarifa_selecionada", "REAL"),
    ("override_manual", "INTEGER DEFAULT 0"),
    # ... colunas já existentes
]
```

### 5. Medição de SLA em `app_piloto.py`

```python
import time

t_inicio = time.perf_counter()
rota = motor_de_rotas_gratuito(end_completo_casa, end_completo_trab)
t_fim = time.perf_counter()
sla_segundos = round(t_fim - t_inicio, 2)

st.session_state.rota_gerada = rota
salvar_roteirizacao(id_selecionado, sla_segundos)
```

### 6. Override Manual — UI em `app_piloto.py`

```python
# Abaixo das abas de trajeto, no modo de visualização:
with st.expander("🔧 Personalizar Rota"):
    opcoes_rota = [r["modal"] for r in rotas] + ["Personalizada"]
    opcao_sel = st.radio("Selecionar opção de rota:", opcoes_rota,
                         key="override_opcao")

    # Auto-fill quando opção calculada é selecionada
    bilhete_default = ""
    tarifa_default = 0.0
    if opcao_sel != "Personalizada":
        idx = opcoes_rota.index(opcao_sel)
        bilhete_default = rotas[idx]["bilhete"]
        tarifa_default = rotas[idx]["valor_diario"]

    bilhete_sel = st.selectbox("Bilhete:", [
        "Crédito Eletrônico VT Ônibus",
        "Crédito Eletrônico VT Metrô/CPTM",
        "Integração VT",
        "Nenhum"
    ], index=..., key="override_bilhete")

    tarifa_sel = st.number_input("Tarifa diária (R$):",
                                  min_value=0.0, step=0.01,
                                  value=tarifa_default,
                                  key="override_tarifa")

    col_conf, col_limpar = st.columns(2)
    with col_conf:
        if st.button("Confirmar Personalização", type="primary"):
            salvar_override_rota(id_selecionado, opcao_sel, bilhete_sel, tarifa_sel)
            st.rerun()
    with col_limpar:
        if st.button("Limpar Override"):
            limpar_override_rota(id_selecionado)
            st.rerun()
```

---

## Data Models

### Tabela `jovens_rotas` — Colunas Novas

| Coluna                   | Tipo    | Default | Descrição                                      |
|--------------------------|---------|---------|------------------------------------------------|
| `data_ultima_roteirizacao` | TEXT  | NULL    | Timestamp da última execução do Motor_de_Rotas |
| `sla_segundos`           | REAL    | NULL    | Tempo de resposta do Motor_de_Rotas em segundos |
| `rota_selecionada`       | TEXT    | NULL    | Modal da rota escolhida no override             |
| `bilhete_selecionado`    | TEXT    | NULL    | Tipo de bilhete do override                     |
| `tarifa_selecionada`     | REAL    | NULL    | Valor diário do override                        |
| `override_manual`        | INTEGER | 0       | Flag: 1 = override ativo, 0 = rota calculada   |

Todas as colunas são adicionadas via `ALTER TABLE ... ADD COLUMN` com tratamento de `OperationalError` para idempotência.

### Tabela `contestacoes` — Sem Alterações

Mantida como está. Acesso migrado para `carregar_contestacoes()` em `banco_dados.py`.

---

## Visual Design System

### Tema — `.streamlit/config.toml`

```toml
[theme]
primaryColor = "#00D4FF"
backgroundColor = "#0A0E1A"
secondaryBackgroundColor = "#0D1117"
textColor = "#E2E8F0"
font = "sans serif"
```

### Paleta de Cores CSS

```css
:root {
  --bg-primary:    #0A0E1A;
  --bg-secondary:  #0D1117;
  --bg-card:       rgba(13, 17, 23, 0.8);
  --accent-blue:   #00D4FF;
  --accent-purple: #7C3AED;
  --accent-orange: #FF6B35;
  --border-glow:   rgba(0, 212, 255, 0.3);
  --text-primary:  #E2E8F0;
  --text-muted:    #94A3B8;
}
```

### CSS Global Injetado em `app_piloto.py`

```python
st.markdown("""
<style>
/* Reset e base */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Sidebar dark */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0D1117 0%, #0A0E1A 100%);
    border-right: 1px solid rgba(0, 212, 255, 0.15);
}
[data-testid="stSidebar"] .stRadio label {
    color: #94A3B8;
    transition: color 0.2s;
}
[data-testid="stSidebar"] .stRadio label:hover {
    color: #00D4FF;
}

/* KPI cards */
div[data-testid="metric-container"] {
    background: linear-gradient(135deg,
        rgba(0, 212, 255, 0.1),
        rgba(124, 58, 237, 0.1));
    border: 1px solid rgba(0, 212, 255, 0.3);
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 0 20px rgba(0, 212, 255, 0.15);
}

/* Glassmorphism cards genéricos */
.glass-card {
    background: rgba(13, 17, 23, 0.8);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(0, 212, 255, 0.2);
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
}

/* Botões primários */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #00D4FF, #7C3AED);
    border: none;
    color: #0A0E1A;
    font-weight: bold;
    border-radius: 8px;
    box-shadow: 0 0 15px rgba(0, 212, 255, 0.4);
    transition: box-shadow 0.2s;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 0 25px rgba(0, 212, 255, 0.7);
}

/* Headings */
h1, h2, h3 {
    color: #E2E8F0;
}

/* Painel IA */
.ia-panel {
    background: rgba(124, 58, 237, 0.08);
    border-left: 4px solid #7C3AED;
    border-radius: 0 8px 8px 0;
    padding: 16px;
    box-shadow: -4px 0 20px rgba(124, 58, 237, 0.3);
}

/* Badge override */
.badge-override {
    background: linear-gradient(135deg, #FF6B35, #FF4500);
    color: white;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: bold;
    box-shadow: 0 0 12px rgba(255, 107, 53, 0.5);
}
</style>
""", unsafe_allow_html=True)
```

### Mapa Folium — Dark Matter

```python
m = folium.Map(
    location=[(lat_c + lat_t) / 2, (lon_c + lon_t) / 2],
    zoom_start=12,
    control_scale=True
)
folium.TileLayer('CartoDB dark_matter').add_to(m)
```

### Painel de Análise da IA — Atualizado

```python
st.markdown(f"""
<div class="ia-panel">
    <h4 style="margin-top:0; color:#A78BFA; font-size:16px;">
        🤖 Análise do Agente de Inteligência Artificial
    </h4>
    <p style="margin:0; color:#CBD5E1; font-size:14px; line-height:1.6;">
        {st.session_state.analise_ia}
    </p>
</div>
""", unsafe_allow_html=True)
```

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Logging de exceções em funções de banco de dados

*For any* função em `banco_dados.py` que realiza operações SQLite, quando a operação lança uma exceção, `logger.exception` deve ser chamado antes de propagar ou retornar o fallback.

**Validates: Requirements 1.2, 6.4**

---

### Property 2: Round-trip de roteirização persiste SLA e timestamp

*For any* ID de jovem válido e valor de `sla_segundos`, após chamar `salvar_roteirizacao(id, sla)`, a consulta `buscar_jovem_por_id(id)` deve retornar `sla_segundos` igual ao valor salvo e `data_ultima_roteirizacao` não nulo.

**Validates: Requirements 2.1, 3.3**

---

### Property 3: Precisão do SLA calculado

*For any* par de timestamps `t_inicio` e `t_fim` com `t_fim >= t_inicio`, o valor `sla = round(t_fim - t_inicio, 2)` deve satisfazer `round(sla, 2) == sla` (precisão de 2 casas decimais) e `sla >= 0`.

**Validates: Requirements 3.1, 3.2**

---

### Property 4: Formatação de coordenadas reais

*For any* par `(lat, lon)` retornado por `obter_coordenadas_reais` com valores não nulos, a string formatada `f"{lat}, {lon}"` deve ser parseável de volta para os mesmos valores float via `extrair_coordenadas`.

**Validates: Requirements 4.2**

---

### Property 5: Validação de CPF — comprimento

*For any* string `s`, `validar_cpf(s)` deve retornar `(False, mensagem)` se e somente se o número de dígitos numéricos em `s` for diferente de 11.

**Validates: Requirements 5.1, 5.2**

---

### Property 6: Validação de CPF — dígitos iguais

*For any* dígito `d` em `"0123456789"`, `validar_cpf(d * 11)` deve retornar `(False, "CPF inválido: todos os dígitos são iguais.")`.

**Validates: Requirements 5.3**

---

### Property 7: Round-trip de override manual

*For any* ID de jovem válido e combinação `(rota, bilhete, tarifa)`, após chamar `salvar_override_rota(id, rota, bilhete, tarifa)`, a consulta `buscar_jovem_por_id(id)` deve retornar `rota_selecionada == rota`, `bilhete_selecionado == bilhete`, `tarifa_selecionada == tarifa` e `override_manual == 1`.

**Validates: Requirements 8.3**

---

### Property 8: Limpeza de override restaura estado neutro

*For any* ID de jovem com override ativo (`override_manual == 1`), após chamar `limpar_override_rota(id)`, a consulta `buscar_jovem_por_id(id)` deve retornar `override_manual == 0` e `rota_selecionada`, `bilhete_selecionado`, `tarifa_selecionada` todos `NULL`.

**Validates: Requirements 8.7**

---

### Property 9: Auto-fill de bilhete e tarifa ao selecionar opção calculada

*For any* lista de rotas calculadas pelo `motor_de_rotas_gratuito` e qualquer índice `i` válido, selecionar a opção `rotas[i]["modal"]` no seletor de override deve resultar em `bilhete_default == rotas[i]["bilhete"]` e `tarifa_default == rotas[i]["valor_diario"]`.

**Validates: Requirements 8.9**

---

## Error Handling

### Estratégia Geral

| Camada         | Falha                              | Comportamento                                              |
|----------------|------------------------------------|------------------------------------------------------------|
| `apis.py`      | Nominatim timeout / erro HTTP      | `logger.exception(...)`, retorna `(None, None)`            |
| `apis.py`      | OSRM indisponível                  | `logger.exception(...)`, usa fallback `10.0 km / 30 min`  |
| `apis.py`      | ViaCEP erro                        | `logger.exception(...)`, retorna `"Endereço não encontrado"` |
| `banco_dados.py` | `sqlite3.OperationalError` em ALTER | Silenciado (idempotência de migração)                    |
| `banco_dados.py` | Qualquer outra exceção SQLite     | `logger.exception(...)`, propaga exceção                  |
| `agente_ia.py` | Gemini API erro                    | `logger.exception(...)`, retorna mensagem de erro legível |
| `app_piloto.py` | `obter_coordenadas_reais` → None  | `st.warning(...)`, mantém coordenada anterior             |
| `app_piloto.py` | CPF inválido no cadastro           | `st.error(...)`, bloqueia submissão do formulário         |

### Tratamento de Override com Rota Não Calculada

Se o Painel_Detalhes carregar um jovem com `override_manual == 1` mas `rota_gerada` ainda não estiver em `session_state`, o app deve exibir os valores do override diretamente do banco sem tentar acessar `rota_gerada["rotas"]`.

---

## Testing Strategy

### Abordagem Dual

O projeto usa duas camadas complementares de testes:

- **Testes unitários com exemplos**: verificam comportamentos específicos, casos de borda e integrações entre componentes.
- **Testes baseados em propriedades (PBT)**: verificam propriedades universais sobre funções puras e operações de banco de dados, usando a biblioteca [Hypothesis](https://hypothesis.readthedocs.io/) para Python.

### Testes de Propriedade (Hypothesis)

Cada propriedade do documento deve ser implementada como um teste Hypothesis com mínimo de 100 iterações. Formato de tag:

```
# Feature: redesign-e-selecao-rota, Property N: <texto da propriedade>
```

| Propriedade | Função testada                        | Estratégia Hypothesis                                      |
|-------------|---------------------------------------|------------------------------------------------------------|
| Property 1  | Funções de `banco_dados.py`           | `@given(st.integers())` + mock `sqlite3` para lançar erro  |
| Property 2  | `salvar_roteirizacao` + `buscar_jovem_por_id` | `@given(st.integers(min_value=1), st.floats(min_value=0))` |
| Property 3  | Cálculo de SLA                        | `@given(st.floats(min_value=0), st.floats(min_value=0))`   |
| Property 4  | `obter_coordenadas_reais` + `extrair_coordenadas` | `@given(st.floats(-90,90), st.floats(-180,180))` |
| Property 5  | `validar_cpf`                         | `@given(st.text())`                                        |
| Property 6  | `validar_cpf`                         | `@given(st.sampled_from("0123456789"))`                    |
| Property 7  | `salvar_override_rota` + `buscar_jovem_por_id` | `@given(st.text(), st.text(), st.floats(min_value=0))` |
| Property 8  | `limpar_override_rota` + `buscar_jovem_por_id` | `@given(st.integers(min_value=1))`                   |
| Property 9  | Lógica de auto-fill do override       | `@given(st.integers(min_value=0, max_value=2))`            |

### Testes Unitários com Exemplos

- `validar_cpf("")` → `(False, "CPF deve conter exatamente 11 dígitos numéricos.")`
- `validar_cpf("12345678901")` → `(True, "")`
- `validar_cpf("11111111111")` → `(False, "CPF inválido: todos os dígitos são iguais.")`
- `obter_coordenadas_reais` com endereço inválido → `(None, None)`
- `buscar_jovem_por_id` com ID inexistente → `None`
- Painel_Detalhes com `override_manual=1` exibe badge "🔧 Rota Personalizada pelo Analista"
- Painel_Detalhes com `override_manual=0` exibe abas de rotas calculadas

### Testes de Smoke (Configuração)

- `config.toml` contém `backgroundColor = "#0A0E1A"`
- Módulos `app_piloto`, `apis`, `agente_ia`, `banco_dados` possuem atributo `logger`
- Tabela `jovens_rotas` contém colunas `data_ultima_roteirizacao`, `sla_segundos`, `rota_selecionada`, `bilhete_selecionado`, `tarifa_selecionada`, `override_manual` após `atualizar_banco_geral()`
- `app_piloto.py` não contém chamadas diretas a `sqlite3.connect`
