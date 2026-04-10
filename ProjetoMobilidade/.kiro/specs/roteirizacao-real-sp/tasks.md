# Implementation Plan: Roteirização Real SP

## Overview

Integra o OpenTripPlanner (OTP) ao sistema existente de Vale-Transporte, substituindo o motor de rotas simulado por dados reais da SPTrans/GTFS. A implementação é incremental: primeiro os scripts de ambiente, depois o cliente OTP isolado, depois a integração com `apis.py`, depois o agente de IA e o frontend, e por fim os testes de propriedade.

## Tasks

- [ ] 1. Corrigir scripts PowerShell de setup do OTP
  - Editar `servidor_rotas/setup_otp.ps1`: substituir caminhos hardcoded por resolução dinâmica via `$MyInvocation.MyCommand.Path` usando `Split-Path -Parent`
  - Definir `$ScriptDir`, `$ProjectRoot`, `$ServidorDir` e `$SaoPauloDir` no topo do script
  - Adicionar verificação de Java no PATH com mensagem de erro clara (versão mínima Java 11) e `exit 1` se ausente
  - Adicionar verificação de `graph.obj` existente para pular o build com mensagem informativa
  - Editar `servidor_rotas/start_otp.ps1`: mesma resolução de caminhos + verificação de `graph.obj` com `exit 1` e mensagem orientando a executar `setup_otp.ps1` primeiro
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_

- [ ] 2. Criar `otp_client.py` — carregamento de tarifas GTFS
  - Criar o arquivo `otp_client.py` na raiz do projeto
  - Implementar `_carregar_tarifas_gtfs(zip_path: str) -> dict` que abre `google_transit.zip`, lê `fare_attributes.txt` e `fare_rules.txt` com `zipfile` + `csv`, e retorna `FareTable` com chaves `bus_only`, `metro_only`, `integration` e `source`
  - Adicionar fallback para tabela hardcoded (`bus_only: 5.82`, `metro_only: 5.92`, `integration: 11.32`, `source: "Tabela fixa 2026"`) quando o zip estiver ausente ou corrompido
  - Chamar `_carregar_tarifas_gtfs()` no nível de módulo (na importação) para pré-carregar as tarifas
  - _Requirements: 3.1, 3.6, 3.7_

  - [ ]* 2.1 Escrever teste de propriedade — Property 6: `info_tarifas` não-vazio
    - **Property 6: `info_tarifas` sempre indica a fonte dos dados**
    - Criar `tests/test_otp_properties.py` com `@given(st.text(), st.text())` mockando Nominatim e OTP
    - Verificar que `resultado["info_tarifas"]` é string não-vazia em qualquer chamada
    - **Validates: Requirements 3.7**

- [ ] 3. Criar `otp_client.py` — verificação de disponibilidade e consulta HTTP ao OTP
  - Implementar `_verificar_otp_disponivel() -> bool` que faz `GET http://localhost:8080/otp/routers/default` com timeout de 2s; captura `ConnectionError` e `Timeout` retornando `False`; loga aviso com `logging.warning` em caso de falha
  - Implementar `_consultar_otp(lat_o, lon_o, lat_d, lon_d) -> list[dict]` que monta a query string para `http://localhost:8080/otp/routers/default/plan` com parâmetros `fromPlace`, `toPlace`, `mode=TRANSIT,WALK`, `numItineraries=5`, `locale=pt`; retorna a lista de itinerários ou `[]` em caso de erro
  - Reutilizar `obter_coordenadas_reais()` de `apis.py` para geocodificação via Nominatim (importar de `apis`)
  - _Requirements: 2.2, 2.8, 6.2_

