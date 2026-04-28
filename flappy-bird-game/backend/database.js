const sqlite3 = require('sqlite3').verbose();
const path = require('path');

// Caminho do banco de dados
const dbPath = path.join(__dirname, 'scores.db');

// Criar conexão com o banco de dados
const db = new sqlite3.Database(dbPath, (err) => {
  if (err) {
    console.error('Erro ao conectar ao banco de dados:', err.message);
  } else {
    console.log('Conectado ao banco de dados SQLite');
    initializeDatabase();
  }
});

/**
 * Inicializa o banco de dados criando a tabela de scores se não existir
 */
function initializeDatabase() {
  db.run(`
    CREATE TABLE IF NOT EXISTS scores (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      playerName TEXT NOT NULL,
      score INTEGER NOT NULL,
      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `, (err) => {
    if (err) {
      console.error('Erro ao criar tabela:', err.message);
    } else {
      console.log('Tabela de scores inicializada');
    }
  });
}

/**
 * Salva uma nova pontuação no banco de dados
 * @param {string} playerName - Nome do jogador (1-20 caracteres)
 * @param {number} score - Pontuação (inteiro não-negativo)
 * @returns {Promise<Object>} Objeto com id, playerName, score, timestamp
 */
function createScore(playerName, score) {
  return new Promise((resolve, reject) => {
    // Validação de entrada
    if (!playerName || typeof playerName !== 'string') {
      reject(new Error('Nome do jogador inválido'));
      return;
    }

    if (playerName.length < 1 || playerName.length > 20) {
      reject(new Error('Nome deve ter entre 1 e 20 caracteres'));
      return;
    }

    if (typeof score !== 'number' || score < 0 || !Number.isInteger(score)) {
      reject(new Error('Pontuação deve ser um inteiro não-negativo'));
      return;
    }

    // Sanitizar nome do jogador (remover caracteres perigosos)
    const sanitizedName = playerName.trim().substring(0, 20);

    // Inserir no banco de dados
    db.run(
      'INSERT INTO scores (playerName, score) VALUES (?, ?)',
      [sanitizedName, score],
      function(err) {
        if (err) {
          reject(err);
        } else {
          // Retornar o score salvo com id e timestamp
          db.get(
            'SELECT id, playerName, score, timestamp FROM scores WHERE id = ?',
            [this.lastID],
            (err, row) => {
              if (err) {
                reject(err);
              } else {
                resolve(row);
              }
            }
          );
        }
      }
    );
  });
}

/**
 * Obtém as top N pontuações ordenadas por score descendente
 * @param {number} limit - Número máximo de scores a retornar (padrão: 10)
 * @returns {Promise<Array>} Array de scores
 */
function getTopScores(limit = 10) {
  return new Promise((resolve, reject) => {
    // Validar limit
    if (typeof limit !== 'number' || limit < 1) {
      limit = 10;
    }
    limit = Math.min(limit, 100); // Máximo de 100 para evitar sobrecarga

    db.all(
      'SELECT id, playerName, score, timestamp FROM scores ORDER BY score DESC LIMIT ?',
      [limit],
      (err, rows) => {
        if (err) {
          reject(err);
        } else {
          resolve(rows || []);
        }
      }
    );
  });
}

/**
 * Obtém todas as pontuações
 * @returns {Promise<Array>} Array de todos os scores
 */
function getAllScores() {
  return new Promise((resolve, reject) => {
    db.all(
      'SELECT id, playerName, score, timestamp FROM scores ORDER BY score DESC',
      (err, rows) => {
        if (err) {
          reject(err);
        } else {
          resolve(rows || []);
        }
      }
    );
  });
}

/**
 * Limpa todos os scores (apenas para desenvolvimento/testes)
 * @returns {Promise<void>}
 */
function clearAllScores() {
  return new Promise((resolve, reject) => {
    db.run('DELETE FROM scores', (err) => {
      if (err) {
        reject(err);
      } else {
        console.log('Todos os scores foram removidos');
        resolve();
      }
    });
  });
}

/**
 * Fecha a conexão com o banco de dados
 */
function closeDatabase() {
  db.close((err) => {
    if (err) {
      console.error('Erro ao fechar banco de dados:', err.message);
    } else {
      console.log('Conexão com banco de dados fechada');
    }
  });
}

module.exports = {
  createScore,
  getTopScores,
  getAllScores,
  clearAllScores,
  closeDatabase
};
