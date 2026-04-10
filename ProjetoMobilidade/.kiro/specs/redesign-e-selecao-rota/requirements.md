# Requirements Document

## Introduction

Este documento cobre três demandas integradas para o sistema de gestão de Vale-Transporte da RENAPSI (app_piloto.py):

1. **Melhorias de backend** — corrigir falhas silenciosas, persistência de dados incompleta, geração de coordenadas falsa e falta de validação de entrada.
2. **Redesign visual futurista** — substituir o tema claro atual por uma interface dark/glassmorphism com acentos neon, adequada para demonstração e venda do produto.
3. **Seleção manual de rota** — permitir que o analista substitua a rota sugerida pela IA com uma rota personalizada, salva no banco de dados.

O sistema é uma aplicação Streamlit com backend SQLite, motor de rotas via OSRM/Nominatim e agente de IA via Gemini.

---

## Glossary

- **App**: A aplicação Streamlit (`app_piloto.py`).
- **Analista**: Usuário operador do sistema (RH/Mobilidade).
- **Jovem / Aprendiz**: Registro de aprendiz cadastrado na tabela `jovens_rotas`.
- **Motor_de_Rotas**: Função `motor_de_rotas_gratuito` em `apis.py` que calcula as 3 opções de rota.
- **Agente_IA**: Módulo `agente_ia.py` que consulta o Gemini para análise de rota.
- **Banco_Dados**: Módulo `banco_dados.py` com helpers SQLite.
- **Nominatim**: Serviço de geocodificação OpenStreetMap usado para obter coordenadas reais.
- **Painel_Detalhes**: Tela de visualização de detalhes de um jovem em "Pesquisar Consultas".
- **Override_Manual**: Substituição da rota calculada pelo Motor_de_Rotas por valores definidos pelo Analista.
- **Bilhete**: Tipo de crédito de vale-transporte (ex: Crédito Eletrônico VT Ônibus).
- **Tarifa**: Valor monetário diário (ida e volta) do vale-transporte.
- **CPF**: Cadastro de Pessoa Física — 11 dígitos numéricos.
- **CEP**: Código de Endereçamento Postal — 8 dígitos numéricos.
- **SLA**: Service Level Agreement — tempo de resposta medido em segundos para o cálculo de rota.
- **Logger**: Instância do módulo `logging` do Python usada para registrar erros e eventos.
- **Glassmorphism**: Estilo visual com cards semi-transparentes, blur de fundo e bordas sutis.
- **CartoDB_Dark**: Camada de mapa escuro do provedor CartoDB (`dark_matter`).

---

## Requirements

### Requirement 1: Logging centralizado e tratamento de erros

**User Story:** Como analista, quero que erros do sistema sejam registrados de forma rastreável, para que eu possa diagnosticar falhas sem perder contexto silenciosamente.

#### Acceptance Criteria

1. THE App SHALL inicializar um Logger com nível INFO no módulo principal (`app_piloto.py`) e em cada módulo auxiliar (`apis.py`, `agente_ia.py`, `banco_dados.py`).
2. WHEN uma exceção ocorre em qualquer bloco `except`, THE App SHALL registrar a exceção via `Logger.exception()` com mensagem descritiva antes de retornar o valor de fallback.
3. THE App SHALL substituir todos os blocos `except: pass` e `except Exception: pass` sem log por blocos que chamem `Logger.exception()`.
4. IF o Logger não puder ser inicializado, THEN THE App SHALL encerrar a inicialização com uma mensagem de erro visível no terminal.

---

### Requirement 2: Persistência de `data_ultima_roteirizacao`

**User Story:** Como analista, quero ver a data e hora em que a última rota foi calculada para um jovem, para que eu possa auditar quando a roteirização foi realizada.

#### Acceptance Criteria

1. WHEN o Motor_de_Rotas conclui o cálculo de rota para um jovem, THE Banco_Dados SHALL gravar o timestamp atual no campo `data_ultima_roteirizacao` da linha correspondente em `jovens_rotas`.
2. THE Banco_Dados SHALL garantir que a coluna `data_ultima_roteirizacao` existe na tabela `jovens_rotas` com tipo `TEXT`, criando-a via `ALTER TABLE` se ausente.
3. WHEN o Painel_Detalhes exibe a data da última roteirização, THE App SHALL ler o valor de `data_ultima_roteirizacao` do banco de dados, não de um valor estático ou `session_state`.

