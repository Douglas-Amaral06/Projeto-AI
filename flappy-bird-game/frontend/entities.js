/**
 * Sistema de Entidades do Flappy Bird
 * Define as classes base e todas as entidades do jogo
 */

/**
 * Classe base para todas as entidades do jogo
 * Define a interface comum para atualização e renderização
 */
class Entity {
  /**
   * @param {number} x - Posição X
   * @param {number} y - Posição Y
   * @param {number} width - Largura
   * @param {number} height - Altura
   */
  constructor(x, y, width, height) {
    this.x = x;
    this.y = y;
    this.width = width;
    this.height = height;
  }

  /**
   * Atualiza a entidade a cada frame
   * @param {number} deltaTime - Tempo decorrido desde o último frame (em ms)
   */
  update(deltaTime) {
    // Implementado pelas subclasses
  }

  /**
   * Renderiza a entidade no canvas
   * @param {CanvasRenderingContext2D} ctx - Contexto 2D do canvas
   */
  render(ctx) {
    // Implementado pelas subclasses
  }

  /**
   * Retorna o bounding box (AABB) da entidade
   * @returns {Object} Objeto com x, y, width, height
   */
  getBounds() {
    return {
      x: this.x,
      y: this.y,
      width: this.width,
      height: this.height
    };
  }
}

/**
 * Classe do Pássaro
 * Implementa física com gravidade e controle de pulo
 */
class Bird extends Entity {
  /**
   * @param {number} x - Posição X inicial
   * @param {number} y - Posição Y inicial
   */
  constructor(x, y) {
    super(x, y, 34, 24); // Dimensões padrão do pássaro
    
    // Propriedades de física
    this.velocity = 0;           // Velocidade vertical (pixels/frame)
    this.gravity = 0.6;          // Aceleração da gravidade (pixels/frame²)
    this.jumpForce = -12;        // Força do pulo (velocidade negativa para cima)
    this.maxVelocity = 15;       // Velocidade máxima (terminal velocity)
    
    // Estado
    this.isAlive = true;
    this.rotation = 0;           // Rotação visual do pássaro
  }

  /**
   * Faz o pássaro pular
   * Aplica força negativa (para cima) à velocidade
   */
  jump() {
    this.velocity = this.jumpForce;
    this.rotation = -0.3; // Inclina o pássaro para cima
  }

  /**
   * Atualiza a física do pássaro
   * Aplica gravidade e atualiza posição
   * 
   * Equação de movimento:
   * velocity = velocity + gravity
   * y = y + velocity
   * 
   * @param {number} deltaTime - Tempo decorrido (em ms)
   */
  update(deltaTime) {
    if (!this.isAlive) return;

    // Aplicar gravidade à velocidade
    // A cada frame, a velocidade aumenta pela gravidade
    this.velocity += this.gravity;

    // Limitar velocidade máxima (terminal velocity)
    // Evita que o pássaro caia muito rápido
    if (this.velocity > this.maxVelocity) {
      this.velocity = this.maxVelocity;
    }

    // Atualizar posição Y baseado na velocidade
    this.y += this.velocity;

    // Atualizar rotação visual
    // Quanto mais rápido cai, mais inclina para baixo
    if (this.velocity > 0) {
      this.rotation = Math.min(this.rotation + 0.1, 0.5);
    } else {
      this.rotation = Math.max(this.rotation - 0.1, -0.3);
    }
  }

  /**
   * Renderiza o pássaro no canvas
   * Desenha um círculo amarelo com olhos
   * 
   * @param {CanvasRenderingContext2D} ctx - Contexto 2D do canvas
   */
  render(ctx) {
    ctx.save();
    
    // Transladar para o centro do pássaro para rotação
    ctx.translate(this.x + this.width / 2, this.y + this.height / 2);
    ctx.rotate(this.rotation);
    
    // Desenhar corpo do pássaro (círculo amarelo)
    ctx.fillStyle = '#E8E94B';
    ctx.beginPath();
    ctx.arc(0, 0, this.width / 2, 0, Math.PI * 2);
    ctx.fill();
    
    // Desenhar contorno
    ctx.strokeStyle = '#D4D42A';
    ctx.lineWidth = 2;
    ctx.stroke();
    
    // Desenhar olho
    ctx.fillStyle = '#000000';
    ctx.beginPath();
    ctx.arc(8, -4, 3, 0, Math.PI * 2);
    ctx.fill();
    
    // Brilho no olho
    ctx.fillStyle = '#FFFFFF';
    ctx.beginPath();
    ctx.arc(9, -5, 1.5, 0, Math.PI * 2);
    ctx.fill();
    
    ctx.restore();
  }
}

