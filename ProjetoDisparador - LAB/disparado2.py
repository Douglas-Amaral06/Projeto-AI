import sys
import json
import time
import random
import threading
import traceback
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# ─────────────────────────────────────────────
# BASE_DIR
# ─────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

# Carrega variáveis de ambiente do .env
load_dotenv(BASE_DIR / ".env")

CHROME_PROFILE = Path.home() / "AppData" / "Local" / "DisparadorRH_Profile"
CONFIG_FILE    = BASE_DIR / "config.json"
HISTORICO_FILE = BASE_DIR / "historico_envios.txt"
ERROS_FILE     = BASE_DIR / "erros.txt"
DEBUG_FILE     = BASE_DIR / "debug.log"

def _debug(msg: str):
    """Grava log de diagnóstico em arquivo — útil quando rodando como .exe sem console."""
    try:
        with open(DEBUG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {msg}\n")
    except Exception:
        pass

# ─────────────────────────────────────────────
# GEMINI AI - GERAÇÃO DE VARIAÇÕES (LangChain com Gemini 2.5)
# ─────────────────────────────────────────────
def gerar_variacoes_ia(texto_base: str, num_variacoes: int = 7, api_key: str = None) -> list:
    """
    Gera variações do texto usando Gemini 2.5 Flash via LangChain.
    Preserva variáveis como [NOME] e mantém tom profissional.
    """
    try:
        # Prioriza api_key passada como parâmetro, depois .env, depois config.json
        if not api_key:
            api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            config = carregar_config()
            api_key = config.get("api_key_gemini", "")
        
        if not api_key:
            raise ValueError("Chave da API do Gemini não configurada. Configure na aba Configurações.")
        
        # Blindagem: remove espaços, quebras de linha e caracteres invisíveis
        api_key = api_key.strip()
        
        # Debug para validação
        print(f"DEBUG IA: Enviando chave de tamanho {len(api_key)}: {api_key[:8]}...")
        _debug(f"gerar_variacoes_ia: API key length={len(api_key)}, preview={api_key[:8]}...")
        
        # Instancia Gemini 2.5 Flash com temperature=0.7 para variações criativas
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.7,
            google_api_key=api_key
        )
        
        prompt = f"""Gere exatamente {num_variacoes} variações diferentes do texto abaixo.

REGRAS OBRIGATÓRIAS:
1. Mantenha o mesmo sentido e tom profissional
2. Preserve OBRIGATORIAMENTE todas as variáveis entre colchetes como [NOME], [EMPRESA], etc.
3. Cada variação deve ser única e natural
4. Não numere as variações
5. Separe cada variação com uma linha contendo apenas "---"
6. Não adicione explicações, apenas as variações

TEXTO BASE:
{texto_base}

FORMATO DE SAÍDA:
Primeira variação aqui
---
Segunda variação aqui
---
Terceira variação aqui
(e assim por diante)"""

        # Dispara a requisição
        resposta = llm.invoke(prompt)
        
        # Extrai o texto retornado
        texto_resposta = resposta.content.strip()
        variacoes = [v.strip() for v in texto_resposta.split("---") if v.strip()]
        
        # Garante que temos exatamente o número solicitado
        if len(variacoes) < num_variacoes:
            # Se retornou menos, completa com o texto base
            while len(variacoes) < num_variacoes:
                variacoes.append(texto_base)
        elif len(variacoes) > num_variacoes:
            # Se retornou mais, pega apenas o solicitado
            variacoes = variacoes[:num_variacoes]
        
        return variacoes
    
    except Exception as e:
        _debug(f"Erro ao gerar variações com IA: {e}")
        raise

# ─────────────────────────────────────────────
# CONFIG JSON
# ─────────────────────────────────────────────
def carregar_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"tempo_min": 20, "tempo_max": 35, "api_key_gemini": ""}

def salvar_config(tempo_min: int, tempo_max: int, api_key_gemini: str = ""):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "tempo_min": tempo_min, 
            "tempo_max": tempo_max,
            "api_key_gemini": api_key_gemini
        }, f, indent=2)

# ─────────────────────────────────────────────
# SELENIUM
# ─────────────────────────────────────────────
def iniciar_driver():
    _debug("iniciar_driver: iniciando ChromeOptions")
    options = ChromeOptions()
    options.add_argument(f"--user-data-dir={CHROME_PROFILE}")

    # Anti-throttling
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Anti-detecção: mascara o navigator.webdriver que o WhatsApp usa para bloquear automação
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # User-agent de um Chrome normal (sem "HeadlessChrome" ou flags de bot)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    _debug(f"iniciar_driver: perfil em {CHROME_PROFILE}")
    driver = webdriver.Chrome(options=options)

    # Remove o navigator.webdriver via CDP (executa antes de qualquer página carregar)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

    driver.set_window_size(800, 600)
    _debug("iniciar_driver: Chrome aberto com sucesso")
    return driver