---

### Requirement 3: Medição e persistência de SLA

**User Story:** Como analista, quero ver o tempo real de resposta do cálculo de rota, para que o dashboard de SLA reflita dados reais de desempenho.

#### Acceptance Criteria

1. WHEN o Motor_de_Rotas é invocado, THE App SHALL registrar o timestamp de início imediatamente antes da chamada.
2. WHEN o Motor_de_Rotas retorna, THE App SHALL calcular `sla_segundos` como a diferença em segundos entre o timestamp de fim e o de início, com precisão de duas casas decimais.
3. THE Banco_Dados SHALL gravar o valor de `sla_segundos` calculado no campo correspondente da linha do jovem em `jovens_rotas`.
4. THE Banco_Dados SHALL garantir que a coluna `sla_segundos` existe na tabela `jovens_rotas` com tipo `REAL`, criando-a via `ALTER TABLE` se ausente.

---

### Requirement 4: Geocodificação real no modo de edição

**User Story:** Como analista, quero que o botão "Buscar Coordenada Correspondente" retorne coordenadas reais do endereço informado, para que o mapa exiba a localização correta do jovem.

#### Acceptance Criteria

1. WHEN o Analista clica em "Buscar Coordenada Correspondente" no modo de edição, THE App SHALL chamar `obter_coordenadas_reais` do módulo `apis.py` com o endereço composto por CEP, logradouro e número informados.
2. WHEN `obter_coordenadas_reais` retorna coordenadas válidas, THE App SHALL preencher o campo de coordenadas com o valor no formato `"lat, lon"`.
3. IF `obter_coordenadas_reais` retornar `(None, None)`, THEN THE App SHALL exibir uma mensagem de aviso ao Analista informando que o endereço não foi encontrado e manter o campo de coordenadas com o valor anterior.
4. THE App SHALL remover toda geração de coordenadas via `random` do fluxo de edição.

---

### Requirement 5: Validação de CPF

**User Story:** Como analista, quero que o sistema rejeite CPFs inválidos no cadastro, para que a base de dados não contenha registros com identificadores incorretos.

#### Acceptance Criteria

1. WHEN o Analista submete o formulário de cadastro de novo jovem, THE App SHALL verificar que o CPF informado contém exatamente 11 dígitos numéricos.
2. IF o CPF contiver menos ou mais de 11 dígitos numéricos, THEN THE App SHALL exibir a mensagem "CPF deve conter exatamente 11 dígitos numéricos." e bloquear o cadastro.
3. IF todos os 11 dígitos do CPF forem iguais (ex: "11111111111"), THEN THE App SHALL exibir a mensagem "CPF inválido: todos os dígitos são iguais." e bloquear o cadastro.
4. WHEN o CPF passa nas validações de formato, THE App SHALL prosseguir com a verificação de duplicidade já existente via `cpf_ja_existe`.

---

### Requirement 6: Centralização do gerenciamento de conexões SQLite

**User Story:** Como desenvolvedor, quero que todas as conexões com o banco de dados sejam abertas e fechadas pelo módulo `banco_dados.py`, para que não haja conexões SQLite abertas diretamente em `app_piloto.py`.

#### Acceptance Criteria

1. THE Banco_Dados SHALL expor funções para todas as operações de leitura e escrita necessárias pelo App, de modo que `app_piloto.py` não importe `sqlite3` diretamente.
2. THE App SHALL substituir cada bloco `sqlite3.connect(...)` em `app_piloto.py` por chamadas às funções correspondentes do Banco_Dados.
3. THE Banco_Dados SHALL garantir que cada função abre a conexão, executa a operação e fecha a conexão (ou usa context manager `with`) dentro do próprio escopo da função.
4. IF uma operação de banco de dados falhar, THEN THE Banco_Dados SHALL registrar o erro via Logger e propagar a exceção para o chamador.

---

### Requirement 7: Redesign visual — tema dark futurista

**User Story:** Como gestor de produto, quero que a interface tenha aparência futurista e profissional com tema escuro, para que o sistema cause impacto visual positivo em demonstrações e apresentações de venda.

