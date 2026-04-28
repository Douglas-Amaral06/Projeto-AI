# 🔧 Troubleshooting - Flappy Bird Space Edition

## ❌ Problemas Comuns e Soluções

### 1. "Cannot find module 'express'"

**Problema**: Erro ao iniciar o servidor

**Solução**:
```bash
cd backend
npm install
```

**Verificar**:
```bash
npm list express
```

---

### 2. "Port 3000 already in use"

**Problema**: Porta 3000 já está sendo usada

**Solução 1 - Usar outra porta**:
```bash
PORT=3001 npm start
```

**Solução 2 - Matar processo na porta 3000**:

Windows:
```bash
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

macOS/Linux:
```bash
lsof -i :3000
kill -9 <PID>
```

---

### 3. "Canvas not found"

**Problema**: Canvas não está sendo renderizado

**Verificar**:
1. Abra DevTools (F12)
2. Vá para Console
3. Procure por erros

**Solução**:
- Certifique-se de que `index.html` está sendo servido
- Verifique se o canvas tem id="gameCanvas"
- Recarregue a página (Ctrl+Shift+R)

---

### 4. "Scores não salvam"

**Problema**: Pontuações não aparecem no ranking

**Verificar**:
1. Abra DevTools (F12)
2. Vá para Network
3. Clique em "Salvar Pontuação"
4. Procure pela requisição POST /api/scores

**Possíveis Causas**:

**A) Servidor não está rodando**
```bash
# Verificar se servidor está rodando
curl http://localhost:3000/api/health
```

**B) Erro de CORS**
- Verifique se CORS está habilitado em `backend/server.js`
- Deve ter: `app.use(cors());`

**C) Erro de validação**
- Nome deve ter 1-20 caracteres
- Score deve ser um inteiro não-negativo
- Verifique a aba Network para ver a resposta de erro

**D) Banco de dados não está acessível**
- Verifique se `backend/scores.db` foi criado
- Verifique permissões de arquivo

---

### 5. "Erro 404 ao acessar http://localhost:3000"

**Problema**: Página não encontrada

**Verificar**:
1. Servidor está rodando? `npm start`
2. Porta correta? (padrão: 3000)
3. URL correta? `http://localhost:3000`

**Solução**:
```bash
# Reiniciar servidor
npm start

# Ou com porta diferente
PORT=3001 npm start
```

---

### 6. "Jogo não responde aos controles"

**Problema**: Espaço/clique/toque não funciona

**Verificar**:
1. Canvas está focado? (clique nele)
2. Jogo está em estado "playing"?
3. Abra DevTools e procure por erros

**Solução**:
- Recarregue a página
- Limpe cache do navegador (Ctrl+Shift+Delete)
- Tente em outro navegador

---

### 7. "Jogo está muito lento (lag)"

**Problema**: FPS baixo, jogo travando

**Verificar**:
1. Abra DevTools (F12)
2. Vá para Performance
3. Grave um frame
4. Procure por gargalos

**Possíveis Causas**:

**A) Muitos canos na tela**
- Verifique se canos off-screen estão sendo removidos
- Edite `PIPE_SPAWN_INTERVAL` em `frontend/game.js`

**B) Muitos planetas na tela**
- Edite `PLANET_SPAWN_INTERVAL` em `frontend/game.js`

**C) Renderização ineficiente**
- Verifique se canvas está sendo limpo a cada frame
- Verifique se há loops desnecessários

**D) Computador sobrecarregado**
- Feche outras abas/programas
- Reinicie o navegador

---

### 8. "Erro: 'this' is undefined"

**Problema**: Erro de contexto em métodos

**Solução**:
- Verifique se métodos estão usando arrow functions
- Exemplo correto:
```javascript
gameLoop = () => {
  // 'this' funciona aqui
}
```

---

### 9. "Banco de dados corrompido"

**Problema**: Erros ao salvar/buscar scores

**Solução**:
1. Parar servidor (Ctrl+C)
2. Deletar arquivo de banco de dados:
```bash
rm backend/scores.db
```
3. Reiniciar servidor:
```bash
npm start
```

---

### 10. "Erro de CORS: No 'Access-Control-Allow-Origin' header"

**Problema**: Frontend não consegue acessar backend

**Verificar**:
- CORS está habilitado em `backend/server.js`?
- Deve ter: `app.use(cors());`

**Solução**:
```javascript
// Em backend/server.js
const cors = require('cors');
app.use(cors());
```

---

### 11. "Erro: 'fetch' is not defined"

**Problema**: Fetch API não está disponível

**Solução**:
- Use navegador moderno (Chrome 41+, Firefox 39+, Safari 10.1+)
- Verifique se está em HTTPS ou localhost

