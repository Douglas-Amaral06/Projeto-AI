/**
 * Game Engine - Flappy Bird Space Edition
 * Gerencia o loop principal do jogo, estados e renderização
 */

class GameEngine {
  /**
   * Constantes do jogo
   */
  static CANVAS_WIDTH = 400;
  static CANVAS_HEIGHT = 600;
  static GROUND_HEIGHT = 50;
  static PIPE_WIDTH = 52;
  static PIPE_GAP_HEIGHT = 120;
  static PIPE_SPAWN_INTERVAL = 2500; // ms entre spawns de canos
  static PLANET_SPAWN_INTERVAL = 8000; // ms entre spawns de planetas
  static MIN_GAP_Y = 80;
  static MAX_GAP_Y = 350;

  /**
   * Estados do jogo
   */
  static STATES = {
    MENU: 'menu',
    PLAYING: 'playing',
    GAME_OVER: 'gameOver',
    PAUSED: 'paused'
  };

  /**
   * Cores da paleta
   */
  static COLORS = {
    SKY: '#0a0e27',
    SPACE_DARK: '#050810',
    GROUND_1: '#DED895',
    GROUND_2: '#73BF2E',
    PIPE: '#74BF2E',
    BIRD: '#E8E94B',
    TEXT: '#FFFFFF',
    TEXT_SHADOW: '#000000'
  };

  /**
   * Construtor do Game Engine
   * @param {HTMLCanvasElement} canvasElement - Elemento canvas do jogo
   */
  constructor(canvasElement) {
    this.canvas = canvasElement;
    this.ctx = this.canvas.getContext('2d');
    
    // Dimensões
    this.width = GameEngine.CANVAS_WIDTH;
    this.height = GameEngine.CANVAS_HEIGHT;
    
    // Estado do jogo
    this.gameState = GameEngine.STATES.MENU;
    this.score = 0;
    this.highScore = localStorage.getItem('flappyBirdHighScore') || 0;
    
    // Entidades
    this.bird = null;
    this.ground = null;
    this.pipes = [];
    this.planets = [];
    
    // Timing
    this.lastFrameTime = 0;
    this.lastPipeSpawnTime = 0;
    this.lastPlanetSpawnTime = 0;
    this.menuBlinkTime = 0;
    this.menuBlinkVisible = true;
    
    // Input
    this.inputQueue = [];
    this.setupInputListeners();
    
    // Animação
    this.animationFrameId = null;
  }

  /**
   * Configura os listeners de input
   * Suporta: teclado (espaço), mouse (clique) e touch
   */
  setupInputListeners() {
    // Teclado - Espaço
    document.addEventListener('keydown', (e) => {
      if (e.code === 'Space') {
        e.preventDefault();
        this.handleInput('jump');
      }
    });

    // Mouse - Clique
    this.canvas.addEventListener('click', () => {
      this.handleInput('jump');
    });

    // Touch - Toque na tela
    this.canvas.addEventListener('touchstart', (e) => {
      e.preventDefault();
      this.handleInput('jump');
    });

    // Botões da UI
    document.getElementById('saveScoreBtn').addEventListener('click', () => {
      this.saveScore();
    });

    document.getElementById('restartBtn').addEventListener('click', () => {
      this.reset();
      this.start();
    });

    document.getElementById('playAgainBtn').addEventListener('click', () => {
      this.reset();
      this.start();
    });

    document.getElementById('retryBtn').addEventListener('click', () => {
      this.saveScore();
    });
  }

  /**
   * Processa input do jogador
   * @param {string} inputType - Tipo de input ('jump', 'pause', etc)
   */
  handleInput(inputType) {
    if (inputType === 'jump') {
      if (this.gameState === GameEngine.STATES.MENU) {
        this.start();
      } else if (this.gameState === GameEngine.STATES.PLAYING) {
        this.bird.jump();
      }
    }
  }

