# 📡 Exemplos de Uso da API

## Endpoints Disponíveis

### 1. GET /api/scores
Retorna as 10 maiores pontuações ordenadas de forma decrescente.

**URL**: `http://localhost:3000/api/scores`

**Método**: GET

**Query Parameters**:
- `limit` (opcional): Número máximo de scores a retornar (padrão: 10, máximo: 100)

**Exemplos**:

```bash
# Obter top 10 (padrão)
curl http://localhost:3000/api/scores

# Obter top 5
curl http://localhost:3000/api/scores?limit=5

# Obter top 20
curl http://localhost:3000/api/scores?limit=20
```

**Resposta (200 OK)**:
```json
[
  {
    "id": 1,
    "playerName": "Douglas",
    "score": 150,
    "timestamp": "2026-04-24T10:30:45.000Z"
  },
  {
    "id": 2,
    "playerName": "Maria",
    "score": 120,
    "timestamp": "2026-04-24T10:25:30.000Z"
  },
  {
    "id": 3,
    "playerName": "João",
    "score": 95,
    "timestamp": "2026-04-24T10:20:15.000Z"
  }
]
```

---

### 2. POST /api/scores
Salva uma nova pontuação no banco de dados.

**URL**: `http://localhost:3000/api/scores`

**Método**: POST

**Headers**:
```
Content-Type: application/json
```

**Body**:
```json
{
  "name": "PlayerName",
  "score": 100
}
```

**Validações**:
- `name`: String de 1-20 caracteres (obrigatório)
- `score`: Inteiro não-negativo (obrigatório)

**Exemplos**:

```bash
# Salvar score básico
curl -X POST http://localhost:3000/api/scores \
  -H "Content-Type: application/json" \
  -d '{"name":"Douglas","score":150}'

# Salvar score com nome com espaços
curl -X POST http://localhost:3000/api/scores \
  -H "Content-Type: application/json" \
  -d '{"name":"João Silva","score":120}'

# Salvar score com pontuação alta
curl -X POST http://localhost:3000/api/scores \
  -H "Content-Type: application/json" \
  -d '{"name":"Champion","score":999}'
```

**Resposta (201 Created)**:
```json
{
  "id": 4,
  "playerName": "Douglas",
  "score": 150,
  "timestamp": "2026-04-24T10:35:00.000Z"
}
```

**Resposta de Erro (400 Bad Request)**:
```json
{
  "error": "Nome deve ter entre 1 e 20 caracteres"
}
```

```json
{
  "error": "Pontuação deve ser um inteiro não-negativo"
}
```

**Resposta de Erro (500 Internal Server Error)**:
```json
{
  "error": "Erro ao salvar pontuação"
}
```

---

### 3. GET /api/health
Health check para verificar se o servidor está disponível.

**URL**: `http://localhost:3000/api/health`

**Método**: GET

**Exemplo**:
```bash
curl http://localhost:3000/api/health
```

**Resposta (200 OK)**:
```json
{
  "status": "ok",
  "message": "Servidor está funcionando"
}
```

---

### 4. GET /api/scores/all
Retorna todas as pontuações (apenas para desenvolvimento).

**URL**: `http://localhost:3000/api/scores/all`

**Método**: GET

**Exemplo**:
```bash
curl http://localhost:3000/api/scores/all
```

**Resposta (200 OK)**:
```json
[
  {
    "id": 1,
    "playerName": "Douglas",
    "score": 150,
    "timestamp": "2026-04-24T10:30:45.000Z"
  },
  {
    "id": 2,
    "playerName": "Maria",
    "score": 120,
    "timestamp": "2026-04-24T10:25:30.000Z"
  }
]
```

---

## Testando com JavaScript (Fetch API)

### Obter Top Scores

```javascript
// Obter top 10 scores
fetch('http://localhost:3000/api/scores')
  .then(response => response.json())
  .then(scores => {
    console.log('Top 10 Scores:', scores);
    scores.forEach((score, index) => {
      console.log(`${index + 1}. ${score.playerName}: ${score.score}`);
    });
  })
  .catch(error => console.error('Erro:', error));
```

### Salvar Nova Pontuação

```javascript
// Salvar score
const playerName = 'Douglas';
const score = 150;

fetch('http://localhost:3000/api/scores', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: playerName,
    score: score
  })
})
  .then(response => response.json())
  .then(savedScore => {
    console.log('Score salvo:', savedScore);
    console.log(`ID: ${savedScore.id}`);
    console.log(`Nome: ${savedScore.playerName}`);
    console.log(`Pontuação: ${savedScore.score}`);
    console.log(`Data: ${savedScore.timestamp}`);
  })
  .catch(error => console.error('Erro ao salvar:', error));
```

### Fluxo Completo (Salvar e Buscar Ranking)

```javascript
async function saveScoreAndGetRanking(playerName, score) {
  try {
    // 1. Salvar score
    const saveResponse = await fetch('http://localhost:3000/api/scores', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: playerName,
        score: score
      })
    });

    if (!saveResponse.ok) {
      throw new Error(`Erro ao salvar: ${saveResponse.status}`);
    }

    const savedScore = await saveResponse.json();
    console.log('✅ Score salvo:', savedScore);

    // 2. Buscar ranking atualizado
    const rankingResponse = await fetch('http://localhost:3000/api/scores?limit=10');
    
    if (!rankingResponse.ok) {
      throw new Error(`Erro ao buscar ranking: ${rankingResponse.status}`);
    }

    const ranking = await rankingResponse.json();
    console.log('🏆 Ranking atualizado:');
    
    ranking.forEach((entry, index) => {
      const marker = entry.id === savedScore.id ? '👉' : '  ';
      console.log(`${marker} ${index + 1}. ${entry.playerName}: ${entry.score}`);
    });

    return { savedScore, ranking };
  } catch (error) {
    console.error('❌ Erro:', error);
  }
}

// Usar a função
saveScoreAndGetRanking('Douglas', 150);
```

