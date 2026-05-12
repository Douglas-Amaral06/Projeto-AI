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

# ─────────────────────────────────────────────
# BASE_DIR
# ─────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

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
# CONFIG JSON
# ─────────────────────────────────────────────
def carregar_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"tempo_min": 20, "tempo_max": 35}

def salvar_config(tempo_min: int, tempo_max: int):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"tempo_min": tempo_min, "tempo_max": tempo_max}, f, indent=2)

# ─────────────────────────────────────────────
# SELENIUM
# ─────────────────────────────────────────────
def iniciar_driver() -> webdriver.Chrome:
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

def enviar_mensagem(driver: webdriver.Chrome, numero: str, mensagem: str) -> bool:
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
        linhas = mensagem.split("\n")
        for i, linha in enumerate(linhas):
            caixa.send_keys(linha)
            if i < len(linhas) - 1:
                caixa.send_keys(Keys.SHIFT + Keys.ENTER)
        time.sleep(0.8)
        caixa.send_keys(Keys.ENTER)
        time.sleep(1.5)
        return True
    except Exception as e:
        return False

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

        left = tk.Frame(main, bg="#1e1e2e")
        left.pack(side="left", fill="both", expand=True)

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

        salvar_config(t_min, t_max)

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
                msg = f"{random.choice(saudacoes)} {random.choice(mensagens)}"
                ts  = time.strftime("%Y-%m-%d %H:%M:%S")

                self.log(f"[{contador}/{total}]  ➜  {numero}", "info")
                _debug(f"enviando para {numero}")

                sucesso = enviar_mensagem(driver, numero, msg)
                pausa_seg = random.uniform(t_min, t_max)

                if sucesso:
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

                # Pausa anti-ban a cada 25 envios
                if contador % 25 == 0:
                    self.log("\n☕  Pausa anti-ban de 15 min (a cada 25 envios)...", "aviso")
                    parar.wait(timeout=900)
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