  /**
   * Inicia o jogo
   */
  start() {
    this.gameState = GameEngine.STATES.PLAYING;
    this.score = 0;
    this.pipes = [];
    this.planets = [];
    this.lastPipeSpawnTime = Date.now();
    this.lastPlanetSpawnTime = Date.now();
    
    // Criar entidades
    this.bird = new Bird(
      this.width / 4,
      this.height / 2
    );
    
    this.ground = new Ground(
      this.height - GameEngine.GROUND_HEIGHT,
      this.width
    );
    
    // Esconder modal de game over
    document.getElementById('gameOverModal').classList.add('hidden');
    
    // Iniciar loop
    this.lastFrameTime = Date.now();
    this.gameLoop();
  }

  /**
   * Reseta o jogo para o estado inicial
   */
  reset() {
    this.gameState = GameEngine.STATES.MENU;
    this.score = 0;
    this.bird = null;
    this.ground = null;
    this.pipes = [];
    this.planets = [];
    this.inputQueue = [];
    this.menuBlinkTime = 0;
    this.menuBlinkVisible = true;
  }

  /**
   * Game Loop Principal
   * Executa: Input → Update → Collision Detection → Render
   * Usa requestAnimationFrame para sincronização com o monitor
   */
  gameLoop = () => {
    const currentTime = Date.now();
    const deltaTime = currentTime - this.lastFrameTime;
    this.lastFrameTime = currentTime;

    // Atualizar
    if (this.gameState === GameEngine.STATES.PLAYING) {
      this.update(deltaTime, currentTime);
      this.checkCollisions();
    }

    // Renderizar
    this.render();

    // Próximo frame
    if (this.gameState === GameEngine.STATES.PLAYING) {
      this.animationFrameId = requestAnimationFrame(this.gameLoop);
    }
  };

  /**
   * Atualiza o estado do jogo
   * @param {number} deltaTime - Tempo decorrido desde o último frame (em ms)
   * @param {number} currentTime - Tempo atual em ms
   */
  update(deltaTime, currentTime) {
    // Atualizar entidades
    this.bird.update(deltaTime);
    this.ground.update(deltaTime);

    // Atualizar canos
    this.pipes.forEach(pipe => pipe.update(deltaTime));

    // Atualizar planetas
    this.planets.forEach(planet => planet.update(deltaTime));

    // Remover canos off-screen
    this.pipes = this.pipes.filter(pipe => !pipe.isOffScreen());

    // Remover planetas off-screen
    this.planets = this.planets.filter(planet => !planet.isOffScreen());

    // Spawnar novos canos
    if (currentTime - this.lastPipeSpawnTime > GameEngine.PIPE_SPAWN_INTERVAL) {
      this.spawnPipe();
      this.lastPipeSpawnTime = currentTime;
    }

    // Spawnar novos planetas
    if (currentTime - this.lastPlanetSpawnTime > GameEngine.PLANET_SPAWN_INTERVAL) {
      this.spawnPlanet();
      this.lastPlanetSpawnTime = currentTime;
    }
  }

  /**
   * Verifica colisões
   * Detecta colisões com canos, chão e teto
   */
  checkCollisions() {
    // Colisão com chão
    if (CollisionDetector.checkBirdGroundCollision(this.bird, this.ground)) {
      this.endGame();
      return;
    }

    // Colisão com teto
    if (CollisionDetector.checkBirdCeilingCollision(this.bird)) {
      this.endGame();
      return;
    }

    // Colisão com canos
    for (let pipe of this.pipes) {
      if (CollisionDetector.checkBirdPipeCollision(this.bird, pipe)) {
        this.endGame();
        return;
      }

      // Verificar pontuação
      if (CollisionDetector.checkPipeScore(this.bird, pipe)) {
        this.score++;
        pipe.markScored();
        
        // Atualizar high score
        if (this.score > this.highScore) {
          this.highScore = this.score;
          localStorage.setItem('flappyBirdHighScore', this.highScore);
        }
      }
    }
  }

