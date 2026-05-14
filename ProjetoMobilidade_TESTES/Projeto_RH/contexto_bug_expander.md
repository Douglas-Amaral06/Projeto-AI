# Contexto do Bug Visual no st.expander

## 1. O Ambiente
- **Framework:** Streamlit
- **Tema configurado:** `base="light"` no arquivo `config.toml`.
- **CSS Atual:** Temos um CSS global otimizado de ~88 linhas que usa seletores `[data-baseweb="*"]` para padronizar os componentes nativos do Streamlit.

## 2. O Problema
Na tela de Auditoria/Compliance, temos o seguinte componente:
`with st.expander("⚡ Ver Detalhes das Contestações"):`

Este componente está com um conflito grave de CSS no seu cabeçalho (a barra clicável, tag `<summary>`):
- **Estado Normal (Bugado):** Fundo escuro e texto escuro (ilegível).
- **Estado Hover (Mouse em cima - Funcionando):** Fundo branco e texto legível.

## 3. O que já tentamos (e falhou)
Tentamos injetar CSS localmente usando `st.markdown(..., unsafe_allow_html=True)` logo acima do expander para forçar o fundo branco. Exemplo do que tentamos:
`div[data-testid="stExpander"] details summary { background-color: #FFFFFF !important; color: #333333 !important; }`
**Resultado:** O Streamlit ignorou ou sobrescreveu essa regra no estado normal, mantendo o fundo escuro.

## 4. Onde está o erro
O problema não está no código Python do expander, mas sim no **CSS Global** do nosso projeto ou em como o Streamlit lida com as classes `.st-emotion-cache` desse componente específico em contraste com as nossas regras globais. O nosso CSS global atual deve estar forçando um `background` ou `color` escuro para `divs` genéricas ou para o estado não-hover de botões/summarys.

## 5. Requisitos para a Solução
1. Você não deve me dar soluções de CSS local (inline) para colocar no arquivo da tela.
2. Você deve analisar o nosso arquivo principal onde o CSS global está sendo injetado.
3. Você deve encontrar a regra exata que está "vazando" para o expander e causando o fundo escuro.
4. Você deve gerar o bloco de CSS global corrigido, utilizando alta especificidade para garantir que o `st.expander` (especificamente o `<summary>`) respeite o tema claro padrão do projeto no seu estado normal, sem quebrar o resto do site.