---

### 12. "Erro: 'localStorage' is not defined"

**Problema**: localStorage não está disponível

**Solução**:
- Verifique se está em contexto de navegador (não Node.js)
- Verifique se cookies/storage estão habilitados

---

### 13. "Pontuação não incrementa"

**Problema**: Score fica em 0

**Verificar**:
1. Pássaro está passando pelos canos?
2. Colisão está sendo detectada?

**Solução**:
- Verifique se `checkPipeScore()` está sendo chamado
- Verifique se flag `scored` está funcionando
- Adicione console.log para debug:
```javascript
if (CollisionDetector.checkPipeScore(this.bird, pipe)) {
  console.log('Score!', this.score);
  this.score++;
  pipe.markScored();
}
```

---

### 14. "Planetas não aparecem"

**Problema**: Fundo vazio sem planetas

**Verificar**:
1. Função `spawnPlanet()` está sendo chamada?
2. Planetas estão sendo renderizados?

**Solução**:
- Verifique `PLANET_SPAWN_INTERVAL` em `frontend/game.js`
- Aumente o intervalo se necessário:
```javascript
static PLANET_SPAWN_INTERVAL = 4000; // Mais frequente
```

---

### 15. "Erro: 'Cannot read property x of undefined'"

**Problema**: Entidade não foi inicializada

**Solução**:
- Verifique se `bird`, `ground`, `pipes` foram criados
- Adicione verificações:
```javascript
if (this.bird && this.bird.isAlive) {
  this.bird.update(deltaTime);
}
```

---

## 🔍 Debug Tips

### 1. Ativar Logs

Adicione em `frontend/game.js`:
```javascript
console.log('Score:', this.score);
console.log('State:', this.gameState);
console.log('Bird Y:', this.bird.y);
console.log('Pipes:', this.pipes.length);
```

### 2. Usar DevTools

**Chrome/Firefox/Edge**:
- F12 para abrir DevTools
- Console para ver erros
- Network para ver requisições
- Performance para profiling

### 3. Testar API Manualmente

```bash
# Testar GET
curl http://localhost:3000/api/scores

# Testar POST
curl -X POST http://localhost:3000/api/scores \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","score":100}'
```

### 4. Verificar Banco de Dados

```bash
# Instalar sqlite3 CLI
npm install -g sqlite3

# Abrir banco de dados
sqlite3 backend/scores.db

# Ver tabelas
.tables

# Ver dados
SELECT * FROM scores;

# Sair
.quit
```

### 5. Monitorar Servidor

```bash
# Ver logs em tempo real
npm start

# Ou com nodemon (auto-restart)
npm install -g nodemon
nodemon backend/server.js
```

---

## 📱 Problemas em Mobile

### 1. "Toque não funciona"

**Solução**:
- Verifique se `touchstart` listener está configurado
- Teste em navegador mobile real (não emulador)

### 2. "Canvas muito pequeno"

**Solução**:
- Verifique viewport meta tag:
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```

### 3. "Scroll horizontal/vertical"

**Solução**:
- Adicione em CSS:
```css
body {
  overflow: hidden;
  margin: 0;
  padding: 0;
}
```

---

## 🌐 Problemas de Rede

### 1. "Servidor não responde"

**Verificar**:
```bash
# Ping servidor
curl -I http://localhost:3000

# Verificar porta
netstat -an | grep 3000
```

### 2. "Timeout em requisições"

**Solução**:
- Aumentar timeout em `frontend/api.js`:
```javascript
static TIMEOUT = 10000; // 10 segundos
```

### 3. "Erro 500 do servidor"

**Verificar**:
1. Logs do servidor
2. Banco de dados acessível
3. Permissões de arquivo

---

## 🆘 Quando Nada Funciona

### 1. Limpar Tudo

```bash
# Parar servidor
# Ctrl+C

# Deletar node_modules
rm -rf backend/node_modules

# Deletar banco de dados
rm backend/scores.db

# Reinstalar
cd backend
npm install

# Reiniciar
npm start
```

### 2. Verificar Versões

```bash
node --version    # Deve ser 14+
npm --version     # Deve ser 6+
```

### 3. Atualizar npm

```bash
npm install -g npm@latest
```

### 4. Limpar Cache npm

```bash
npm cache clean --force
```

---

## 📞 Suporte

Se o problema persistir:

1. **Verifique os logs** do servidor e navegador
2. **Procure por erros** em DevTools (F12)
3. **Teste em outro navegador**
4. **Reinicie tudo** (servidor, navegador, computador)
5. **Leia a documentação** (README.md, API_EXAMPLES.md)

---

**Boa sorte! 🍀**