def enviar_mensagem(driver, numero: str, mensagem: str, modo_fragmentado: bool = True) -> bool:
    """
    Envia mensagem com digitação humanizada e erros ocasionais.
    
    Args:
        driver: WebDriver do Selenium
        numero: Número do destinatário
        mensagem: Texto completo da mensagem
        modo_fragmentado: Se True, divide mensagem em fragmentos enviados separadamente
    """
    driver.get(f"https://web.whatsapp.com/send?phone={numero}&text=")
    try:
        wait = WebDriverWait(driver, 40)
        caixa = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')
            )
        )
        time.sleep(1.5)
        caixa.click()
        
        # Simulação de leitura de mensagens antigas (comportamento natural)
        _simular_leitura_historico(driver)
        
        # Modo Conversa Natural: fragmenta mensagem em partes
        if modo_fragmentado:
            fragmentos = _fragmentar_mensagem_ia(mensagem)
            
            for idx, fragmento in enumerate(fragmentos):
                # Digita o fragmento com erros ocasionais e pausas intermitentes
                _digitar_com_erros(caixa, fragmento)
                
                # Envia o fragmento
                time.sleep(random.uniform(0.5, 1.0))
                caixa.send_keys(Keys.ENTER)
                
                # Pausa entre fragmentos (exceto no último)
                if idx < len(fragmentos) - 1:
                    pausa = random.uniform(3, 8)
                    time.sleep(pausa)
        else:
            # Modo tradicional: envia tudo de uma vez
            linhas = mensagem.split("\n")
            for i, linha in enumerate(linhas):
                _digitar_com_erros(caixa, linha)
                
                if i < len(linhas) - 1:
                    caixa.send_keys(Keys.SHIFT + Keys.ENTER)
                    time.sleep(random.uniform(0.1, 0.2))
            
            time.sleep(0.8)
            caixa.send_keys(Keys.ENTER)
        
        time.sleep(1.5)
        return True
    except Exception as e:
        return False


def _simular_leitura_historico(driver):
    """
    Simula usuário lendo mensagens antigas antes de enviar.
    Comportamento natural que reduz suspeita de automação.
    """
    try:
        # 40% de chance de simular leitura (não sempre, para parecer natural)
        if random.random() < 0.4:
            # Localiza área de mensagens
            try:
                chat_area = driver.find_element(By.XPATH, '//div[@data-tab="6"]')
                
                # Rola para cima (simula leitura de mensagens antigas)
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollTop - 300", chat_area)
                time.sleep(random.uniform(0.5, 1.5))
                
                # Rola de volta para baixo
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", chat_area)
                time.sleep(random.uniform(0.3, 0.8))
            except Exception:
                # Se não encontrar área de chat, ignora silenciosamente
                pass
    except Exception:
        # Ignora erros silenciosamente (não crítico)
        pass


def _fragmentar_mensagem_ia(mensagem: str) -> list:
    """
    Fragmenta mensagem em partes naturais para simular conversa.
    Usa pontuação e quebras de linha como guia.
    """
    fragmentos = []
    
    # Remove quebras de linha múltiplas e normaliza
    mensagem_limpa = " ".join(mensagem.split())
    
    # Divide por pontos, vírgulas e quebras naturais
    # Prioriza: ponto final > ponto de interrogação > vírgula
    partes = []
    buffer = ""
    
    for char in mensagem_limpa:
        buffer += char
        # Fragmenta em pontos finais, interrogações ou exclamações
        if char in '.!?' and len(buffer.strip()) > 15:
            partes.append(buffer.strip())
            buffer = ""
    
    # Adiciona resto se houver
    if buffer.strip():
        partes.append(buffer.strip())
    
    # Se ficou muito fragmentado (mais de 4 partes), agrupa
    if len(partes) > 4:
        fragmentos = []
        temp = ""
        for parte in partes:
            temp += " " + parte if temp else parte
            # Agrupa até ~80 caracteres ou 2 sentenças
            if len(temp) > 80 or temp.count('.') >= 2:
                fragmentos.append(temp.strip())
                temp = ""
        if temp:
            fragmentos.append(temp.strip())
    else:
        fragmentos = partes
    
    # Garante pelo menos 1 fragmento
    if not fragmentos:
        fragmentos = [mensagem]
    
    # Limita a 4 fragmentos no máximo (muito fragmentado fica artificial)
    if len(fragmentos) > 4:
        fragmentos = fragmentos[:4]
    
    return fragmentos


def _digitar_com_erros(caixa, texto: str):
    """
    Digita texto com erros ocasionais, correções e micro-pausas naturais.
    Simula digitação humana com interrupções e pensamentos.
    """
    palavras = texto.split(" ")
    contador_palavras = 0
    
    for idx_palavra, palavra in enumerate(palavras):
        # Micro-pausa aleatória a cada 8-12 palavras (simula pessoa pensando)
        if contador_palavras > 0 and contador_palavras % random.randint(8, 12) == 0:
            pausa_pensamento = random.uniform(0.5, 2.0)
            time.sleep(pausa_pensamento)
        
        # 15% de chance de cometer um erro de digitação em palavras com 5+ letras
        if len(palavra) >= 5 and random.random() < 0.15:
            # Simula erro: digita palavra errada
            pos_erro = random.randint(1, len(palavra) - 1)
            palavra_errada = palavra[:pos_erro] + random.choice('aeioutnsr') + palavra[pos_erro:]
            
            # Digita a palavra errada
            for char in palavra_errada:
                caixa.send_keys(char)
                time.sleep(random.uniform(0.01, 0.05))
            
            # Pausa de "percepção do erro" (humano percebe que errou)
            time.sleep(random.uniform(0.3, 0.7))
            
            # Apaga a palavra errada (backspace)
            for _ in range(len(palavra_errada)):
                caixa.send_keys(Keys.BACK_SPACE)
                time.sleep(random.uniform(0.02, 0.06))
            
            # Pausa antes de digitar corretamente
            time.sleep(random.uniform(0.1, 0.3))
            
            # Digita a palavra correta
            for char in palavra:
                caixa.send_keys(char)
                time.sleep(random.uniform(0.01, 0.05))
        else:
            # Digita normalmente sem erro, mas com pausas intermitentes
            for idx_char, char in enumerate(palavra):
                caixa.send_keys(char)
                
                # Pausa intermitente durante digitação (simula hesitação)
                if idx_char > 0 and idx_char % random.randint(3, 6) == 0 and random.random() < 0.3:
                    time.sleep(random.uniform(0.2, 0.6))
                else:
                    time.sleep(random.uniform(0.01, 0.05))
        
        contador_palavras += 1
        
        # Adiciona espaço entre palavras (exceto na última palavra)
        if idx_palavra < len(palavras) - 1:
            caixa.send_keys(" ")
            time.sleep(random.uniform(0.05, 0.1))