/**
 * Classe do Cano (Obstáculo)
 * Representa um par de canos (superior e inferior) com abertura no meio
 */
class Pipe extends Entity {
  /**
   * @param {number} x - Posição X inicial
   * @param {number} gapY - Posição Y da abertura (topo do gap)
   * @param {number} gapHeight - Altura da abertura (padrão: 120)
   */
  constructor(x, gapY, gapHeight = 120) {
    super(x, 0, 52, 600); // Altura total do canvas
    
    // Propriedades do cano
    this.speed = -4;           // Velocidade de movimento (pixels/frame)
    this.gapY = gapY;          // Posição Y da abertura
    this.gapHeight = gapHeight; // Altura da abertura
    this.scored = false;       // Flag para evitar contar duas vezes
    this.pipeColor = '#74BF2E';
    this.pipeOutline = '#543847';
  }

  /**
   * Atualiza a posição do cano
   * Move para a esquerda continuamente
   * 
   * @param {number} deltaTime - Tempo decorrido (em ms)
   */
  update(deltaTime) {
    // Mover cano para a esquerda
    this.x += this.speed;
  }

  /**
   * Renderiza o cano no canvas
   * Desenha dois retângulos (cano superior e inferior) com abertura no meio
   * 
   * @param {CanvasRenderingContext2D} ctx - Contexto 2D do canvas
   */
  render(ctx) {
    // Cano superior
    ctx.fillStyle = this.pipeColor;
    ctx.fillRect(this.x, 0, this.width, this.gapY);
    
    // Contorno do cano superior
    ctx.strokeStyle = this.pipeOutline;
    ctx.lineWidth = 2;
    ctx.strokeRect(this.x, 0, this.width, this.gapY);
    
    // Cano inferior
    const bottomPipeY = this.gapY + this.gapHeight;
    ctx.fillStyle = this.pipeColor;
    ctx.fillRect(this.x, bottomPipeY, this.width, this.height - bottomPipeY);
    
    // Contorno do cano inferior
    ctx.strokeStyle = this.pipeOutline;
    ctx.lineWidth = 2;
    ctx.strokeRect(this.x, bottomPipeY, this.width, this.height - bottomPipeY);
  }

  /**
   * Verifica se o cano saiu da tela
   * @returns {boolean} true se o cano está completamente fora da tela
   */
  isOffScreen() {
    return this.x + this.width < 0;
  }

  /**
   * Verifica se o cano já foi contado para pontuação
   * @returns {boolean} true se já foi contado
   */
  hasBeenScored() {
    return this.scored;
  }

  /**
   * Marca o cano como já contado para pontuação
   */
  markScored() {
    this.scored = true;
  }
}

/**
 * Classe do Chão
 * Implementa o chão com efeito de scroll contínuo
 */
class Ground extends Entity {
  /**
   * @param {number} y - Posição Y do chão
   * @param {number} width - Largura do canvas
   */
  constructor(y, width) {
    super(0, y, width, 50); // Altura padrão do chão
    
    this.speed = -4;           // Velocidade de movimento (pixels/frame)
    this.scrollOffset = 0;     // Offset para efeito de scroll contínuo
    this.tileWidth = 50;       // Largura de cada tile do padrão
  }

  /**
   * Atualiza a posição do chão
   * Implementa scroll contínuo com looping
   * 
   * @param {number} deltaTime - Tempo decorrido (em ms)
   */
  update(deltaTime) {
    // Atualizar offset de scroll
    this.scrollOffset += this.speed;
    
    // Resetar offset quando completa um ciclo
    if (this.scrollOffset <= -this.tileWidth) {
      this.scrollOffset += this.tileWidth;
    }
  }

