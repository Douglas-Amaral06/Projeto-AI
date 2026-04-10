# Requirements Document

## Introduction

Este documento descreve os requisitos para a feature **Roteirização Real SP**, que substitui o motor de rotas simulado (`motor_de_rotas_gratuito()` em `apis.py`) por um motor real integrado ao OpenTripPlanner (OTP) local, alimentado pelo GTFS oficial da SPTrans e pelo mapa OSM de São Paulo. A feature também aprimora o agente de IA (Gemini) para receber dados reais de rotas, e corrige os scripts PowerShell de setup do OTP para funcionarem a partir de qualquer diretório.

O sistema existente é um app Streamlit de gestão de Vale-Transporte para aprendizes em São Paulo. Atualmente, as rotas retornadas são fictícias (tempos e linhas aleatórios). Com esta feature, o sistema passará a exibir linhas de ônibus reais (ex: "8012-10 SPTrans"), estações de metrô reais, tempos de viagem reais e tarifas baseadas nos dados oficiais da SPTrans.

---

## Glossary

- **OTP**: OpenTripPlanner — servidor de roteirização multimodal open-source que consome GTFS e OSM para calcular rotas reais de transporte público.
- **GTFS**: General Transit Feed Specification — formato padrão de dados de transporte público. O arquivo `google_transit.zip` da SPTrans contém linhas, paradas, horários e tarifas reais de São Paulo.
- **OSM**: OpenStreetMap — mapa geográfico aberto usado pelo OTP para calcular trechos a pé e de bicicleta.
- **Motor_OTP**: Módulo Python responsável por consultar a API REST do OTP local e transformar a resposta em estrutura de dados compatível com o sistema existente.
- **Agente_IA**: Módulo `agente_ia.py` que usa a API Gemini para analisar rotas e recomendar a melhor opção.
- **Nominatim**: Serviço de geocodificação do OpenStreetMap, já utilizado em `apis.py` para converter endereços em coordenadas.
- **OSRM**: Serviço externo de roteamento de carro, atualmente usado em `apis.py` apenas para calcular distância em km.
- **SPTrans**: São Paulo Transporte — operadora do sistema de ônibus municipal de São Paulo.
- **GTFS_Fare**: Arquivos `fare_attributes.txt` e `fare_rules.txt` dentro do `google_transit.zip` que definem as tarifas oficiais por linha/agência.
- **Grafo_OTP**: Arquivo `graph.obj` gerado pelo OTP ao processar o GTFS + OSM, necessário para que o servidor de rotas funcione.
- **Setup_Script**: Scripts PowerShell (`setup_otp.ps1`, `start_otp.ps1`) responsáveis por baixar o OSM, construir o grafo e iniciar o servidor OTP.
- **Itinerary**: Objeto retornado pela API do OTP representando uma opção de rota completa, contendo múltiplos `legs` (trechos).
- **Leg**: Trecho individual de uma rota (ex: caminhada até o ponto, ônibus da linha X, metrô da linha Y).
- **Vale_Transporte**: Benefício trabalhista que cobre o custo de transporte público do empregado. O sistema calcula o valor diário (ida + volta).

---

## Requirements

### Requirement 1: Setup do Ambiente OTP Funcional

**User Story:** Como desenvolvedor, quero executar os scripts de setup do OTP a partir de qualquer diretório do sistema, para que o ambiente de roteirização seja configurado sem erros de caminho.

#### Acceptance Criteria

1. THE Setup_Script SHALL localizar automaticamente o diretório `servidor_rotas/` relativo à raiz do projeto, independentemente do diretório de trabalho atual do PowerShell.
2. WHEN o script `setup_otp.ps1` é executado, THE Setup_Script SHALL baixar o arquivo OSM de São Paulo (via BBBike ou Geofabrik) para o diretório `servidor_rotas/saopaulo/`.
3. WHEN o arquivo OSM e o `google_transit.zip` estão presentes em `servidor_rotas/saopaulo/`, THE Setup_Script SHALL executar o OTP com o parâmetro `--buildAndExit` para gerar o `graph.obj`.
4. WHEN o `graph.obj` já existe em `servidor_rotas/saopaulo/`, THE Setup_Script SHALL pular a etapa de build e exibir mensagem informando que o grafo já está construído.
5. IF o Java não estiver instalado ou não for encontrado no PATH, THEN THE Setup_Script SHALL exibir mensagem de erro clara indicando a versão mínima requerida (Java 11+) e encerrar com código de saída não-zero.
6. WHEN o script `start_otp.ps1` é executado, THE Setup_Script SHALL iniciar o servidor OTP na porta 8080 usando o `graph.obj` existente.
7. IF o `graph.obj` não existir quando `start_otp.ps1` for executado, THEN THE Setup_Script SHALL exibir mensagem orientando o usuário a executar `setup_otp.ps1` primeiro.