# ─────────────────────────────────────────────
# APLICAÇÃO PRINCIPAL
# ─────────────────────────────────────────────
class DisparadorApp(tk.Tk):

    SAUDACOES_PADRAO = (
        "*Douglas RH Jovem Renapsi*, Olá jovem, bom dia.\n"
        "*Douglas RH Jovem Renapsi*, Olá jovem, como você está?\n"
        "*Douglas RH Jovem Renapsi*, Olá jovem, espero que esteja bem."
    )

    MENSAGEM_PADRAO = (
        "Gostaria que você me enviasse a sua operadora e o número do seu bilhete de transporte "
        "(vinculado ao seu CPF). Além disso, peço que assine sua roteirização para a implantação "
        "da rota de trabalho/curso."
    )

    def __init__(self):
        super().__init__()
        self.title("Disparador RH — Painel de Controle")
        self.geometry("860x640")
        self.resizable(True, True)
        self.configure(bg="#1e1e2e")

        self._config = carregar_config()
        self._parar_event = threading.Event()  # setado para sinalizar parada
        self.lista_mensagens_spin = []  # Lista de variações geradas pela IA

        self._build_ui()

    # ── UI ────────────────────────────────────
    def _build_ui(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook",            background="#1e1e2e", borderwidth=0)
        style.configure("TNotebook.Tab",        background="#313244", foreground="#cdd6f4",
                        padding=[14, 6], font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab",
                  background=[("selected", "#89b4fa")],
                  foreground=[("selected", "#1e1e2e")])
        style.configure("TFrame",               background="#1e1e2e")
        style.configure("Green.TButton",        background="#a6e3a1", foreground="#1e1e2e",
                        font=("Segoe UI", 11, "bold"), padding=10)
        style.map("Green.TButton",
                  background=[("disabled", "#45475a"), ("active", "#94e2d5")])

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=10)

        # ── Aba 1 ──
        aba1 = ttk.Frame(nb)
        nb.add(aba1, text="  ⚙️  Configuração e Disparo  ")
        self._build_aba1(aba1)

        # ── Aba 2 ──
        aba2 = ttk.Frame(nb)
        nb.add(aba2, text="  📋  Logs do Sistema  ")
        self._build_aba2(aba2)

        # ── Aba 3 ──
        aba3 = ttk.Frame(nb)
        nb.add(aba3, text="  🔧  Configurações  ")
        self._build_aba3(aba3)

    def _label(self, parent, texto):
        tk.Label(
            parent, text=texto,
            bg="#1e1e2e", fg="#89b4fa",
            font=("Segoe UI", 9, "bold"), anchor="w"
        ).pack(fill="x", padx=6, pady=(8, 2))

    def _text_box(self, parent, height=5):
        txt = scrolledtext.ScrolledText(
            parent, height=height,
            bg="#313244", fg="#cdd6f4",
            insertbackground="#cdd6f4",
            font=("Consolas", 10),
            relief="flat", bd=0,
            wrap="word"
        )
        txt.pack(fill="both", expand=True, padx=6, pady=2)
        return txt

    def _build_aba1(self, parent):
        # Painel esquerdo (inputs) + direito (pausas + botão)
        main = tk.Frame(parent, bg="#1e1e2e")
        main.pack(fill="both", expand=True)

        # ── Painel esquerdo com scrollbar ──
        left_container = tk.Frame(main, bg="#1e1e2e")
        left_container.pack(side="left", fill="both", expand=True)

        # Canvas para scroll
        canvas = tk.Canvas(left_container, bg="#1e1e2e", highlightthickness=0)
        scrollbar = ttk.Scrollbar(left_container, orient="vertical", command=canvas.yview)
        
        # Frame interno que conterá todos os widgets
        left = tk.Frame(canvas, bg="#1e1e2e")
        
        # Configura o canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Empacota scrollbar e canvas
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Cria janela no canvas
        canvas_window = canvas.create_window((0, 0), window=left, anchor="nw")
        
        # Função para atualizar a região de scroll
        def _on_frame_configure(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Ajusta largura do frame interno ao canvas
            canvas_width = canvas.winfo_width()
            canvas.itemconfig(canvas_window, width=canvas_width)
        
        left.bind("<Configure>", _on_frame_configure)
        canvas.bind("<Configure>", _on_frame_configure)
        
        # Bind da rodinha do mouse para scroll
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        # Aplica o bind recursivamente em todos os widgets
        def _bind_mousewheel(widget):
            widget.bind("<MouseWheel>", _on_mousewheel)
            for child in widget.winfo_children():
                _bind_mousewheel(child)
        
        _bind_mousewheel(left)
        canvas.bind("<MouseWheel>", _on_mousewheel)

        right = tk.Frame(main, bg="#1e1e2e", width=220)
        right.pack(side="right", fill="y", padx=(0, 6))
        right.pack_propagate(False)

        # ── Contatos ──
        self._label(left, "📱 Contatos (um número por linha, sem +55):")
        self.txt_contatos = self._text_box(left, height=8)

        # ── Saudações ──
        self._label(left, "👋 Saudações (uma por linha — sorteio aleatório):")
        self.txt_saudacoes = self._text_box(left, height=5)
        self.txt_saudacoes.insert("1.0", self.SAUDACOES_PADRAO)

        # ── Corpo das Mensagens com sistema de múltiplas variações ──
        frame_mensagens_header = tk.Frame(left, bg="#1e1e2e")
        frame_mensagens_header.pack(fill="x", padx=6, pady=(8, 2))
        
        tk.Label(
            frame_mensagens_header, 
            text="✉️  Mensagens (use o botão + para adicionar variações — sorteio aleatório):",
            bg="#1e1e2e", fg="#89b4fa",
            font=("Segoe UI", 9, "bold"), 
            anchor="w"
        ).pack(side="left", fill="x", expand=True)
        
        btn_add_msg = tk.Button(
            frame_mensagens_header,
            text="➕ Adicionar Variação",
            bg="#a6e3a1", fg="#1e1e2e",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            command=self._adicionar_campo_mensagem
        )
        btn_add_msg.pack(side="right", padx=4)
        
        # Container scrollável para múltiplas mensagens
        self.frame_mensagens_container = tk.Frame(left, bg="#1e1e2e")
        self.frame_mensagens_container.pack(fill="both", expand=True, padx=6, pady=2)
        
        # Lista para armazenar os widgets de mensagem
        self.campos_mensagens = []
        
        # Adiciona o primeiro campo de mensagem
        self._adicionar_campo_mensagem(texto_inicial=self.MENSAGEM_PADRAO)

        # ── Botão de Geração de Variações com IA ──
        frame_ia = tk.Frame(left, bg="#1e1e2e")
        frame_ia.pack(fill="x", padx=6, pady=8)
        
        self.btn_gerar_ia = tk.Button(
            frame_ia,
            text="✨ Gerar Variações com IA",
            bg="#cba6f7", fg="#1e1e2e",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            command=self._gerar_variacoes_ia
        )
        self.btn_gerar_ia.pack(side="left", padx=4)
        
        self.lbl_status_ia = tk.Label(
            frame_ia,
            text="",
            bg="#1e1e2e", fg="#a6e3a1",
            font=("Segoe UI", 9, "bold")
        )
        self.lbl_status_ia.pack(side="left", padx=8)

        # ── Painel direito ──
        tk.Label(right, text="⏱  Pausas entre envios",
                 bg="#1e1e2e", fg="#89b4fa",
                 font=("Segoe UI", 10, "bold")).pack(pady=(18, 10))

        def _spin(label_txt, default):
            frm = tk.Frame(right, bg="#1e1e2e")
            frm.pack(fill="x", padx=10, pady=4)
            tk.Label(frm, text=label_txt, bg="#1e1e2e", fg="#cdd6f4",
                     font=("Segoe UI", 9)).pack(anchor="w")
            var = tk.StringVar(value=str(default))
            tk.Spinbox(frm, from_=1, to=3600, textvariable=var, width=8,
                       bg="#313244", fg="#cdd6f4", buttonbackground="#45475a",
                       font=("Consolas", 11), relief="flat").pack(anchor="w", pady=2)
            return var

        self.var_min = _spin("Mínimo (s):", self._config["tempo_min"])
        self.var_max = _spin("Máximo (s):", self._config["tempo_max"])

        # Separador
        tk.Frame(right, bg="#45475a", height=1).pack(fill="x", padx=10, pady=16)

        # Progresso
        tk.Label(right, text="Progresso", bg="#1e1e2e", fg="#a6adc8",
                 font=("Segoe UI", 9)).pack()
        self.lbl_progresso = tk.Label(right, text="—", bg="#1e1e2e", fg="#cdd6f4",
                                      font=("Segoe UI", 11, "bold"))
        self.lbl_progresso.pack(pady=4)

        self.progressbar = ttk.Progressbar(right, orient="horizontal",
                                           mode="determinate", length=180)
        self.progressbar.pack(padx=10, pady=4)

        # Botão
        self.btn_iniciar = ttk.Button(
            right, text="🚀  INICIAR DISPARO",
            style="Green.TButton",
            command=self._on_iniciar
        )
        self.btn_iniciar.pack(fill="x", padx=10, pady=(20, 6))

        self.btn_parar = ttk.Button(
            right, text="⛔  PARAR",
            command=self._on_parar,
            state="disabled"
        )
        self.btn_parar.pack(fill="x", padx=10)

    def _build_aba2(self, parent):
        tk.Label(parent, text="Logs em tempo real",
                 bg="#1e1e2e", fg="#89b4fa",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=10, pady=(8, 2))

        self.txt_log = scrolledtext.ScrolledText(
            parent, state="disabled",
            bg="#11111b", fg="#cdd6f4",
            font=("Consolas", 10),
            relief="flat", bd=0
        )
        self.txt_log.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Tags de cor
        self.txt_log.tag_config("ok",      foreground="#a6e3a1")
        self.txt_log.tag_config("erro",    foreground="#f38ba8")
        self.txt_log.tag_config("aviso",   foreground="#f9e2af")
        self.txt_log.tag_config("info",    foreground="#89dceb")
        self.txt_log.tag_config("destaque",foreground="#cba6f7", font=("Consolas", 10, "bold"))

        btn_limpar = tk.Button(
            parent, text="🗑  Limpar Logs",
            bg="#45475a", fg="#cdd6f4",
            font=("Segoe UI", 9), relief="flat",
            command=self._limpar_log
        )
        btn_limpar.pack(anchor="e", padx=10, pady=(0, 8))

    def _build_aba3(self, parent):
        """Aba de Configurações - API Key do Gemini"""
        container = tk.Frame(parent, bg="#1e1e2e")
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        tk.Label(
            container,
            text="🔑  Configuração da API do Gemini",
            bg="#1e1e2e", fg="#89b4fa",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", pady=(0, 10))
        
        # Descrição
        tk.Label(
            container,
            text="Cole aqui sua chave da API do Google Gemini para habilitar a geração de variações de mensagens com IA.",
            bg="#1e1e2e", fg="#cdd6f4",
            font=("Segoe UI", 9),
            wraplength=600,
            justify="left"
        ).pack(anchor="w", pady=(0, 15))
        
        # Frame para o campo de API Key
        frame_api = tk.Frame(container, bg="#1e1e2e")
        frame_api.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            frame_api,
            text="Chave da API (Gemini):",
            bg="#1e1e2e", fg="#89b4fa",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", pady=(0, 5))
        
        self.entry_api_key = tk.Entry(
            frame_api,
            bg="#313244", fg="#cdd6f4",
            insertbackground="#cdd6f4",
            font=("Consolas", 10),
            relief="flat",
            bd=0,
            show="*"  # Oculta a chave como senha
        )
        self.entry_api_key.pack(fill="x", ipady=8, pady=(0, 5))
        
        # Carrega a chave salva
        api_key_salva = self._config.get("api_key_gemini", "")
        if api_key_salva:
            self.entry_api_key.insert(0, api_key_salva)
        
        # Checkbox para mostrar/ocultar chave
        self.var_mostrar_chave = tk.BooleanVar(value=False)
        tk.Checkbutton(
            frame_api,
            text="Mostrar chave",
            variable=self.var_mostrar_chave,
            command=self._toggle_mostrar_chave,
            bg="#1e1e2e", fg="#cdd6f4",
            selectcolor="#313244",
            activebackground="#1e1e2e",
            activeforeground="#cdd6f4",
            font=("Segoe UI", 9)
        ).pack(anchor="w", pady=(0, 10))
        
        # Botão Salvar
        btn_salvar_api = tk.Button(
            frame_api,
            text="💾  Salvar Configuração",
            bg="#a6e3a1", fg="#1e1e2e",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            command=self._salvar_api_key
        )
        btn_salvar_api.pack(anchor="w", pady=(5, 0))
        
        # Status da configuração
        self.lbl_status_config = tk.Label(
            container,
            text="",
            bg="#1e1e2e", fg="#a6e3a1",
            font=("Segoe UI", 9, "bold")
        )
        self.lbl_status_config.pack(anchor="w", pady=(10, 0))
        
        # Separador
        tk.Frame(container, bg="#45475a", height=1).pack(fill="x", pady=20)
        
        # Instruções
        tk.Label(
            container,
            text="📖  Como obter sua chave da API:",
            bg="#1e1e2e", fg="#89b4fa",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", pady=(0, 10))
        
        instrucoes = [
            "1. Acesse: https://aistudio.google.com/apikey",
            "2. Faça login com sua conta Google",
            "3. Clique em 'Create API Key'",
            "4. Copie a chave gerada",
            "5. Cole aqui e clique em 'Salvar Configuração'"
        ]
        
        for instrucao in instrucoes:
            tk.Label(
                container,
                text=instrucao,
                bg="#1e1e2e", fg="#cdd6f4",
                font=("Segoe UI", 9),
                justify="left"
            ).pack(anchor="w", pady=2)
    
    def _toggle_mostrar_chave(self):
        """Alterna entre mostrar/ocultar a chave da API"""
        if self.var_mostrar_chave.get():
            self.entry_api_key.config(show="")
        else:
            self.entry_api_key.config(show="*")
    
    def _salvar_api_key(self):
        """Salva a chave da API no config.json"""
        api_key = self.entry_api_key.get().strip()
        
        if not api_key:
            messagebox.showwarning(
                "Aviso",
                "Por favor, insira uma chave da API válida."
            )
            return
        
        try:
            # Salva no config
            t_min = int(self.var_min.get())
            t_max = int(self.var_max.get())
            salvar_config(t_min, t_max, api_key)
            
            # Atualiza config em memória
            self._config["api_key_gemini"] = api_key
            
            # Feedback visual
            self.lbl_status_config.config(
                text="✅ Chave da API salva com sucesso!",
                fg="#a6e3a1"
            )
            self.log("[CONFIG] ✅ Chave da API do Gemini configurada com sucesso!", "ok")
            
            messagebox.showinfo(
                "Sucesso",
                "Chave da API salva com sucesso!\n\n"
                "Agora você pode usar o botão '✨ Gerar Variações com IA' "
                "na aba de Configuração e Disparo."
            )
            
        except Exception as e:
            self.lbl_status_config.config(
                text="❌ Erro ao salvar",
                fg="#f38ba8"
            )
            messagebox.showerror(
                "Erro",
                f"Erro ao salvar a configuração:\n\n{e}"
            )

    # ── Log ───────────────────────────────────
    def log(self, mensagem: str, tag: str = "info"):
        """Thread-safe: insere linha no painel de logs."""
        def _insert():
            self.txt_log.configure(state="normal")
            self.txt_log.insert("end", mensagem + "\n", tag)
            self.txt_log.see("end")
            self.txt_log.configure(state="disabled")
        self.after(0, _insert)

    def _limpar_log(self):
        self.txt_log.configure(state="normal")
        self.txt_log.delete("1.0", "end")
        self.txt_log.configure(state="disabled")

    # ── Gerenciamento de Campos de Mensagem ──────────────────────────────────
    def _adicionar_campo_mensagem(self, texto_inicial=""):
        """Adiciona um novo campo de mensagem com botão de remover"""
        frame_msg = tk.Frame(self.frame_mensagens_container, bg="#1e1e2e", relief="solid", bd=1)
        frame_msg.pack(fill="both", expand=True, pady=4)
        
        # Header do campo com número e botão remover
        header = tk.Frame(frame_msg, bg="#313244")
        header.pack(fill="x")
        
        numero_msg = len(self.campos_mensagens) + 1
        tk.Label(
            header,
            text=f"📝 Mensagem #{numero_msg}",
            bg="#313244", fg="#89b4fa",
            font=("Segoe UI", 9, "bold"),
            anchor="w"
        ).pack(side="left", padx=8, pady=4)
        
        # Botão remover (só aparece se tiver mais de 1 mensagem)
        btn_remover = tk.Button(
            header,
            text="🗑️ Remover",
            bg="#f38ba8", fg="#1e1e2e",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            cursor="hand2",
            command=lambda f=frame_msg: self._remover_campo_mensagem(f)
        )
        if len(self.campos_mensagens) > 0:  # Só mostra se não for o primeiro
            btn_remover.pack(side="right", padx=8, pady=4)
        
        # Campo de texto para a mensagem
        txt = scrolledtext.ScrolledText(
            frame_msg,
            height=4,
            bg="#313244", fg="#cdd6f4",
            insertbackground="#cdd6f4",
            font=("Consolas", 10),
            relief="flat", bd=0,
            wrap="word"
        )
        txt.pack(fill="both", expand=True, padx=4, pady=4)
        
        if texto_inicial:
            txt.insert("1.0", texto_inicial)
        
        # Armazena referência
        self.campos_mensagens.append({
            "frame": frame_msg,
            "text_widget": txt,
            "btn_remover": btn_remover
        })
        
        # Atualiza numeração de todos os campos
        self._atualizar_numeracao_mensagens()
    
    def _remover_campo_mensagem(self, frame):
        """Remove um campo de mensagem"""
        # Não permite remover se for o último
        if len(self.campos_mensagens) <= 1:
            messagebox.showwarning(
                "Aviso",
                "Você precisa ter pelo menos uma mensagem cadastrada."
            )
            return
        
        # Remove da lista
        self.campos_mensagens = [
            campo for campo in self.campos_mensagens 
            if campo["frame"] != frame
        ]
        
        # Destroi o widget
        frame.destroy()
        
        # Atualiza numeração
        self._atualizar_numeracao_mensagens()
    
    def _atualizar_numeracao_mensagens(self):
        """Atualiza a numeração dos campos de mensagem"""
        for idx, campo in enumerate(self.campos_mensagens, 1):
            # Atualiza o label do header
            header = campo["frame"].winfo_children()[0]
            label = header.winfo_children()[0]
            label.config(text=f"📝 Mensagem #{idx}")
            
            # Mostra/esconde botão remover
            if len(self.campos_mensagens) > 1:
                campo["btn_remover"].pack(side="right", padx=8, pady=4)
            else:
                campo["btn_remover"].pack_forget()
    
    def _coletar_mensagens(self):
        """Coleta todas as mensagens dos campos"""
        mensagens = []
        for campo in self.campos_mensagens:
            texto = campo["text_widget"].get("1.0", tk.END).strip()
            if texto:
                mensagens.append(texto)
        return mensagens

    # ── Geração de Variações com IA ──────────────────────────────────
    def _gerar_variacoes_ia(self):
        """Gera variações usando Gemini AI em thread separada"""
        # Pega o texto do primeiro campo de mensagem
        if not self.campos_mensagens:
            messagebox.showerror("Erro", "Adicione uma mensagem base primeiro.")
            return
        
        texto_base = self.campos_mensagens[0]["text_widget"].get("1.0", tk.END).strip()
        if not texto_base:
            messagebox.showerror("Erro", "A primeira mensagem está vazia.")
            return
        
        # Verifica se a API key está configurada
        api_key = self._config.get("api_key_gemini", "")
        if not api_key:
            api_key = os.getenv("GEMINI_API_KEY", "")
        
        if not api_key:
            messagebox.showerror(
                "API Key não configurada",
                "Por favor, configure sua chave da API do Gemini na aba 'Configurações' antes de gerar variações."
            )
            return
        
        # Desabilita botão durante processamento
        self.btn_gerar_ia.config(state="disabled", text="⏳ Gerando...")
        self.lbl_status_ia.config(text="Aguarde...", fg="#f9e2af")
        
        def _worker():
            try:
                variacoes = gerar_variacoes_ia(texto_base, num_variacoes=7, api_key=api_key)
                self.lista_mensagens_spin = variacoes
                
                # Atualiza UI na thread principal
                self.after(0, lambda: self._aplicar_variacoes_ia(variacoes))
                
            except Exception as e:
                erro_msg = str(e)
                self.after(0, lambda: self._erro_geracao_ia(erro_msg))
        
        threading.Thread(target=_worker, daemon=True).start()
    
    def _aplicar_variacoes_ia(self, variacoes):
        """Aplica as variações geradas aos campos de mensagem"""
        # Remove todos os campos exceto o primeiro
        while len(self.campos_mensagens) > 1:
            ultimo = self.campos_mensagens[-1]
            ultimo["frame"].destroy()
            self.campos_mensagens.pop()
        
        # Adiciona as variações como novos campos
        for i, variacao in enumerate(variacoes):
            if i == 0:
                # Atualiza o primeiro campo
                self.campos_mensagens[0]["text_widget"].delete("1.0", tk.END)
                self.campos_mensagens[0]["text_widget"].insert("1.0", variacao)
            else:
                # Adiciona novos campos
                self._adicionar_campo_mensagem(texto_inicial=variacao)
        
        # Atualiza status
        self.btn_gerar_ia.config(state="normal", text="✨ Gerar Variações com IA")
        self.lbl_status_ia.config(
            text=f"✅ {len(variacoes)} variações geradas com IA prontas para uso",
            fg="#a6e3a1"
        )
        self.log(f"[IA] ✨ {len(variacoes)} variações geradas com sucesso!", "ok")
    
    def _erro_geracao_ia(self, erro_msg):
        """Trata erros na geração de variações"""
        self.btn_gerar_ia.config(state="normal", text="✨ Gerar Variações com IA")
        self.lbl_status_ia.config(text="❌ Erro ao gerar", fg="#f38ba8")
        self.log(f"[IA] ❌ Erro: {erro_msg}", "erro")
        messagebox.showerror(
            "Erro na Geração de Variações",
            f"Não foi possível gerar variações com a IA:\n\n{erro_msg}\n\n"
            "Verifique se a chave da API está configurada corretamente no arquivo .env"
        )

    # ── Progresso ─────────────────────────────
    def _atualizar_progresso(self, atual: int, total: int):
        def _upd():
            pct = int(atual / total * 100) if total else 0
            self.progressbar["value"] = pct
            self.lbl_progresso.config(text=f"{atual} / {total}  ({pct}%)")
        self.after(0, _upd)

    # ── Botões ────────────────────────────────
    def _on_iniciar(self):
        _debug("_on_iniciar: botão clicado")
        # Valida pausas
        try:
            t_min = int(self.var_min.get())
            t_max = int(self.var_max.get())
        except ValueError:
            messagebox.showerror("Erro", "Os tempos de pausa devem ser números inteiros.")
            return
        if t_min <= 0 or t_max <= 0:
            messagebox.showerror("Erro", "Os tempos devem ser maiores que zero.")
            return
        if t_min > t_max:
            messagebox.showerror("Erro", "O tempo mínimo não pode ser maior que o máximo.")
            return

        # Coleta dados das áreas de texto
        contatos  = [l.strip() for l in self.txt_contatos.get("1.0", tk.END).splitlines() if l.strip()]
        saudacoes = [l.strip() for l in self.txt_saudacoes.get("1.0", tk.END).splitlines() if l.strip()]
        mensagens = self._coletar_mensagens()  # NOVO: usa o método de coleta

        if not contatos:
            messagebox.showerror("Erro", "Adicione ao menos um contato.")
            return
        if not saudacoes:
            messagebox.showerror("Erro", "Adicione ao menos uma saudação.")
            return
        if not mensagens:
            messagebox.showerror("Erro", "Adicione ao menos uma mensagem.")
            return

        salvar_config(t_min, t_max, self._config.get("api_key_gemini", ""))

        self._parar_event.clear()
        self.btn_iniciar.config(state="disabled")
        self.btn_parar.config(state="normal")
        self.progressbar["value"] = 0

        t = threading.Thread(
            target=self._worker_disparo,
            args=(contatos, saudacoes, mensagens, t_min, t_max),
            daemon=True
        )
        t.start()

    def _on_parar(self):
        self._parar_event.set()
        self.log("⛔  Sinal de parada enviado — aguardando envio atual terminar...", "aviso")

    # ── Worker (Thread) ───────────────────────
    def _worker_disparo(self, contatos, saudacoes, mensagens, t_min, t_max):
        total    = len(contatos)
        contador = 0
        contador_sucesso = 0  # Contador de envios bem-sucedidos para pausas humanizadas
        erros    = 0
        parar    = self._parar_event  # atalho local

        _debug(f"_worker_disparo: iniciado | {total} contatos | pausa {t_min}-{t_max}s")
        self.log(f"{'─'*55}", "destaque")
        self.log(f"🚀  Iniciando disparo: {total} contatos | pausa {t_min}s–{t_max}s", "destaque")
        self.log(f"{'─'*55}", "destaque")

        driver = None
        try:
            self.log("[INFO] Abrindo Chrome...", "info")
            _debug("_worker_disparo: chamando iniciar_driver()")
            driver = iniciar_driver()
            _debug("_worker_disparo: driver criado")

            if parar.is_set():
                self.log("⛔  Parado antes de abrir o WhatsApp.", "aviso")
                return

            self.log("[INFO] Aguardando WhatsApp Web (até 60s)...", "info")
            driver.get("https://web.whatsapp.com")

            # Polling manual: verifica parada a cada 1s durante o wait
            deadline  = time.time() + 60
            carregado = False
            while time.time() < deadline:
                if parar.is_set():
                    self.log("⛔  Parado durante carregamento do WhatsApp.", "aviso")
                    return
                try:
                    driver.find_element(By.XPATH, '//div[@data-tab="3"]')
                    carregado = True
                    break
                except Exception:
                    time.sleep(1)

            if carregado:
                self.log("[INFO] WhatsApp Web carregado.", "info")
                _debug("_worker_disparo: WhatsApp Web carregado")
            else:
                self.log("[AVISO] Timeout no WhatsApp Web. Verifique o QR Code.", "aviso")
                _debug("_worker_disparo: timeout aguardando WhatsApp Web")

            for numero_raw in contatos:
                if parar.is_set():
                    break

                numero = numero_raw.strip()
                if not numero:
                    continue
                if not numero.startswith("+"):
                    numero = f"+55{numero}"

                contador += 1
                
            
                mensagem_corpo = random.choice(mensagens)
                
                # Extrai nome do número (simplificado - pode ser melhorado)
                nome = numero.split("+55")[-1][:2]  # Placeholder - ajuste conforme necessário
                mensagem_corpo = mensagem_corpo.replace("[NOME]", nome)
                
                # Monta mensagem final com saudação
                msg = f"{random.choice(saudacoes)} {mensagem_corpo}"
                ts  = time.strftime("%Y-%m-%d %H:%M:%S")

                self.log(f"[{contador}/{total}]  ➜  {numero}", "info")
                _debug(f"enviando para {numero}")

                # Sorteio aleatório: 50% fragmentado, 50% mensagem inteira
                usar_fragmentacao = random.choice([True, False])
                
                if usar_fragmentacao:
                    self.log(f"   💬 Modo: Conversa fragmentada", "info")
                else:
                    self.log(f"   📝 Modo: Mensagem única", "info")
                
                # Envia com modo sorteado
                sucesso = enviar_mensagem(driver, numero, msg, modo_fragmentado=usar_fragmentacao)
                
                # Sistema de Aquecimento Inteligente (otimizado para alto volume)
                if contador_sucesso <= 3:
                    # Aquecimento inicial ultra-rápido (primeiros 3 envios)
                    pausa_seg = random.uniform(90, 150)  # 1.5-2.5 min
                    self.log(f"   🔥 Aquecimento: pausa de {pausa_seg:.0f}s", "aviso")
                elif contador_sucesso <= 10:
                    # Transição rápida (envios 4-10)
                    pausa_seg = random.uniform(45, 75)  # 45s-1.25min
                    self.log(f"   ⚡ Acelerando: pausa de {pausa_seg:.0f}s", "aviso")
                else:
                    # Velocidade cruzeiro (envios 11+)
                    pausa_seg = random.uniform(t_min, t_max)  # Padrão configurado

                if sucesso:
                    contador_sucesso += 1
                    self.log(f"   ✅  Enviado  |  próxima pausa: {pausa_seg:.1f}s", "ok")
                    _debug(f"OK: {numero}")
                    with open(HISTORICO_FILE, "a", encoding="utf-8") as f:
                        f.write(f"{ts} - OK - {numero}\n")
                else:
                    erros += 1
                    self.log(f"   ❌  Falha    |  próxima pausa: {pausa_seg:.1f}s", "erro")
                    _debug(f"ERRO: {numero}")
                    with open(ERROS_FILE, "a", encoding="utf-8") as f:
                        f.write(f"{ts} - ERRO - {numero}\n")

                self._atualizar_progresso(contador, total)

                # Pausa interrompível: Event.wait retorna imediatamente se parar for setado
                parar.wait(timeout=pausa_seg)
                if parar.is_set():
                    break

                # Pausa humanizada de segurança a cada 15 envios bem-sucedidos
                if contador_sucesso > 0 and contador_sucesso % 15 == 0:
                    pausa_humanizada = random.randint(90, 180)  # Reduzido: 1.5-3 min
                    self.log(f"\n☕  Pausa humanizada de segurança ativada... ({pausa_humanizada//60} min)", "aviso")
                    parar.wait(timeout=pausa_humanizada)
                    if parar.is_set():
                        break

                # Pausa anti-ban a cada 40 envios (aumentado de 25 para 40)
                if contador % 40 == 0:
                    pausa_antiban = random.randint(300, 600)  # Reduzido: 5-10 min
                    self.log(f"\n☕  Pausa anti-ban de {pausa_antiban//60} min (a cada 40 envios)...", "aviso")
                    parar.wait(timeout=pausa_antiban)
                    if parar.is_set():
                        break

        except Exception as e:
            tb = traceback.format_exc()
            _debug(f"EXCEÇÃO CRÍTICA:\n{tb}")
            self.log(f"[ERRO CRÍTICO] {e}", "erro")
            self.log("[ERRO] Verifique o arquivo debug.log na pasta do programa para detalhes.", "erro")
            self.after(0, lambda err=str(e): messagebox.showerror(
                "Erro ao iniciar",
                f"Ocorreu um erro ao abrir o Chrome/WhatsApp:\n\n{err}\n\n"
                "Verifique se o Google Chrome está instalado.\n"
                "Detalhes técnicos salvos em debug.log na pasta do programa."
            ))
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
            enviados = contador - erros
            _debug(f"_worker_disparo: finalizado | {enviados}/{total} enviados | {erros} erros")
            self.log(f"{'─'*55}", "destaque")
            self.log(f"🎯  Concluído: {enviados}/{total} enviados | {erros} erro(s)", "destaque")
            self.log(f"{'─'*55}", "destaque")
            self.after(0, lambda: self.btn_iniciar.config(state="normal"))
            self.after(0, lambda: self.btn_parar.config(state="disabled"))


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = DisparadorApp()
    app.mainloop()
