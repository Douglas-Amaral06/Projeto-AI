const express = require('express');
const cors = require('cors');
const path = require('path');
const db = require('./database');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, '../frontend')));

/**
 * GET /
 * Serve o arquivo index.html (frontend)
 */
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, '../frontend/index.html'));
});

/**
 * GET /api/scores
 * Retorna as 10 maiores pontuações ordenadas de forma decrescente
 * Query params:
 *   - limit: número de scores a retornar (padrão: 10, máximo: 100)
 */
app.get('/api/scores', async (req, res) => {
  try {
    const limit = Math.min(parseInt(req.query.limit) || 10, 100);
    const scores = await db.getTopScores(limit);
    res.json(scores);
  } catch (error) {
    console.error('Erro ao buscar scores:', error);
    res.status(500).json({ error: 'Erro ao buscar pontuações' });
  }
});

/**
 * POST /api/scores
 * Salva uma nova pontuação no banco de dados
 * Body:
 *   - name: string (1-20 caracteres) - nome do jogador
 *   - score: number (inteiro não-negativo) - pontuação
 */
app.post('/api/scores', async (req, res) => {
  try {
    const { name, score } = req.body;

    // Validação básica
    if (!name || typeof name !== 'string') {
      return res.status(400).json({ error: 'Nome do jogador é obrigatório' });
    }

    if (typeof score !== 'number' || score < 0 || !Number.isInteger(score)) {
      return res.status(400).json({ error: 'Pontuação deve ser um inteiro não-negativo' });
    }

    if (name.length < 1 || name.length > 20) {
      return res.status(400).json({ error: 'Nome deve ter entre 1 e 20 caracteres' });
    }

    // Salvar score no banco de dados
    const savedScore = await db.createScore(name, score);
    res.status(201).json(savedScore);
  } catch (error) {
    console.error('Erro ao salvar score:', error);
    res.status(500).json({ error: 'Erro ao salvar pontuação' });
  }
});

/**
 * GET /api/scores/all
 * Retorna todas as pontuações (apenas para desenvolvimento)
 */
app.get('/api/scores/all', async (req, res) => {
  try {
    const scores = await db.getAllScores();
    res.json(scores);
  } catch (error) {
    console.error('Erro ao buscar todos os scores:', error);
    res.status(500).json({ error: 'Erro ao buscar pontuações' });
  }
});

/**
 * Health check endpoint
 */
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', message: 'Servidor está funcionando' });
});

/**
 * Tratamento de erros 404
 */
app.use((req, res) => {
  res.status(404).json({ error: 'Rota não encontrada' });
});

/**
 * Tratamento de erros global
 */
app.use((err, req, res, next) => {
  console.error('Erro não tratado:', err);
  res.status(500).json({ error: 'Erro interno do servidor' });
});

/**
 * Inicia o servidor
 */
app.listen(PORT, () => {
  console.log(`🎮 Servidor Flappy Bird rodando em http://localhost:${PORT}`);
  console.log(`📊 API de scores disponível em http://localhost:${PORT}/api/scores`);
});

/**
 * Tratamento de encerramento gracioso
 */
process.on('SIGINT', () => {
  console.log('\n🛑 Encerrando servidor...');
  db.closeDatabase();
  process.exit(0);
});
