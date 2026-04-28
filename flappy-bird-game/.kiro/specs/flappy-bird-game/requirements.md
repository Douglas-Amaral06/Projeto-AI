# Requirements Document: Flappy Bird Game

## Executive Summary

O Flappy Bird Game é um clone completo do jogo clássico Flappy Bird, implementado como uma aplicação web full-stack. O projeto combina um front-end interativo em HTML5 Canvas com um back-end Node.js/Express para gerenciar um ranking global de pontuações. O objetivo é fornecer uma experiência de jogo fluida, responsiva e com persistência de dados.

## Business Requirements

### BR1: Jogo Funcional e Jogável
O sistema deve fornecer uma experiência de jogo completa e funcional que espelhe a mecânica clássica do Flappy Bird, permitindo que jogadores compitam por pontuações mais altas.

**Critérios de Aceitação**:
- O jogo deve ser acessível diretamente no navegador sem instalação adicional
- O jogo deve ser jogável em tempo real com resposta imediata aos controles
- A experiência deve ser fluida a 60 FPS

### BR2: Persistência de Pontuações
O sistema deve manter um registro permanente de pontuações de jogadores para criar um ranking competitivo.

**Critérios de Aceitação**:
- Pontuações devem ser salvas no servidor após o fim do jogo
- Um ranking das 10 maiores pontuações deve ser acessível
- Cada pontuação deve incluir nome do jogador, pontuação e timestamp

### BR3: Interface Intuitiva
O sistema deve fornecer uma interface clara e intuitiva que guie o jogador através do jogo.

**Critérios de Aceitação**:
- Tela inicial com instruções claras
- HUD durante o jogo mostrando pontuação atual
- Tela de game over com opção de salvar pontuação e visualizar ranking
- Design visual consistente com estética pixel-art 8-bit

## Functional Requirements

### FR1: Mecânica de Física do Pássaro

**Descrição**: O pássaro deve obedecer a leis de física realistas com gravidade constante.

**Detalhes**:
- Gravidade constante de 0.6 pixels/frame² puxando o pássaro para baixo
- Velocidade inicial do pássaro é 0
- Ao pular, o pássaro recebe impulso de -12 pixels/frame (força para cima)
- Velocidade máxima (terminal) deve ser limitada para evitar comportamento irreal
- Posição do pássaro deve ser atualizada a cada frame: `y = y + velocity` e `velocity = velocity + gravity`

**Entrada**: Clique do mouse, pressão da barra de espaço ou toque na tela
**Saída**: Pássaro se move para cima quando acionado, cai continuamente por gravidade
**Critérios de Aceitação**:
- Pássaro cai suavemente quando não há entrada
- Pássaro salta imediatamente ao receber entrada
- Movimento é previsível e consistente

### FR2: Geração de Obstáculos (Canos)

**Descrição**: O sistema deve gerar pares de canos que se movem da direita para a esquerda continuamente.

**Detalhes**:
- Cada par de canos consiste em um cano superior e um inferior
- Abertura entre canos (gap) tem altura fixa de 120 pixels
- Altura da abertura é gerada aleatoriamente para cada novo par
- Canos se movem a -4 pixels/frame (velocidade constante para esquerda)
- Novos canos são gerados quando o anterior sai da tela
- Espaçamento horizontal entre pares de canos é consistente (~200 pixels)

**Entrada**: Nenhuma (geração automática)
**Saída**: Canos aparecem na direita, movem-se para esquerda, desaparecem
**Critérios de Aceitação**:
- Canos aparecem em intervalos regulares
- Abertura é sempre passável (não muito pequena)
- Abertura varia em altura entre pares
- Canos são removidos da memória quando off-screen

### FR3: Detecção de Colisão

**Descrição**: O sistema deve detectar colisões entre o pássaro e obstáculos usando AABB (Axis-Aligned Bounding Box).

**Detalhes**:
- Colisão AABB: dois retângulos colidem se se sobrepõem em ambos os eixos X e Y
- Fórmula: `rect1.x + rect1.width >= rect2.x AND rect1.x <= rect2.x + rect2.width AND rect1.y + rect1.height >= rect2.y AND rect1.y <= rect2.y + rect2.height`
- Colisão com cano superior: pássaro toca cano acima da abertura
- Colisão com cano inferior: pássaro toca cano abaixo da abertura
- Colisão com chão: pássaro toca o limite inferior da tela
- Colisão com teto: pássaro toca o limite superior da tela (game over)

**Entrada**: Posições do pássaro e obstáculos a cada frame
**Saída**: Sinal de colisão que encerra o jogo
**Critérios de Aceitação**:
- Colisão é detectada com precisão
- Pássaro pode passar pela abertura sem falsos positivos
- Colisão com chão encerra o jogo imediatamente
- Sem lag ou atraso na detecção