  /**
   * Renderiza o chão no canvas
   * Desenha padrão alternado de cores com efeito de scroll
   * 
   * @param {CanvasRenderingContext2D} ctx - Contexto 2D do canvas
   */
  render(ctx) {
    const colors = ['#DED895', '#73BF2E']; // Bege e verde
    
    // Desenhar tiles do chão com offset de scroll
    for (let i = -1; i < Math.ceil(this.width / this.tileWidth) + 1; i++) {
      const tileX = i * this.tileWidth + this.scrollOffset;
      const colorIndex = (i % 2 + 2) % 2; // Alternar cores
      
      ctx.fillStyle = colors[colorIndex];
      ctx.fillRect(tileX, this.y, this.tileWidth, this.height);
      
      // Contorno
      ctx.strokeStyle = '#543847';
      ctx.lineWidth = 1;
      ctx.strokeRect(tileX, this.y, this.tileWidth, this.height);
    }
  }
}

/**
 * Classe do Planeta
 * Representa um planeta de fundo que se move lentamente
 */
class Planet extends Entity {
  /**
   * @param {number} x - Posição X inicial
   * @param {number} y - Posição Y inicial
   * @param {number} radius - Raio do planeta
   * @param {string} color - Cor do planeta
   */
  constructor(x, y, radius, color) {
    super(x, y, radius * 2, radius * 2);
    
    this.radius = radius;
    this.color = color;
    this.speed = -1; // Movimento lento (parallax)
    this.opacity = 0.6;
  }

  /**
   * Atualiza a posição do planeta
   * Move lentamente para a esquerda (parallax effect)
   * 
   * @param {number} deltaTime - Tempo decorrido (em ms)
   */
  update(deltaTime) {
    this.x += this.speed;
  }

  /**
   * Renderiza o planeta no canvas
   * Desenha um círculo com gradiente
   * 
   * @param {CanvasRenderingContext2D} ctx - Contexto 2D do canvas
   */
  render(ctx) {
    ctx.save();
    ctx.globalAlpha = this.opacity;
    
    // Criar gradiente radial para efeito 3D
    const gradient = ctx.createRadialGradient(
      this.x - this.radius / 3,
      this.y - this.radius / 3,
      0,
      this.x,
      this.y,
      this.radius
    );
    
    gradient.addColorStop(0, this.lightenColor(this.color, 30));
    gradient.addColorStop(1, this.color);
    
    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
    ctx.fill();
    
    // Contorno
    ctx.strokeStyle = this.darkenColor(this.color, 30);
    ctx.lineWidth = 2;
    ctx.stroke();
    
    ctx.restore();
  }

  /**
   * Verifica se o planeta saiu da tela
   * @returns {boolean} true se o planeta está completamente fora da tela
   */
  isOffScreen() {
    return this.x + this.radius < 0;
  }

  /**
   * Clareia uma cor (aumenta luminosidade)
   * @private
   * @param {string} color - Cor em formato hex
   * @param {number} percent - Percentual de clareza
   * @returns {string} Cor clarificada em formato hex
   */
  lightenColor(color, percent) {
    const num = parseInt(color.replace('#', ''), 16);
    const amt = Math.round(2.55 * percent);
    const R = Math.min(255, (num >> 16) + amt);
    const G = Math.min(255, (num >> 8 & 0x00FF) + amt);
    const B = Math.min(255, (num & 0x0000FF) + amt);
    return '#' + (0x1000000 + R * 0x10000 + G * 0x100 + B).toString(16).slice(1);
  }

  /**
   * Escurece uma cor (diminui luminosidade)
   * @private
   * @param {string} color - Cor em formato hex
   * @param {number} percent - Percentual de escuridão
   * @returns {string} Cor escurecida em formato hex
   */
  darkenColor(color, percent) {
    const num = parseInt(color.replace('#', ''), 16);
    const amt = Math.round(2.55 * percent);
    const R = Math.max(0, (num >> 16) - amt);
    const G = Math.max(0, (num >> 8 & 0x00FF) - amt);
    const B = Math.max(0, (num & 0x0000FF) - amt);
    return '#' + (0x1000000 + R * 0x10000 + G * 0x100 + B).toString(16).slice(1);
  }
}