#### Acceptance Criteria

1. THE App SHALL aplicar um tema escuro com cor de fundo principal `#0A0E1A` (ou equivalente dark navy) via `.streamlit/config.toml` e CSS global injetado.
2. THE App SHALL usar as cores de acento: azul elétrico `#00D4FF`, roxo `#7C3AED` e ciano/teal como cores primárias para bordas, destaques e elementos interativos.
3. THE App SHALL renderizar cards de KPI, painéis de rota e painéis de detalhes com estilo glassmorphism: fundo semi-transparente (`rgba`), `backdrop-filter: blur`, e borda sutil com cor de acento.
4. THE App SHALL aplicar efeito de brilho (`box-shadow` com cor neon) nos cards de KPI do Dashboard e nos botões de ação primária.
5. THE App SHALL manter a imagem `logo_renapsi.png` sem alterações de arquivo, posicionamento ou dimensionamento relativo.
6. THE App SHALL redesenhar a sidebar com fundo escuro e estado ativo do menu com borda ou brilho na cor de acento.
7. THE App SHALL aplicar gradiente ou cor de acento nos botões primários (ex: "Pesquisar", "Confirmar", "Recalcular Rota").
8. WHERE o mapa Folium é exibido, THE App SHALL usar a camada de tiles `CartoDB dark_matter` como camada base padrão.
9. THE App SHALL atualizar o painel de análise da IA com borda esquerda e brilho na cor roxa `#7C3AED`.
10. THE App SHALL garantir que todo texto sobre fundos escuros tenha contraste suficiente para leitura (texto claro sobre fundo escuro).

---

### Requirement 8: Seleção manual de rota (Override)

**User Story:** Como analista, quero poder substituir manualmente a rota sugerida pela IA para um jovem, para que eu possa ajustar casos especiais que o algoritmo não cobre adequadamente.

#### Acceptance Criteria

1. WHEN o Painel_Detalhes está em modo de visualização, THE App SHALL exibir um botão "Personalizar Rota" abaixo do painel de opções de trajeto.
2. WHEN o Analista clica em "Personalizar Rota", THE App SHALL exibir um painel de override com os seguintes controles:
   - Seletor de opção de rota: radio ou selectbox com as 3 opções calculadas pelo Motor_de_Rotas mais a opção "Personalizada".
   - Seletor de bilhete: selectbox com as opções "Crédito Eletrônico VT Ônibus", "Crédito Eletrônico VT Metrô/CPTM", "Integração VT", "Nenhum".
   - Campo de tarifa: number input com o valor da opção selecionada pré-preenchido, editável pelo Analista.
3. WHEN o Analista confirma o override, THE Banco_Dados SHALL gravar os valores nos campos `rota_selecionada` (TEXT), `bilhete_selecionado` (TEXT), `tarifa_selecionada` (REAL) e `override_manual` (INTEGER, 1 = ativo) na linha do jovem em `jovens_rotas`.
4. THE Banco_Dados SHALL garantir que as colunas `rota_selecionada`, `bilhete_selecionado`, `tarifa_selecionada` e `override_manual` existem na tabela `jovens_rotas`, criando-as via `ALTER TABLE` se ausentes.
5. WHEN o Painel_Detalhes carrega um jovem com `override_manual = 1`, THE App SHALL exibir os valores de `rota_selecionada`, `bilhete_selecionado` e `tarifa_selecionada` no lugar dos valores calculados pelo Motor_de_Rotas.
6. WHEN um override está ativo, THE App SHALL exibir um indicador visual "🔧 Rota Personalizada pelo Analista" em destaque no painel de resultado.
7. WHEN o Analista clica em "Limpar Override", THE Banco_Dados SHALL gravar `override_manual = 0` e limpar os campos `rota_selecionada`, `bilhete_selecionado` e `tarifa_selecionada` para NULL na linha do jovem.
8. WHEN o override é limpo, THE App SHALL voltar a exibir as opções calculadas pelo Motor_de_Rotas sem indicador de personalização.
9. IF o Analista seleciona uma das 3 opções calculadas no seletor de rota, THEN THE App SHALL pré-preencher automaticamente o campo de bilhete e tarifa com os valores correspondentes daquela opção.