### FR4: Sistema de Pontuação

**Descrição**: O sistema deve rastrear e incrementar a pontuação quando o pássaro passa por obstáculos.

**Detalhes**:
- Pontuação começa em 0
- 1 ponto é adicionado quando o pássaro cruza completamente a coordenada X do centro de um par de canos
- Cada cano é contado apenas uma vez (flag `scored` previne contagem dupla)
- Pontuação é exibida em tempo real no HUD
- Pontuação final é exibida na tela de game over

**Entrada**: Posição do pássaro e canos a cada frame
**Saída**: Incremento de pontuação, atualização de HUD
**Critérios de Aceitação**:
- Pontuação incrementa exatamente uma vez por cano
- Pontuação é visível durante o jogo
- Pontuação final é correta

### FR5: Game Loop e Renderização

**Descrição**: O sistema deve executar um game loop fluido a 60 FPS usando requestAnimationFrame.

**Detalhes**:
- Game loop executa: Input → Update → Collision Detection → Render
- requestAnimationFrame garante sincronização com refresh rate do monitor
- Canvas é limpo a cada frame
- Todas as entidades são renderizadas em ordem: fundo → canos → chão → pássaro → HUD
- Delta time é calculado para física independente de frame rate

**Entrada**: Eventos de entrada do usuário
**Saída**: Frame renderizado no canvas
**Critérios de Aceitação**:
- Game roda a ~60 FPS
- Sem stuttering ou frame drops
- Renderização é suave e responsiva

### FR6: Tela Inicial (Menu)

**Descrição**: O sistema deve exibir uma tela inicial com instruções e opção para começar.

**Detalhes**:
- Título "Flappy Bird" centralizado e grande
- Texto "Clique para começar" piscando (alternando visibilidade a cada 500ms)
- Fundo com céu e chão estáticos
- Pássaro estático no centro
- Ao clicar/tocar/pressionar espaço, o jogo inicia

**Entrada**: Clique, toque ou pressão de espaço
**Saída**: Transição para estado "playing"
**Critérios de Aceitação**:
- Menu é visualmente atraente
- Instruções são claras
- Transição para jogo é imediata

### FR7: HUD (Heads-Up Display) Durante o Jogo

**Descrição**: O sistema deve exibir informações em tempo real durante o jogo.

**Detalhes**:
- Pontuação atual exibida no topo esquerdo
- Fonte grande (24px+), branca com borda preta para legibilidade
- Atualiza a cada frame
- Posicionado para não obstruir gameplay

**Entrada**: Pontuação atual do jogo
**Saída**: Texto renderizado no canvas
**Critérios de Aceitação**:
- Pontuação é legível
- Não interfere com gameplay
- Atualiza em tempo real

### FR8: Tela de Game Over

**Descrição**: O sistema deve exibir uma tela de game over com opções de ação.

**Detalhes**:
- Painel semi-transparente cobrindo a tela
- Exibe "Game Over" em grande
- Exibe pontuação final
- Campo de input para nome do jogador (máx 20 caracteres)
- Botão "Salvar Pontuação" para enviar score ao servidor
- Botão "Restart" para reiniciar o jogo
- Após salvar, exibe ranking das 10 maiores pontuações

**Entrada**: Nome do jogador, clique em botões
**Saída**: Score salvo no servidor, ranking exibido
**Critérios de Aceitação**:
- Painel é visível e legível
- Input aceita nome válido
- Botões são responsivos
- Ranking é exibido após salvar

### FR9: Integração com API de Pontuações

**Descrição**: O front-end deve se comunicar com o back-end para salvar e recuperar pontuações.

**Detalhes**:
- Usar Fetch API para requisições HTTP
- POST /api/scores com payload `{ "name": "PlayerName", "score": 100 }`
- GET /api/scores para recuperar top 10
- Tratamento de erros de rede
- Feedback visual durante requisição (loading state)

**Entrada**: Nome do jogador e pontuação
**Saída**: Confirmação de salvamento, ranking atualizado
**Critérios de Aceitação**:
- Score é salvo com sucesso
- Ranking é recuperado e exibido
- Erros de rede são tratados graciosamente

### FR10: Renderização Visual com Canvas

**Descrição**: Todos os elementos visuais devem ser renderizados diretamente no Canvas usando primitivas matemáticas.