---

### Requirement 2: Motor de Rotas Real via OTP

**User Story:** Como analista de RH, quero que o sistema calcule rotas reais de transporte público em São Paulo, para que o Vale-Transporte dos aprendizes seja calculado com base em linhas e tempos reais.

#### Acceptance Criteria

1. THE Motor_OTP SHALL expor uma função `motor_de_rotas_otp(end_casa, end_trab)` com a mesma assinatura de retorno que a função `motor_de_rotas_gratuito()` existente, garantindo compatibilidade com `app_piloto.py`.
2. WHEN `motor_de_rotas_otp()` é chamado com dois endereços válidos em São Paulo, THE Motor_OTP SHALL consultar a API REST do OTP local em `http://localhost:8080/otp/routers/default/plan`.
3. WHEN o OTP retorna itinerários válidos, THE Motor_OTP SHALL extrair até 3 opções de rota distintas por modal predominante (ônibus, metrô/CPTM, integração ônibus+metrô).
4. WHEN uma rota contém trechos de transporte público, THE Motor_OTP SHALL incluir no campo `trajeto` o nome real da linha (ex: "Ônibus 8012-10 SPTrans" ou "Metrô Linha 2-Verde").
5. WHEN uma rota contém múltiplos trechos de transporte público, THE Motor_OTP SHALL listar todas as linhas utilizadas no campo `trajeto`, separadas por " → ".
6. THE Motor_OTP SHALL calcular o tempo total de viagem em minutos a partir do campo `duration` retornado pelo OTP, sem estimativas aleatórias.
7. WHEN o OTP retorna menos de 3 itinerários distintos por modal, THE Motor_OTP SHALL preencher as opções faltantes com os dados simulados do `motor_de_rotas_gratuito()` como fallback, marcando-as com sufixo "(estimado)".
8. IF o servidor OTP não estiver acessível em `http://localhost:8080`, THEN THE Motor_OTP SHALL retornar os dados do `motor_de_rotas_gratuito()` como fallback e registrar um aviso no log do sistema.
9. THE Motor_OTP SHALL retornar as coordenadas reais de origem e destino obtidas via Nominatim, mantendo o campo `coords_reais` no formato `[(lat_c, lon_c), (lat_t, lon_t)]`.

---

### Requirement 3: Tarifas e Bilhetes Reais

**User Story:** Como analista de RH, quero que o sistema exiba as tarifas e tipos de bilhete corretos para cada rota, para que o cálculo do Vale-Transporte reflita o custo real do deslocamento.

#### Acceptance Criteria

1. THE Motor_OTP SHALL extrair as tarifas do GTFS (`fare_attributes.txt`, `fare_rules.txt`) contido em `servidor_rotas/saopaulo/google_transit.zip` durante a inicialização do módulo.
2. WHEN uma rota contém apenas trechos de ônibus SPTrans, THE Motor_OTP SHALL aplicar a tarifa de ônibus municipal vigente (R$ 5,82) e definir o campo `bilhete` como "Crédito Eletrônico VT (Ônibus SPTrans)".
3. WHEN uma rota contém apenas trechos de metrô ou CPTM, THE Motor_OTP SHALL aplicar a tarifa metroferroviária vigente (R$ 5,92) e definir o campo `bilhete` como "Crédito Eletrônico VT (Metrô/CPTM)".
4. WHEN uma rota contém integração ônibus + metrô/CPTM, THE Motor_OTP SHALL aplicar a tarifa de integração vigente (R$ 11,32) e definir o campo `bilhete` como "Integração VT (Ônibus + Metrô/CPTM)".
5. THE Motor_OTP SHALL calcular o `valor_diario` multiplicando a tarifa aplicável por 2 (ida e volta).
6. WHEN os arquivos de tarifa GTFS não estiverem disponíveis ou não puderem ser lidos, THE Motor_OTP SHALL utilizar a tabela de tarifas hardcoded existente em `apis.py` como fallback.
7. THE Motor_OTP SHALL incluir no campo `info_tarifas` a fonte dos dados de tarifa utilizada (ex: "GTFS SPTrans 2025" ou "Tabela fixa 2026").

