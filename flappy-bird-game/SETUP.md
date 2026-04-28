# 🚀 Setup Rápido - Flappy Bird Space Edition

## Passo 1: Instalar Dependências

```bash
cd backend
npm install
```

## Passo 2: Iniciar o Servidor

```bash
npm start
```

Você verá:
```
🎮 Servidor Flappy Bird rodando em http://localhost:3000
📊 API de scores disponível em http://localhost:3000/api/scores
```

## Passo 3: Abrir no Navegador

Abra seu navegador e acesse:
```
http://localhost:3000
```

## 🎮 Pronto para Jogar!

- **Espaço** ou **Clique** para pular
- Evite os canos verdes
- Ganhe 1 ponto a cada cano que passar
- Salve sua pontuação no ranking

## 📁 Arquivos Criados

```
backend/
├── server.js          ✅ Servidor Express com API REST
├── database.js        ✅ SQLite com persistência de scores
└── package.json       ✅ Dependências (express, cors, sqlite3)

frontend/
├── index.html         ✅ Estrutura HTML com canvas
├── style.css          ✅ Estilos com tema espacial
├── game.js            ✅ Game engine com loop 60 FPS
├── entities.js        ✅ Classes Bird, Pipe, Ground, Planet
└── api.js             ✅ Cliente HTTP para backend

.kiro/specs/
├── design.md          ✅ Arquitetura e design técnico
├── requirements.md    ✅ Requisitos funcionais
└── tasks.md           ✅ Plano de implementação

README.md              ✅ Documentação completa
SETUP.md              ✅ Este arquivo
.gitignore            ✅ Configuração Git
```

## ✨ Customizações Implementadas

### 🌌 Fundo Espacial com Planetas
- Fundo escuro com estrelas
- Planetas coloridos que se movem em parallax
- Novos planetas aparecem a cada 8 segundos
- Cores variadas: vermelho, ciano, azul, laranja, verde

### 📊 Sistema de Pontuação
- Incrementa 1 ponto a cada cano atravessado
- Pontuação exibida em tempo real no HUD
- High score salvo em localStorage
- Ranking das 10 maiores pontuações

## 🎨 Tema Visual

- **Espaço**: Fundo azul escuro com estrelas
- **Pássaro**: Círculo amarelo com olho
- **Canos**: Retângulos verdes com contorno escuro
- **Chão**: Padrão alternado bege/verde
- **Planetas**: Círculos com gradiente e cores variadas

## 🔧 Troubleshooting

### Porta 3000 já está em uso?
```bash
PORT=3001 npm start
```

### Erro de módulo não encontrado?
```bash
cd backend
npm install
```

### Scores não salvam?
1. Verifique se o servidor está rodando
2. Abra DevTools (F12) → Network
3. Verifique erros de CORS

## 📱 Testar em Mobile

1. Descubra seu IP local:
```bash
ipconfig getifaddr en0  # macOS/Linux
ipconfig               # Windows
```

2. Acesse no mobile:
```
http://SEU_IP:3000
```

## 🎯 Próximos Passos (Opcional)

- Adicionar sons e música
- Implementar diferentes níveis de dificuldade
- Adicionar power-ups
- Criar animações mais complexas
- Implementar multiplayer

## 📞 Suporte

Se encontrar problemas:
1. Verifique se Node.js está instalado: `node --version`
2. Verifique se npm está instalado: `npm --version`
3. Limpe cache: `npm cache clean --force`
4. Reinstale dependências: `rm -rf node_modules && npm install`

---

**Divirta-se! 🎮✨**