/**
 * Sistema de Detecção de Colisão
 * Implementa AABB (Axis-Aligned Bounding Box) collision detection
 */
class CollisionDetector {
  /**
   * Verifica colisão AABB entre dois retângulos
   * 
   * Algoritmo AABB:
   * Dois retângulos colidem se se sobrepõem em AMBOS os eixos X e Y
   * 
   * Condição de colisão:
   * rect1.x + rect1.width >= rect2.x AND
   * rect1.x <= rect2.x + rect2.width AND
   * rect1.y + rect1.height >= rect2.y AND
   * rect1.y <= rect2.y + rect2.height
   * 
   * @static
   * @param {Object} rect1 - Primeiro retângulo {x, y, width, height}
   * @param {Object} rect2 - Segundo retângulo {x, y, width, height}
   * @returns {boolean} true se há colisão, false caso contrário
   */
  static checkAABB(rect1, rect2) {
    return (
      rect1.x + rect1.width >= rect2.x &&
      rect1.x <= rect2.x + rect2.width &&
      rect1.y + rect1.height >= rect2.y &&
      rect1.y <= rect2.y + rect2.height
    );
  }

  /**
   * Verifica colisão entre pássaro e cano
   * Verifica colisão com ambas as partes do cano (superior e inferior)
   * 
   * @static
   * @param {Bird} bird - Entidade do pássaro
   * @param {Pipe} pipe - Entidade do cano
   * @returns {boolean} true se há colisão, false caso contrário
   */
  static checkBirdPipeCollision(bird, pipe) {
    const birdBounds = bird.getBounds();
    
    // Cano superior
    const topPipeBounds = {
      x: pipe.x,
      y: 0,
      width: pipe.width,
      height: pipe.gapY
    };
    
    // Cano inferior
    const bottomPipeBounds = {
      x: pipe.x,
      y: pipe.gapY + pipe.gapHeight,
      width: pipe.width,
      height: pipe.height - (pipe.gapY + pipe.gapHeight)
    };
    
    // Verificar colisão com ambas as partes
    return (
      this.checkAABB(birdBounds, topPipeBounds) ||
      this.checkAABB(birdBounds, bottomPipeBounds)
    );
  }

  /**
   * Verifica colisão entre pássaro e chão
   * 
   * @static
   * @param {Bird} bird - Entidade do pássaro
   * @param {Ground} ground - Entidade do chão
   * @returns {boolean} true se há colisão, false caso contrário
   */
  static checkBirdGroundCollision(bird, ground) {
    const birdBounds = bird.getBounds();
    const groundBounds = ground.getBounds();
    
    return this.checkAABB(birdBounds, groundBounds);
  }

  /**
   * Verifica se o pássaro cruzou o cano (para pontuação)
   * O pássaro marca ponto quando seu centro X passa pelo centro X do cano
   * 
   * @static
   * @param {Bird} bird - Entidade do pássaro
   * @param {Pipe} pipe - Entidade do cano
   * @returns {boolean} true se o pássaro cruzou o cano, false caso contrário
   */
  static checkPipeScore(bird, pipe) {
    // Centro X do pássaro
    const birdCenterX = bird.x + bird.width / 2;
    
    // Centro X do cano
    const pipeCenterX = pipe.x + pipe.width / 2;
    
    // Pássaro marca ponto quando passa pelo centro do cano
    // e o cano ainda não foi contado
    return birdCenterX > pipeCenterX && !pipe.hasBeenScored();
  }

  /**
   * Verifica colisão com o teto (limite superior)
   * 
   * @static
   * @param {Bird} bird - Entidade do pássaro
   * @returns {boolean} true se o pássaro colidiu com o teto
   */
  static checkBirdCeilingCollision(bird) {
    return bird.y <= 0;
  }
}