---

### Requirement 4: Agente de IA com Dados Reais

**User Story:** Como analista de RH, quero que o agente de IA analise as rotas com base em dados reais de linhas e tempos, para que a recomendação seja precisa e confiável.

#### Acceptance Criteria

1. WHEN `analisar_rota_com_ia()` é chamado com dados provenientes do Motor_OTP, THE Agente_IA SHALL incluir no prompt os nomes reais das linhas de transporte de cada opção de rota.
2. WHEN uma rota possui múltiplos trechos, THE Agente_IA SHALL incluir no prompt o número de transferências necessárias para cada opção.
3. WHEN os dados de rota incluem tempo de caminhada, THE Agente_IA SHALL incluir no prompt o tempo total de caminhada em minutos para cada opção.
4. THE Agente_IA SHALL indicar explicitamente no prompt quando uma opção de rota é baseada em dados reais do OTP versus dados estimados (fallback).
5. WHEN o Agente_IA recebe dados reais do OTP, THE Agente_IA SHALL produzir uma análise que mencione pelo menos uma linha de transporte real pelo nome na recomendação final.
6. IF a chave da API Gemini não estiver configurada, THEN THE Agente_IA SHALL retornar a mensagem de aviso existente sem alterações.

---

### Requirement 5: Exibição de Rotas Reais no Frontend

**User Story:** Como analista de RH, quero visualizar as linhas de ônibus e metrô reais no painel de resultados, para que eu possa validar a rota do aprendiz com informações concretas.

#### Acceptance Criteria

1. WHEN uma rota real é calculada pelo Motor_OTP, THE App_Piloto SHALL exibir o nome real da linha no campo "Trajeto" de cada aba de opção de rota.
2. WHEN uma rota possui múltiplos trechos de transporte público, THE App_Piloto SHALL exibir cada linha separada por " → " no campo "Trajeto".
3. WHEN uma opção de rota é baseada em dados estimados (fallback), THE App_Piloto SHALL exibir o sufixo "(estimado)" junto ao nome do modal.
4. THE App_Piloto SHALL exibir o tempo de viagem real em minutos conforme retornado pelo OTP, sem arredondamentos arbitrários.
5. WHEN o servidor OTP não está disponível, THE App_Piloto SHALL exibir um aviso visual informando que as rotas exibidas são estimativas, sem interromper o fluxo do usuário.
6. THE App_Piloto SHALL manter o mapa Folium existente com os marcadores de Casa (C) e Trabalho (T) e a linha reta entre eles, independentemente da fonte dos dados de rota.

---

### Requirement 6: Compatibilidade e Não-Regressão

**User Story:** Como desenvolvedor, quero que a integração com o OTP não quebre nenhuma funcionalidade existente do sistema, para que o app continue funcionando mesmo quando o OTP não estiver rodando.

#### Acceptance Criteria

1. THE Motor_OTP SHALL ser importado em `apis.py` de forma que a função `motor_de_rotas_gratuito()` original permaneça disponível como fallback sem alterações em sua assinatura.
2. WHEN o Motor_OTP é importado, THE Motor_OTP SHALL verificar a disponibilidade do servidor OTP de forma assíncrona, sem bloquear a inicialização do módulo.
3. THE App_Piloto SHALL continuar funcionando normalmente (usando fallback) quando o servidor OTP não estiver em execução.
4. WHEN o banco de dados SQLite é consultado, THE App_Piloto SHALL continuar usando as funções existentes de `banco_dados.py` sem modificações na estrutura das tabelas.
5. THE Motor_OTP SHALL ser implementado em um novo arquivo `otp_client.py`, sem modificar a estrutura interna da função `motor_de_rotas_gratuito()` em `apis.py`.