  /**
   * Spawna um novo cano
   * Gera posição aleatória para a abertura
   */
  spawnPipe() {
    const gapY = this.generateRandomGapY();
    const pipe = new Pipe(
      this.width,
      gapY,
      GameEngine.PIPE_GAP_HEIGHT
    );
    this.pipes.push(pipe);
  }

  /**
   * Gera posição aleatória para a abertura do cano
   * Garante que a abertura está dentro dos limites da tela
   * 
   * @returns {number} Posição Y da abertura
   */
  generateRandomGapY() {
    const minGapY = GameEngine.MIN_GAP_Y;
    const maxGapY = GameEngine.MAX_GAP_Y;
    const randomGapY = minGapY + Math.random() * (maxGapY - minGapY);
    
    // Garantir que a abertura não ultrapassa os limites
    const gapY = Math.max(
      0,
      Math.min(
        randomGapY,
        this.height - GameEngine.GROUND_HEIGHT - GameEngine.PIPE_GAP_HEIGHT
      )
    );
    
    return gapY;
  }

  /**
   * Spawna um novo planeta
   * Gera posição aleatória e cor aleatória
   */
  spawnPlanet() {
    const planetColors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8'];
    const randomColor = planetColors[Math.floor(Math.random() * planetColors.length)];
    const randomRadius = 20 + Math.random() * 40; // Entre 20 e 60
    const randomY = 50 + Math.random() * (this.height - GameEngine.GROUND_HEIGHT - randomRadius * 2);
    
    const planet = new Planet(
      this.width + randomRadius,
      randomY,
      randomRadius,
      randomColor
    );
    
    this.planets.push(planet);
  }

  /**
   * Encerra o jogo
   */
  endGame() {
    this.gameState = GameEngine.STATES.GAME_OVER;
    this.bird.isAlive = false;
    
    // Mostrar modal de game over
    this.showGameOverModal();
  }

  /**
   * Mostra o modal de game over
   */
  showGameOverModal() {
    const modal = document.getElementById('gameOverModal');
    const finalScoreEl = document.getElementById('finalScore');
    const playerNameInput = document.getElementById('playerName');
    const rankingContainer = document.getElementById('rankingContainer');
    const loadingState = document.getElementById('loadingState');
    const errorState = document.getElementById('errorState');
    
    // Resetar estados
    rankingContainer.classList.add('hidden');
    loadingState.classList.add('hidden');
    errorState.classList.add('hidden');
    
    // Mostrar pontuação final
    finalScoreEl.textContent = this.score;
    playerNameInput.value = '';
    playerNameInput.focus();
    
    // Mostrar modal
    modal.classList.remove('hidden');
  }

  /**
   * Salva a pontuação no servidor
   */
  async saveScore() {
    const playerNameInput = document.getElementById('playerName');
    const playerName = playerNameInput.value.trim();
    
    if (!playerName) {
      this.showError('Por favor, digite seu nome');
      return;
    }

    const loadingState = document.getElementById('loadingState');
    const errorState = document.getElementById('errorState');
    const buttonGroup = document.querySelector('.button-group');
    
    // Mostrar loading
    loadingState.classList.remove('hidden');
    buttonGroup.style.display = 'none';
    errorState.classList.add('hidden');

    try {
      // Salvar score
      const savedScore = await ScoreAPI.saveScore(playerName, this.score);
      console.log('Score salvo:', savedScore);

      // Buscar ranking atualizado
      const topScores = await ScoreAPI.getTopScores(10);
      
      // Esconder loading
      loadingState.classList.add('hidden');
      
      // Mostrar ranking
      this.displayRanking(topScores, savedScore.id);
    } catch (error) {
      console.error('Erro ao salvar score:', error);
      loadingState.classList.add('hidden');
      this.showError(error.message || 'Erro ao salvar pontuação. Tente novamente.');
    }
  }