**Detalhes**:
- Céu: retângulo azul claro (#70C5CE)
- Chão: retângulos verde (#73BF2E) e bege (#DED895) alternados
- Canos: retângulos verde vibrante (#74BF2E) com contorno escuro (#543847)
- Pássaro: círculo ou retângulo amarelo (#E8E94B)
- Sem uso de imagens externas (spritesheets preparados para futuro)

**Entrada**: Posições e estados das entidades
**Saída**: Elementos desenhados no canvas
**Critérios de Aceitação**:
- Todos os elementos são visíveis
- Cores correspondem à paleta especificada
- Renderização é eficiente

## Non-Functional Requirements

### NFR1: Performance

**Descrição**: O jogo deve manter performance consistente.

**Detalhes**:
- Manter 60 FPS em navegadores modernos
- Tempo de renderização < 16ms por frame
- Uso de memória < 50MB
- Sem memory leaks durante gameplay prolongado

**Critérios de Aceitação**:
- Profiler mostra FPS consistente
- Sem lag durante gameplay
- Memória estável após 10+ minutos de jogo

### NFR2: Responsividade

**Descrição**: O jogo deve responder imediatamente aos controles do usuário.

**Detalhes**:
- Latência de input < 50ms
- Pulo do pássaro ocorre no frame seguinte ao input
- Sem delay perceptível

**Critérios de Aceitação**:
- Controles se sentem responsivos
- Sem lag entre input e ação

### NFR3: Compatibilidade de Navegador

**Descrição**: O jogo deve funcionar em navegadores modernos.

**Detalhes**:
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Suporte a mobile (iOS Safari, Chrome Mobile)

**Critérios de Aceitação**:
- Jogo funciona em todos os navegadores listados
- Sem erros de console
- Responsivo em diferentes tamanhos de tela

### NFR4: Escalabilidade do Backend

**Descrição**: O backend deve suportar múltiplos jogadores simultâneos.

**Detalhes**:
- Suportar 100+ requisições simultâneas
- Tempo de resposta < 200ms para GET /api/scores
- Tempo de resposta < 500ms para POST /api/scores
- Sem perda de dados

**Critérios de Aceitação**:
- Load testing mostra performance aceitável
- Sem timeouts ou erros sob carga

### NFR5: Segurança

**Descrição**: O sistema deve proteger contra ataques comuns.

**Detalhes**:
- Validação de entrada no servidor
- Sanitização de nomes de jogadores
- Proteção contra SQL injection (parameterized queries)
- Proteção contra XSS
- Rate limiting em endpoints de API

**Critérios de Aceitação**:
- Nenhuma vulnerabilidade conhecida
- Dados de usuário são seguros
- Sem injeção de código

### NFR6: Usabilidade

**Descrição**: O jogo deve ser fácil de usar para qualquer pessoa.

**Detalhes**:
- Interface intuitiva sem tutorial necessário
- Controles simples e responsivos
- Feedback visual claro (pontuação, game over)
- Acessibilidade básica (contraste, tamanho de fonte)

**Critérios de Aceitação**:
- Novo usuário consegue jogar sem instruções
- Feedback é claro
- Sem confusão sobre o que fazer

### NFR7: Manutenibilidade

**Descrição**: O código deve ser bem estruturado e fácil de manter.

**Detalhes**:
- Separação clara de responsabilidades
- Código comentado em pontos críticos
- Nomes de variáveis e funções descritivos
- Sem código duplicado

**Critérios de Aceitação**:
- Código é legível
- Fácil adicionar novas features
- Fácil debugar problemas

## User Stories

### US1: Jogar o Jogo Básico
**Como** um jogador  
**Quero** jogar Flappy Bird no navegador  
**Para que** eu possa me divertir e competir por pontuações altas

**Critérios de Aceitação**:
- [ ] Consigo acessar o jogo no navegador
- [ ] Consigo controlar o pássaro com clique/espaço/toque
- [ ] O pássaro cai por gravidade
- [ ] Consigo evitar canos
- [ ] O jogo termina ao colidir
- [ ] Minha pontuação é exibida

### US2: Salvar Minha Pontuação
**Como** um jogador  
**Quero** salvar minha pontuação com meu nome  
**Para que** eu possa aparecer no ranking global

**Critérios de Aceitação**:
- [ ] Ao fazer game over, posso digitar meu nome
- [ ] Consigo clicar em "Salvar Pontuação"
- [ ] Minha pontuação é salva no servidor
- [ ] Recebo confirmação de salvamento

### US3: Ver Ranking Global
**Como** um jogador  
**Quero** ver as 10 maiores pontuações  
**Para que** eu saiba como estou comparado a outros jogadores

**Critérios de Aceitação**:
- [ ] Após salvar, vejo o ranking atualizado
- [ ] Ranking mostra nome, pontuação e posição
- [ ] Ranking está ordenado corretamente (maior para menor)
- [ ] Consigo voltar ao menu e jogar novamente

### US4: Jogar Novamente
**Como** um jogador  
**Quero** reiniciar o jogo rapidamente  
**Para que** eu possa tentar melhorar minha pontuação

**Critérios de Aceitação**:
- [ ] Botão "Restart" reinicia o jogo
- [ ] Pontuação volta a 0
- [ ] Pássaro volta à posição inicial
- [ ] Canos são limpos

### US5: Jogar em Dispositivo Móvel
**Como** um jogador em mobile  
**Quero** jogar Flappy Bird no meu smartphone  
**Para que** eu possa jogar em qualquer lugar

**Critérios de Aceitação**:
- [ ] Jogo é responsivo em telas pequenas
- [ ] Toque funciona como controle
- [ ] Sem scroll horizontal/vertical
- [ ] Elementos são legíveis em mobile

## Data Requirements

### DR1: Armazenamento de Pontuações
- Cada pontuação deve armazenar: ID, Nome do Jogador, Pontuação, Timestamp
- Dados devem ser persistidos em SQLite
- Suportar pelo menos 10.000 registros sem degradação de performance

### DR2: Integridade de Dados
- Nenhuma pontuação deve ser perdida
- Nomes de jogadores devem ser validados (1-20 caracteres)
- Pontuações devem ser não-negativas
- Timestamps devem ser precisos

## Constraints

### C1: Tecnologia
- Front-end: HTML5, CSS3, JavaScript ES6+ (sem frameworks)
- Back-end: Node.js + Express.js
- Banco de dados: SQLite
- Sem dependências externas para renderização (Canvas nativo)

### C2: Tamanho de Arquivo
- Arquivo HTML < 50KB
- Arquivo CSS < 20KB
- Arquivo JavaScript total < 100KB
- Sem assets externos (imagens, fontes)

### C3: Compatibilidade
- Deve funcionar em navegadores modernos (2020+)
- Deve funcionar em mobile (iOS e Android)
- Sem polyfills necessários

### C4: Ambiente
- Backend deve rodar em Node.js 14+
- SQLite deve ser embarcado (sem servidor externo)
- Deve funcionar em localhost sem configuração complexa

## Acceptance Criteria (Global)

### AC1: Jogo Funcional
- [ ] Jogo inicia sem erros
- [ ] Pássaro se move corretamente
- [ ] Canos aparecem e se movem
- [ ] Colisões são detectadas
- [ ] Pontuação incrementa corretamente
- [ ] Game over funciona

### AC2: Backend Funcional
- [ ] Servidor Express inicia sem erros
- [ ] GET /api/scores retorna top 10
- [ ] POST /api/scores salva score
- [ ] Banco de dados persiste dados
- [ ] Sem erros de conexão

### AC3: Interface Completa
- [ ] Tela inicial é exibida
- [ ] HUD mostra pontuação
- [ ] Tela de game over é exibida
- [ ] Ranking é exibido após salvar
- [ ] Botões funcionam corretamente

### AC4: Qualidade
- [ ] Sem erros de console
- [ ] Sem memory leaks
- [ ] Performance é fluida (60 FPS)
- [ ] Código é bem comentado
- [ ] Sem código duplicado

## Success Metrics

1. **Gameplay**: Jogo é jogável e divertido (subjetivo, mas testável com usuários)
2. **Performance**: Mantém 60 FPS consistentemente
3. **Confiabilidade**: 100% uptime do servidor durante testes
4. **Usabilidade**: Novo usuário consegue jogar em < 30 segundos
5. **Dados**: Todas as pontuações são salvas e recuperadas corretamente

## Out of Scope

- Multiplayer em tempo real
- Leaderboard por região/país
- Achievements ou badges
- Customização de pássaro/canos
- Diferentes níveis de dificuldade
- Efeitos sonoros ou música
- Animações complexas
- Integração com redes sociais
- Autenticação de usuários
- Histórico de jogos por usuário

## Glossary

- **AABB**: Axis-Aligned Bounding Box - método de detecção de colisão usando retângulos
- **Canvas**: Elemento HTML5 para desenho 2D
- **Game Loop**: Ciclo principal que atualiza e renderiza o jogo
- **HUD**: Heads-Up Display - informações exibidas durante o jogo
- **Pipe**: Obstáculo (cano) que o pássaro deve evitar
- **Gap**: Abertura entre canos por onde o pássaro passa
- **Sprite**: Imagem 2D de um objeto (preparado para futuro)
- **Frame Rate**: Número de frames renderizados por segundo (FPS)
- **requestAnimationFrame**: API do navegador para sincronizar com refresh rate

## Revision History

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 1.0 | 2026-04-24 | Kiro | Documento inicial baseado em design |