---

## Testando com Postman

### 1. Criar Requisição GET

1. Abra Postman
2. Clique em "New" → "Request"
3. Selecione "GET"
4. URL: `http://localhost:3000/api/scores`
5. Clique em "Send"

### 2. Criar Requisição POST

1. Clique em "New" → "Request"
2. Selecione "POST"
3. URL: `http://localhost:3000/api/scores`
4. Vá para "Body" → "raw" → "JSON"
5. Cole:
```json
{
  "name": "Douglas",
  "score": 150
}
```
6. Clique em "Send"

---

## Testando com cURL

### Obter Scores

```bash
# Top 10
curl http://localhost:3000/api/scores

# Top 5
curl http://localhost:3000/api/scores?limit=5

# Todos
curl http://localhost:3000/api/scores/all
```

### Salvar Score

```bash
# Score simples
curl -X POST http://localhost:3000/api/scores \
  -H "Content-Type: application/json" \
  -d '{"name":"Douglas","score":150}'

# Score com nome com espaços
curl -X POST http://localhost:3000/api/scores \
  -H "Content-Type: application/json" \
  -d '{"name":"João Silva","score":120}'

# Score com pontuação alta
curl -X POST http://localhost:3000/api/scores \
  -H "Content-Type: application/json" \
  -d '{"name":"Champion","score":999}'
```

### Health Check

```bash
curl http://localhost:3000/api/health
```

---

## Casos de Teste

### ✅ Casos Válidos

```bash
# Nome válido, score válido
curl -X POST http://localhost:3000/api/scores \
  -H "Content-Type: application/json" \
  -d '{"name":"Douglas","score":150}'

# Nome com espaços
curl -X POST http://localhost:3000/api/scores \
  -H "Content-Type: application/json" \
  -d '{"name":"João Silva","score":120}'

# Score zero
curl -X POST http://localhost:3000/api/scores \
  -H "Content-Type: application/json" \
  -d '{"name":"Beginner","score":0}'

# Score alto
curl -X POST http://localhost:3000/api/scores \
  -H "Content-Type: application/json" \
  -d '{"name":"Expert","score":9999}'
```

### ❌ Casos Inválidos

```bash
# Nome vazio
curl -X POST http://localhost:3000/api/scores \
  -H "Content-Type: application/json" \
  -d '{"name":"","score":100}'
# Resposta: 400 - "Nome do jogador é obrigatório"

# Nome muito longo (> 20 caracteres)
curl -X POST http://localhost:3000/api/scores \
  -H "Content-Type: application/json" \
  -d '{"name":"EsteNomeTemMaisDe20Caracteres","score":100}'
# Resposta: 400 - "Nome deve ter entre 1 e 20 caracteres"

# Score negativo
curl -X POST http://localhost:3000/api/scores \
  -H "Content-Type: application/json" \
  -d '{"name":"Douglas","score":-10}'
# Resposta: 400 - "Pontuação deve ser um inteiro não-negativo"

# Score não é inteiro
curl -X POST http://localhost:3000/api/scores \
  -H "Content-Type: application/json" \
  -d '{"name":"Douglas","score":150.5}'
# Resposta: 400 - "Pontuação deve ser um inteiro não-negativo"

# Score faltando
curl -X POST http://localhost:3000/api/scores \
  -H "Content-Type: application/json" \
  -d '{"name":"Douglas"}'
# Resposta: 400 - "Pontuação deve ser um inteiro não-negativo"

# Nome faltando
curl -X POST http://localhost:3000/api/scores \
  -H "Content-Type: application/json" \
  -d '{"score":100}'
# Resposta: 400 - "Nome do jogador é obrigatório"
```

---

## Resposta de Erros

### 400 Bad Request
Validação falhou (nome inválido, score inválido, etc)

```json
{
  "error": "Descrição do erro"
}
```

### 404 Not Found
Rota não existe

```json
{
  "error": "Rota não encontrada"
}
```

### 500 Internal Server Error
Erro no servidor (banco de dados, etc)

```json
{
  "error": "Erro ao salvar pontuação"
}
```

---

## Performance

### Tempo de Resposta Esperado

| Endpoint | Método | Tempo Esperado |
|----------|--------|----------------|
| /api/scores | GET | < 100ms |
| /api/scores?limit=100 | GET | < 200ms |
| /api/scores | POST | < 300ms |
| /api/health | GET | < 50ms |

### Teste de Carga

```bash
# Salvar 100 scores rapidamente
for i in {1..100}; do
  curl -X POST http://localhost:3000/api/scores \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"Player$i\",\"score\":$((RANDOM % 1000))}"
done
```

---

## Integração com Frontend

O frontend usa a classe `ScoreAPI` em `frontend/api.js`:

```javascript
// Obter top scores
const scores = await ScoreAPI.getTopScores(10);

// Salvar score
const savedScore = await ScoreAPI.saveScore('Douglas', 150);

// Verificar saúde do servidor
const isHealthy = await ScoreAPI.checkServerHealth();
```

---

## Dicas

1. **Use Postman** para testar endpoints rapidamente
2. **Use cURL** para automação e scripts
3. **Use DevTools** (F12) para ver requisições do frontend
4. **Verifique logs** do servidor para debug
5. **Teste casos inválidos** para garantir validação

---

**Pronto para testar a API! 🚀**