  /**
   * Exibe o ranking de pontuações
   * @param {Array} scores - Array de scores
   * @param {number} currentScoreId - ID do score atual (para highlight)
   */
  displayRanking(scores, currentScoreId) {
    const rankingContainer = document.getElementById('rankingContainer');
    const rankingBody = document.getElementById('rankingBody');
    
    // Limpar tabela
    rankingBody.innerHTML = '';
    
    // Preencher tabela
    scores.forEach((score, index) => {
      const row = document.createElement('tr');
      
      if (score.id === currentScoreId) {
        row.classList.add('current-player');
      }
      
      const date = new Date(score.timestamp);
      const formattedDate = date.toLocaleDateString('pt-BR', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
      
      row.innerHTML = `
        <td>${index + 1}</td>
        <td>${score.playerName}</td>
        <td>${score.score}</td>
        <td>${formattedDate}</td>
      `;
      
      rankingBody.appendChild(row);
    });
    
    // Mostrar ranking
    rankingContainer.classList.remove('hidden');
  }

  /**
   * Mostra mensagem de erro
   * @param {string} message - Mensagem de erro
   */
  showError(message) {
    const errorState = document.getElementById('errorState');
    const errorMessage = document.getElementById('errorMessage');
    const buttonGroup = document.querySelector('.button-group');
    
    errorMessage.textContent = message;
    errorState.classList.remove('hidden');
    buttonGroup.style.display = 'flex';
  }

  /**
   * Renderiza o jogo
   */
  render() {
    if (this.gameState === GameEngine.STATES.MENU) {
      this.renderMenu();
    } else if (this.gameState === GameEngine.STATES.PLAYING) {
      this.renderGame();
    } else if (this.gameState === GameEngine.STATES.GAME_OVER) {
      this.renderGame(); // Renderizar jogo congelado
    }
  }

  /**
   * Renderiza a tela de menu
   */
  renderMenu() {
    // Fundo
    this.ctx.fillStyle = GameEngine.COLORS.SPACE_DARK;
    this.ctx.fillRect(0, 0, this.width, this.height);

    // Renderizar estrelas
    this.renderStars();

    // Renderizar pássaro estático
    const staticBird = new Bird(this.width / 2, this.height / 3);
    staticBird.render(this.ctx);

    // Renderizar chão
    this.ground = new Ground(this.height - GameEngine.GROUND_HEIGHT, this.width);
    this.ground.render(this.ctx);

    // Título
    this.ctx.fillStyle = GameEngine.COLORS.TEXT;
    this.ctx.font = 'bold 48px Arial';
    this.ctx.textAlign = 'center';
    this.ctx.textBaseline = 'middle';
    
    // Sombra do texto
    this.ctx.fillStyle = GameEngine.COLORS.TEXT_SHADOW;
    this.ctx.fillText('FLAPPY BIRD', this.width / 2 + 2, 80 + 2);
    
    // Texto principal
    this.ctx.fillStyle = GameEngine.COLORS.TEXT;
    this.ctx.fillText('FLAPPY BIRD', this.width / 2, 80);

    // Subtítulo
    this.ctx.font = 'bold 16px Arial';
    this.ctx.fillStyle = '#00ff00';
    this.ctx.fillText('SPACE EDITION', this.width / 2, 120);

    // Texto piscando "Clique para começar"
    this.menuBlinkTime += 16; // Aproximadamente 60 FPS
    if (this.menuBlinkTime > 500) {
      this.menuBlinkVisible = !this.menuBlinkVisible;
      this.menuBlinkTime = 0;
    }

    if (this.menuBlinkVisible) {
      this.ctx.font = '16px Arial';
      this.ctx.fillStyle = GameEngine.COLORS.TEXT;
      this.ctx.fillText('Clique para começar', this.width / 2, this.height - 100);
    }

    // High score
    this.ctx.font = '14px Arial';
    this.ctx.fillStyle = '#ffff00';
    this.ctx.textAlign = 'center';
    this.ctx.fillText(`Melhor Pontuação: ${this.highScore}`, this.width / 2, this.height - 50);
  }

  /**
   * Renderiza o jogo em andamento
   */
  renderGame() {
    // Fundo espacial
    this.ctx.fillStyle = GameEngine.COLORS.SPACE_DARK;
    this.ctx.fillRect(0, 0, this.width, this.height);

    // Renderizar estrelas
    this.renderStars();

    // Renderizar planetas
    this.planets.forEach(planet => planet.render(this.ctx));

    // Renderizar canos
    this.pipes.forEach(pipe => pipe.render(this.ctx));

    // Renderizar chão
    this.ground.render(this.ctx);

    // Renderizar pássaro
    this.bird.render(this.ctx);

    // Renderizar HUD (pontuação)
    this.renderHUD();
  }

  /**
   * Renderiza o HUD (Heads-Up Display)
   * Mostra a pontuação atual
   */
  renderHUD() {
    const scoreText = `Score: ${this.score}`;
    
    // Sombra do texto
    this.ctx.fillStyle = GameEngine.COLORS.TEXT_SHADOW;
    this.ctx.font = 'bold 32px Arial';
    this.ctx.textAlign = 'left';
    this.ctx.textBaseline = 'top';
    this.ctx.fillText(scoreText, 22, 22);

    // Texto principal
    this.ctx.fillStyle = GameEngine.COLORS.TEXT;
    this.ctx.fillText(scoreText, 20, 20);

    // High score no canto superior direito
    const highScoreText = `Best: ${this.highScore}`;
    this.ctx.font = 'bold 16px Arial';
    this.ctx.textAlign = 'right';
    
    // Sombra
    this.ctx.fillStyle = GameEngine.COLORS.TEXT_SHADOW;
    this.ctx.fillText(highScoreText, this.width - 18, 22);
    
    // Texto principal
    this.ctx.fillStyle = '#ffff00';
    this.ctx.fillText(highScoreText, this.width - 20, 20);
  }

  /**
   * Renderiza as estrelas de fundo
   */
  renderStars() {
    // Usar seed baseada em posição para gerar estrelas consistentes
    const starCount = 50;
    
    for (let i = 0; i < starCount; i++) {
      // Gerar posição pseudo-aleatória baseada no índice
      const x = (i * 73) % this.width;
      const y = (i * 97) % this.height;
      const size = ((i * 13) % 3) + 0.5;
      const opacity = ((i * 11) % 100) / 100 * 0.7 + 0.3;
      
      this.ctx.fillStyle = `rgba(255, 255, 255, ${opacity})`;
      this.ctx.beginPath();
      this.ctx.arc(x, y, size, 0, Math.PI * 2);
      this.ctx.fill();
    }
  }

  /**
   * Retorna a pontuação atual
   * @returns {number} Pontuação
   */
  getScore() {
    return this.score;
  }

  /**
   * Retorna o estado atual do jogo
   * @returns {string} Estado do jogo
   */
  getGameState() {
    return this.gameState;
  }

  /**
   * Retorna as entidades do jogo
   * @returns {Object} Objeto com bird, ground, pipes, planets
   */
  getEntities() {
    return {
      bird: this.bird,
      ground: this.ground,
      pipes: this.pipes,
      planets: this.planets
    };
  }
}

/**
 * Inicializa o jogo quando o DOM está pronto
 */
document.addEventListener('DOMContentLoaded', () => {
  const canvas = document.getElementById('gameCanvas');
  
  if (!canvas) {
    console.error('Canvas não encontrado!');
    return;
  }

  // Criar e iniciar o game engine
  const engine = new GameEngine(canvas);
  
  // Renderizar menu inicial
  engine.render();
  
  // Armazenar engine globalmente para debug
  window.gameEngine = engine;
  
  console.log('🎮 Flappy Bird Space Edition iniciado!');
  console.log('Clique no canvas ou pressione espaço para começar');
});