- [ ] 4. Criar `otp_client.py` — parsing de itinerários e classificação de modal
  - Implementar `_classificar_modal(legs: list[dict]) -> str` que inspeciona o campo `mode` de cada leg e retorna `"bus_only"` (apenas BUS), `"metro_only"` (apenas SUBWAY/RAIL/TRAM) ou `"integration"` (BUS + SUBWAY/RAIL)
  - Implementar `_extrair_trajeto(legs: list[dict]) -> str` que filtra legs com `mode != "WALK"`, formata cada um como `"Ônibus {route} {agencyName}"` ou `"Metrô {route} {agencyName}"` conforme o modo, e une com `" → "`
  - Implementar `_calcular_tarifa(legs: list[dict], tarifas: dict) -> tuple[float, str]` que usa `_classificar_modal()` para selecionar a entrada correta em `tarifas` e retorna `(price, label)`
  - Implementar `_parsear_itinerario(itinerary: dict, tarifas: dict) -> dict` que extrai `duration`, chama as funções acima e retorna o dict de rota no formato compatível com `motor_de_rotas_gratuito()` (campos: `modal`, `trajeto`, `valor_diario`, `tempo`, `bilhete`)
  - O campo `tempo` deve ser `f"{math.ceil(duration / 60)} min"` — sem estimativas aleatórias
  - O campo `valor_diario` deve ser `tarifa * 2` (ida e volta)
  - _Requirements: 2.3, 2.4, 2.5, 2.6, 3.2, 3.3, 3.4, 3.5_

  - [ ]* 4.1 Escrever teste de propriedade — Property 3: nomes reais de linhas no `trajeto`
    - **Property 3: Nomes reais de linhas no campo `trajeto`**
    - `@given(itinerary_with_transit_legs())` — estratégia que gera itinerários com N legs de transporte (N ≥ 1)
    - Verificar que `trajeto` contém os nomes de todas as N linhas separados por `" → "`
    - **Validates: Requirements 2.4, 2.5, 5.1, 5.2**

  - [ ]* 4.2 Escrever teste de propriedade — Property 4: tempo derivado de `duration`
    - **Property 4: Tempo de viagem derivado do campo `duration` do OTP**
    - `@given(st.integers(min_value=60, max_value=7200))` passado como `duration` no itinerário mockado
    - Verificar que `tempo == f"{math.ceil(duration / 60)} min"`
    - **Validates: Requirements 2.6, 5.4**

  - [ ]* 4.3 Escrever teste de propriedade — Property 5: tarifa correta por modal
    - **Property 5: Tarifa correta por modal**
    - `@given(itinerary_by_mode_strategy())` — estratégia que gera itinerários com legs de modo fixo (bus-only, metro-only, integration)
    - Verificar `valor_diario` e conteúdo de `bilhete` para cada caso
    - **Validates: Requirements 3.2, 3.3, 3.4, 3.5**

- [ ] 5. Criar `otp_client.py` — função pública `motor_de_rotas_otp()` com fallback
  - Implementar `motor_de_rotas_otp(end_casa: str, end_trab: str) -> dict` que:
    1. Geocodifica os dois endereços via `obter_coordenadas_reais()` (com fallback para coordenadas padrão de SP)
    2. Chama `_verificar_otp_disponivel()`; se `False`, retorna resultado de `motor_de_rotas_gratuito()` com log de aviso
    3. Chama `_consultar_otp()` e parseia até 3 itinerários distintos por modal com `_parsear_itinerario()`
    4. Preenche opções faltantes com dados de `motor_de_rotas_gratuito()` marcando `trajeto` com sufixo `" (estimado)"`
    5. Retorna dict com chaves `rotas` (lista de 3), `distancia_km`, `coords_reais`, `info_tarifas`
  - Garantir que `coords_reais` seja sempre `[(lat_c, lon_c), (lat_t, lon_t)]` com as coordenadas reais do Nominatim
  - _Requirements: 2.1, 2.7, 2.8, 2.9, 6.1, 6.5_

  - [ ]* 5.1 Escrever teste de propriedade — Property 1: compatibilidade de assinatura de retorno
    - **Property 1: Compatibilidade de assinatura de retorno**
    - `@given(st.text(), st.text())` com mock de Nominatim e OTP (respostas variadas)
    - Verificar que o retorno contém exatamente as chaves `rotas`, `distancia_km`, `coords_reais`, `info_tarifas`
    - Verificar que cada item em `rotas` contém `modal`, `trajeto`, `valor_diario`, `tempo`, `bilhete`
    - **Validates: Requirements 2.1, 6.1**

  - [ ]* 5.2 Escrever teste de propriedade — Property 2: sempre 3 opções com fallback marcado
    - **Property 2: Sempre 3 opções de rota com fallback marcado**
    - `@given(st.lists(itinerary_strategy(), max_size=5))` — OTP retorna 0 a 5 itinerários
    - Verificar que `len(rotas) == 3` sempre
    - Verificar que toda opção de fallback tem `"(estimado)"` no campo `trajeto`
    - **Validates: Requirements 2.3, 2.7, 5.3**

  - [ ]* 5.3 Escrever teste de propriedade — Property 7: coordenadas preservadas
    - **Property 7: Coordenadas reais preservadas no retorno**
    - `@given(lat_lon_strategy(), lat_lon_strategy())` — estratégia que gera pares `(lat, lon)` válidos para SP
    - Mockar Nominatim para retornar as coordenadas geradas
    - Verificar que `coords_reais == [(lat_c, lon_c), (lat_t, lon_t)]`
    - **Validates: Requirements 2.9**

