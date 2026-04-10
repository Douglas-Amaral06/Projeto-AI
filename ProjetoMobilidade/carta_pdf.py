"""
Geração da Carta de Opção de Transporte e Mobilidade em PDF.
Usa fpdf2 (pip install fpdf2) — compatível com Python 3.14+.
"""
import io
import datetime
from fpdf import FPDF

# ── Dados fixos da empresa ────────────────────────────────────────────────────
EMPRESA = {
    "cnpj":       "37.381.902/0004-78",
    "nome":       "RENAPSI - SÃO PAULO - C-T",
    "endereco":   "Rua Cincinato Braga, 388 - Bela Vista - São Paulo - SP - 01333-010",
    "local_trab": "Renapsi - CINCINATO - SP",
    "cod_app":    "45287",
    "cod_end":    "437022",
}

CODIGOS_BILHETE = {
    "Crédito Eletrônico VT (Ônibus)":       "210",
    "Crédito Eletrônico VT (Metrô)":        "211",
    "Integração Ônibus+Metrô VT":           "214",
    "Integração VT":                        "214",
    "Crédito Eletrônico VT Ônibus":         "210",
    "Crédito Eletrônico VT Metrô/CPTM":    "211",
    "Integração VT (Ônibus + Metrô/CPTM)": "214",
    "Nenhum":                               "000",
}

OPERADORAS = {
    "Crédito Eletrônico VT (Ônibus)":       "SPTRANS",
    "Crédito Eletrônico VT (Metrô)":        "METRO SP",
    "Integração Ônibus+Metrô VT":           "SPTRANS",
    "Integração VT":                        "SPTRANS",
    "Crédito Eletrônico VT Ônibus":         "SPTRANS",
    "Crédito Eletrônico VT Metrô/CPTM":    "METRO SP",
    "Integração VT (Ônibus + Metrô/CPTM)": "SPTRANS",
    "Nenhum":                               "-",
}

# Cores (R, G, B)
AZUL       = (26, 58, 92)
AZUL_CLARO = (214, 228, 240)
CINZA      = (242, 242, 242)
CINZA_ESC  = (100, 100, 100)
PRETO      = (0, 0, 0)
BRANCO     = (255, 255, 255)


class CartaPDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_margins(15, 12, 15)
        self.set_auto_page_break(auto=True, margin=15)
        self.add_page()

    # ── helpers ──────────────────────────────────────────────────────────────
    def _set_fill(self, rgb):
        self.set_fill_color(*rgb)

    def _set_text(self, rgb):
        self.set_text_color(*rgb)

    def _set_draw(self, rgb):
        self.set_draw_color(*rgb)

    def _label_lateral(self, texto: str, altura: float):
        """Faixa lateral colorida com texto rotacionado."""
        x0 = self.get_x()
        y0 = self.get_y()
        self._set_fill(AZUL)
        self.rect(x0, y0, 8, altura, style="F")
        self._set_text(BRANCO)
        self.set_font("Helvetica", "B", 6)
        # Escreve letra a letra verticalmente
        for i, ch in enumerate(texto):
            self.set_xy(x0 + 1.5, y0 + 2 + i * 3.5)
            self.cell(5, 3.5, ch, align="C")
        self._set_text(PRETO)
        self.set_xy(x0 + 8, y0)

    def _linha_kv(self, chave: str, valor: str, w_chave=40, w_valor=0, bold_val=False):
        """Par chave: valor em linha."""
        if w_valor == 0:
            w_valor = self.epw - w_chave
        self.set_font("Helvetica", "B", 7)
        self._set_text(CINZA_ESC)
        self.cell(w_chave, 5, chave, border=0)
        self.set_font("Helvetica", "B" if bold_val else "", 8)
        self._set_text(PRETO)
        self.cell(w_valor, 5, valor, border=0, ln=True)

    def _cabecalho_secao(self, cols: list, widths: list, altura=5):
        """Linha de cabeçalho de tabela."""
        self._set_fill(AZUL_CLARO)
        self.set_font("Helvetica", "B", 7)
        self._set_text(PRETO)
        for txt, w in zip(cols, widths):
            self.cell(w, altura, txt, border=1, fill=True)
        self.ln()

    def _linha_dados(self, cols: list, widths: list, altura=5, fill=False):
        self._set_fill(CINZA if fill else BRANCO)
        self.set_font("Helvetica", "", 8)
        self._set_text(PRETO)
        for txt, w in zip(cols, widths):
            self.cell(w, altura, str(txt), border=1, fill=fill)
        self.ln()

    def _hr(self, espessura=0.3, cor=CINZA_ESC):
        self._set_draw(cor)
        self.set_line_width(espessura)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.set_line_width(0.2)
        self._set_draw(PRETO)
        self.ln(2)

    def _bloco_secao(self, label: str, conteudo_fn, altura_label: float):
        """Renderiza label lateral + conteúdo."""
        x_ini = self.get_x()
        y_ini = self.get_y()
        self._label_lateral(label, altura_label)
        conteudo_fn()
        self.set_xy(x_ini, y_ini + altura_label + 2)


