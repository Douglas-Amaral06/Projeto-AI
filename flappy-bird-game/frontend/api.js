/**
 * API Client para comunicação com o backend
 * Gerencia requisições HTTP para salvar e recuperar pontuações
 */

class ScoreAPI {
  /**
   * URL base da API
   */
  static BASE_URL = 'http://localhost:3000/api';

  /**
   * Timeout padrão para requisições (em ms)
   */
  static TIMEOUT = 5000;

  /**
   * Obtém as top N pontuações do servidor
   * @param {number} limit - Número máximo de scores a retornar (padrão: 10)
   * @returns {Promise<Array>} Array de scores ordenados por pontuação descendente
   * @throws {Error} Se a requisição falhar
   */
  static async getTopScores(limit = 10) {
    try {
      const response = await this._fetchWithTimeout(
        `${this.BASE_URL}/scores?limit=${limit}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );

      if (!response.ok) {
        throw new Error(`Erro ao buscar scores: ${response.status}`);
      }

      const scores = await response.json();
      return scores;
    } catch (error) {
      console.error('Erro ao buscar top scores:', error);
      throw error;
    }
  }

  /**
   * Salva uma nova pontuação no servidor
   * @param {string} playerName - Nome do jogador (1-20 caracteres)
   * @param {number} score - Pontuação (inteiro não-negativo)
   * @returns {Promise<Object>} Objeto com id, playerName, score, timestamp
   * @throws {Error} Se a requisição falhar ou validação falhar
   */
  static async saveScore(playerName, score) {
    try {
      // Validação local
      if (!playerName || typeof playerName !== 'string') {
        throw new Error('Nome do jogador é obrigatório');
      }

      if (playerName.length < 1 || playerName.length > 20) {
        throw new Error('Nome deve ter entre 1 e 20 caracteres');
      }

      if (typeof score !== 'number' || score < 0 || !Number.isInteger(score)) {
        throw new Error('Pontuação deve ser um inteiro não-negativo');
      }

      const response = await this._fetchWithTimeout(
        `${this.BASE_URL}/scores`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            name: playerName.trim(),
            score: score
          })
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `Erro ao salvar score: ${response.status}`);
      }

      const savedScore = await response.json();
      return savedScore;
    } catch (error) {
      console.error('Erro ao salvar score:', error);
      throw error;
    }
  }

  /**
   * Obtém todas as pontuações (apenas para desenvolvimento)
   * @returns {Promise<Array>} Array de todos os scores
   * @throws {Error} Se a requisição falhar
   */
  static async getAllScores() {
    try {
      const response = await this._fetchWithTimeout(
        `${this.BASE_URL}/scores/all`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );

      if (!response.ok) {
        throw new Error(`Erro ao buscar todos os scores: ${response.status}`);
      }

      const scores = await response.json();
      return scores;
    } catch (error) {
      console.error('Erro ao buscar todos os scores:', error);
      throw error;
    }
  }

  /**
   * Verifica se o servidor está disponível
   * @returns {Promise<boolean>} true se servidor está ok, false caso contrário
   */
  static async checkServerHealth() {
    try {
      const response = await this._fetchWithTimeout(
        `${this.BASE_URL}/health`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );

      return response.ok;
    } catch (error) {
      console.warn('Servidor não está disponível:', error);
      return false;
    }
  }

  /**
   * Wrapper para fetch com timeout
   * @private
   * @param {string} url - URL da requisição
   * @param {Object} options - Opções do fetch
   * @returns {Promise<Response>} Response do fetch
   * @throws {Error} Se timeout ou erro de rede
   */
  static async _fetchWithTimeout(url, options = {}) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.TIMEOUT);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal
      });
      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      if (error.name === 'AbortError') {
        throw new Error('Requisição expirou (timeout)');
      }
      throw error;
    }
  }

  /**
   * Formata um score para exibição
   * @static
   * @param {Object} score - Objeto score com id, playerName, score, timestamp
   * @returns {Object} Score formatado
   */
  static formatScore(score) {
    return {
      ...score,
      formattedDate: new Date(score.timestamp).toLocaleDateString('pt-BR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    };
  }
}

// Exportar para uso global
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ScoreAPI;
}