- [ ] 6. Checkpoint — Verificar `otp_client.py` isolado
  - Garantir que todos os testes passam, ask the user if questions arise.

- [ ] 7. Atualizar `apis.py` para expor `motor_de_rotas_otp()` com fallback
  - Adicionar bloco `try/except ImportError` no topo de `apis.py` para importar `motor_de_rotas_otp` de `otp_client`
  - Definir flag `_OTP_DISPONIVEL` conforme o import teve sucesso
  - Adicionar função `motor_de_rotas_otp(end_casa: str, end_trab: str) -> dict` em `apis.py` que delega para `_motor_otp()` se disponível, ou chama `motor_de_rotas_gratuito()` caso contrário
  - Garantir que `motor_de_rotas_gratuito()` permanece **sem nenhuma alteração** em sua implementação interna
  - _Requirements: 2.1, 6.1, 6.5_

- [ ] 8. Atualizar `agente_ia.py` com prompt enriquecido
  - Estender a assinatura de `analisar_rota_com_ia()` com três parâmetros opcionais retrocompatíveis: `transferencias: list[int] | None = None`, `tempos_caminhada: list[int] | None = None`, `fonte_dados: str = "estimado"`
  - Atualizar o prompt para incluir, quando disponíveis: nomes reais das linhas (campo `trajeto` de cada rota), número de transferências por opção, tempo de caminhada por opção, e indicação explícita de `"dados reais OTP"` vs `"estimativa"` para cada opção
  - Manter o comportamento existente quando os novos parâmetros forem `None` (retrocompatibilidade total)
  - Manter o retorno da mensagem de aviso existente quando a chave Gemini não estiver configurada
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [ ]* 8.1 Escrever teste de propriedade — Property 8: prompt contém dados reais
    - **Property 8: Prompt do agente contém dados reais de linhas, transferências e caminhada**
    - `@given(route_metadata_strategy())` — estratégia que gera listas de rotas com nomes de linhas reais, transferências e tempos de caminhada
    - Verificar que o prompt construído contém: (a) pelo menos um nome de linha real, (b) número de transferências de cada opção, (c) tempo de caminhada de cada opção, (d) string `"dados reais OTP"` ou `"estimativa"`
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**

- [ ] 9. Atualizar `app_piloto.py` para usar `motor_de_rotas_otp()` e exibir aviso de fallback
  - Substituir a chamada `motor_de_rotas_gratuito(...)` na seção de auto-roteirização por `motor_de_rotas_otp(...)`
  - Extrair metadados de transferências e caminhada do resultado OTP para passar a `analisar_rota_com_ia()` com os novos parâmetros
  - Adicionar aviso visual (`st.warning`) quando o resultado contiver rotas com `"(estimado)"` no trajeto, informando que o OTP não está disponível e as rotas são estimativas
  - Manter o mapa Folium existente com marcadores C/T e linha reta sem alterações
  - Manter todas as demais funcionalidades (contestações, edição, envio de carta) sem alterações
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 6.3, 6.4_

- [ ] 10. Checkpoint final — Garantir que todos os testes passam
  - Garantir que todos os testes passam, ask the user if questions arise.

## Notes

- Tarefas marcadas com `*` são opcionais e podem ser puladas para um MVP mais rápido
- Cada tarefa referencia requisitos específicos para rastreabilidade
- Os testes de propriedade usam **Hypothesis** com mínimo de 100 iterações; HTTP do OTP e Nominatim deve ser mockado com `unittest.mock.patch`
- `motor_de_rotas_gratuito()` em `apis.py` **nunca deve ser modificado** — é o fallback de segurança
- Os scripts PowerShell não existem ainda no workspace; devem ser criados do zero em `servidor_rotas/`