def gerar_carta_pdf(dados_jovem: dict, rota_selecionada: dict,
                    end_casa_completo: str, end_trab_completo: str) -> bytes:
    """
    Gera a Carta de Opção de Transporte e Mobilidade em PDF.
    Retorna bytes do PDF.
    """
    pdf = CartaPDF()
    lw = pdf.epw  # largura útil

    # ── Cabeçalho ─────────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 13)
    pdf._set_text(AZUL)
    pdf.cell(lw * 0.4, 8, "RENAPSI", ln=False)
    pdf.set_font("Helvetica", "B", 11)
    pdf._set_text(PRETO)
    pdf.cell(lw * 0.6, 8, "Carta de Opcao de Transporte e Mobilidade",
             align="R", ln=True)
    pdf._hr(1.5, AZUL)

    # ── EMPRESA ───────────────────────────────────────────────────────────────
    y_emp = pdf.get_y()
    pdf._label_lateral("EMPRESA", 28)

    pdf.set_font("Helvetica", "B", 7)
    pdf._set_text(CINZA_ESC)
    pdf.cell(35, 4, "CNPJ", border=0)
    pdf.cell(lw * 0.5, 4, "Empresa", border=0)
    pdf.cell(0, 4, "Cod. App", align="R", ln=True)

    pdf.set_font("Helvetica", "", 8)
    pdf._set_text(PRETO)
    pdf.cell(35, 4, EMPRESA["cnpj"], border=0)
    pdf.cell(lw * 0.5, 4, EMPRESA["nome"], border=0)
    pdf.cell(0, 4, EMPRESA["cod_app"], align="R", ln=True)

    pdf.set_font("Helvetica", "B", 7)
    pdf._set_text(CINZA_ESC)
    pdf.cell(0, 4, "Endereco", ln=True)
    pdf.set_font("Helvetica", "", 8)
    pdf._set_text(PRETO)
    pdf.cell(0, 4, EMPRESA["endereco"], ln=True)

    pdf.set_font("Helvetica", "B", 7)
    pdf._set_text(CINZA_ESC)
    pdf.cell(lw * 0.7, 4, "Local de Trabalho", border=0)
    pdf.cell(0, 4, "Cod. End.", align="R", ln=True)
    pdf.set_font("Helvetica", "", 8)
    pdf._set_text(PRETO)
    pdf.cell(lw * 0.7, 4, EMPRESA["local_trab"], border=0)
    pdf.cell(0, 4, EMPRESA["cod_end"], align="R", ln=True)

    pdf._hr()

    # ── USUÁRIO ───────────────────────────────────────────────────────────────
    cpf_raw = str(dados_jovem.get('cpf', '')).zfill(11)
    cpf_fmt = f"{cpf_raw[:3]}.{cpf_raw[3:6]}.{cpf_raw[6:9]}-{cpf_raw[9:]}" if len(cpf_raw) == 11 else cpf_raw
    cod_resultado = str(dados_jovem.get('id', '0')).zfill(7)

    pdf._label_lateral("USUARIO", 22)

    pdf.set_font("Helvetica", "B", 7)
    pdf._set_text(CINZA_ESC)
    pdf.cell(40, 4, "CPF", border=0)
    pdf.cell(35, 4, "Matricula", border=0)
    pdf.cell(lw * 0.4, 4, "Nome", border=0)
    pdf.cell(0, 4, "Cod. Resultado", align="R", ln=True)

    pdf.set_font("Helvetica", "", 8)
    pdf._set_text(PRETO)
    pdf.cell(40, 4, cpf_fmt, border=0)
    pdf.cell(35, 4, str(dados_jovem.get('matricula', '') or ''), border=0)
    pdf.cell(lw * 0.4, 4, dados_jovem.get('nome', '').upper(), border=0)
    pdf.cell(0, 4, cod_resultado, align="R", ln=True)

    pdf.set_font("Helvetica", "B", 7)
    pdf._set_text(CINZA_ESC)
    pdf.cell(0, 4, "Endereco", ln=True)
    pdf.set_font("Helvetica", "", 8)
    pdf._set_text(PRETO)
    pdf.cell(0, 4, end_casa_completo.upper()[:90], ln=True)

    pdf._hr()

    # ── Dados da rota ─────────────────────────────────────────────────────────
    bilhete   = rota_selecionada.get('bilhete', 'Integracao Onibus+Metro VT')
    trajeto   = rota_selecionada.get('trajeto', rota_selecionada.get('modal', ''))
    tempo     = rota_selecionada.get('tempo', '-')
    tarifa_un = rota_selecionada.get('valor_diario', 0) / 2
    cod_item  = CODIGOS_BILHETE.get(bilhete, "214")
    operadora = OPERADORAS.get(bilhete, "SPTRANS")
    valor_total = rota_selecionada.get('valor_diario', 0)

    # Nome limpo para exibição
    linha_nome = f"VT. {bilhete.upper().replace('CREDITO ELETRONICO ','').replace('(','').replace(')','')}"
    linha_nome = linha_nome.encode('ascii', 'replace').decode('ascii')

    w1, w2, w3, w4, w5 = lw*0.30, lw*0.12, lw*0.22, lw*0.22, lw*0.06

    # IDA
    pdf._label_lateral("IDA", 14)
    pdf._cabecalho_secao(
        ["IDA - Linha / Instrucao", "m - min.", "Origem - Embarque", "Destino - Desembarque", "Tarifa"],
        [w1, w2, w3, w4, w5]
    )
    pdf._linha_dados(
        [linha_nome, tempo, end_casa_completo[:28], end_trab_completo[:28], f"R${tarifa_un:.2f}"],
        [w1, w2, w3, w4, w5]
    )
    pdf.ln(2)

    # VOLTA
    pdf._label_lateral("VOLTA", 14)
    pdf._cabecalho_secao(
        ["VOLTA - Linha / Instrucao", "m - min.", "Origem - Embarque", "Destino - Desembarque", "Tarifa"],
        [w1, w2, w3, w4, w5]
    )
    pdf._linha_dados(
        [linha_nome, tempo, end_trab_completo[:28], end_casa_completo[:28], f"R${tarifa_un:.2f}"],
        [w1, w2, w3, w4, w5]
    )
    pdf.ln(2)

    # VT
    wv1, wv2, wv3, wv4, wv5, wv6 = lw*0.18, lw*0.06, lw*0.36, lw*0.10, lw*0.10, lw*0.12
    pdf._label_lateral("VT", 18)
    pdf._cabecalho_secao(
        ["Operadora", "Qtd", "Item Tipo", "Item Cod.", "Tarifa", "Valor VT"],
        [wv1, wv2, wv3, wv4, wv5, wv6]
    )
    pdf._linha_dados(
        [operadora, "2", linha_nome, cod_item, f"R${tarifa_un:.2f}", f"R${valor_total:.2f}"],
        [wv1, wv2, wv3, wv4, wv5, wv6]
    )
    # Linha Total
    pdf._set_fill(AZUL_CLARO)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(wv1 + wv2 + wv3 + wv4, 5, "", border=1, fill=True)
    pdf.cell(wv5, 5, "Total", border=1, fill=True, align="R")
    pdf.cell(wv6, 5, f"R${valor_total:.2f}", border=1, fill=True, align="R")
    pdf.ln(3)

    # ── ACEITE ────────────────────────────────────────────────────────────────
    pdf._label_lateral("ACEITE", 28)

    texto_legal = (
        "O beneficiario de VT se compromete a utiliza-lo para o deslocamento "
        "casa-trabalho-casa. Qualquer declaracao falsa, abuso, ou uso indevido "
        "do VT, constituira em falta grave, sujeitando as penalidades da Lei. "
        "Autorizo o desconto de ate 6% do salario base na folha de pagamento, "
        "conforme legislacao em vigor."
    )

    x_aceite = pdf.get_x()
    y_aceite = pdf.get_y()

    # Opções à esquerda
    pdf.set_font("Helvetica", "", 8)
    pdf._set_text(PRETO)
    for opcao in ["[X] Tenho interesse. Quero utilizar o transporte acima.",
                  "[ ] Nao tenho interesse.",
                  "[ ] Quero cancelar meu beneficio"]:
        pdf.cell(lw * 0.42, 6, opcao, ln=True)

    # Texto legal à direita
    pdf.set_xy(x_aceite + lw * 0.44, y_aceite)
    pdf.set_font("Helvetica", "", 7)
    pdf._set_text(CINZA_ESC)
    pdf.multi_cell(lw * 0.50, 4, texto_legal)

    pdf.ln(4)
    pdf._hr()

    # ── Rodapé: Data e Assinatura ─────────────────────────────────────────────
    data_hoje = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    pdf.set_font("Helvetica", "B", 8)
    pdf._set_text(CINZA_ESC)
    pdf.cell(lw * 0.5, 5, "Data:", ln=False)
    pdf.cell(lw * 0.5, 5, "Assinatura:", ln=True)

    pdf.set_font("Helvetica", "", 9)
    pdf._set_text(PRETO)
    pdf.cell(lw * 0.5, 6, data_hoje, ln=False)
    pdf.cell(lw * 0.5, 6, "_" * 30, ln=True)

    pdf._hr(0.5)

    # Retorna bytes
    return bytes(pdf.output())
