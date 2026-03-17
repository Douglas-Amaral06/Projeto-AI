import matplotlib.pyplot as plt
import pandas as pd

# 1. Dados atualizados
folhas_entregues = 100

dados_empresas = [
    ('TAM LINHAS AEREAS S/A.', 341),
    ('COMPANHIA DE ENGENHARIA DE TRAFEGO', 172),
    ('PEPSICO DO BRASIL LTDA', 66),
    ('BANCO DO BRASIL S.A.', 22),
    ('SPAL INDUSTRIA BRASILEIRA DE BEBIDAS S/A', 22),
    ('PEPSICO DO BRASIL INDUSTRIA E COM. DE ALIMENTOS LTDA.', 19), 
    ('KAVAK TECNOLOGIA E COMERCIO DE VEICULOS LTDA.', 17),
    ('C. CARVALHO GENEROSO MERCADO LTDA', 13),
    ('CAIXA ECONOMICA FEDERAL', 13),
    ('CEAGESP - COMPANHIA DE ENTREPOSTOS E ARMAZENS...', 12),
    ('OUTROS', 222)
]

# Cria o dataframe e inverte a ordem pra ficar do maior pro menor no gráfico de barras
df = pd.DataFrame(dados_empresas, columns=['Empresa', 'Frequencia'])
df = df.sort_values(by='Frequencia', ascending=True)

# Cálculos
faltam_entregar = df['Frequencia'].sum()
total = folhas_entregues + faltam_entregar

# 2. Configuração de cores 
cor_fundo = '#0b132b' 
cor_texto = '#ffffff'
cor_entregue = '#10b981' 
cor_falta = '#f59e0b'
cor_total = '#3b82f6'

#  largura da imagem e altura da imagem, e cor de fundo do gráfico
fig = plt.figure(figsize=(18, 8), facecolor=cor_fundo) 
fig.suptitle("Controle Folha Ponto", fontsize=24, color=cor_texto, fontweight='bold', y=0.95)

# Divisão da tela em 6 partes horizontais.
gs = fig.add_gridspec(2, 6, height_ratios=[1, 3], wspace=1.0) 

# --- KPIs (Linha de cima) ---
ax_kpi1 = fig.add_subplot(gs[0, 0:2])
ax_kpi2 = fig.add_subplot(gs[0, 2:4])
ax_kpi3 = fig.add_subplot(gs[0, 4:6])

for ax in [ax_kpi1, ax_kpi2, ax_kpi3]:
    ax.set_axis_off()

ax_kpi1.text(0.5, 0.5, f"Entregues\n\n{folhas_entregues}", ha='center', va='center', fontsize=18, color=cor_fundo, fontweight='bold', bbox=dict(facecolor=cor_entregue, boxstyle='round,pad=1.2', edgecolor='none'))
ax_kpi2.text(0.5, 0.5, f"Faltam\n\n{faltam_entregar}", ha='center', va='center', fontsize=18, color=cor_fundo, fontweight='bold', bbox=dict(facecolor=cor_falta, boxstyle='round,pad=1.2', edgecolor='none'))
ax_kpi3.text(0.5, 0.5, f"Total\n\n{total}", ha='center', va='center', fontsize=18, color=cor_fundo, fontweight='bold', bbox=dict(facecolor=cor_total, boxstyle='round,pad=1.2', edgecolor='none'))

# --- Gráfico Donut (Embaixo, Esquerda) ---
ax_donut = fig.add_subplot(gs[1, 0:2])
valores = [folhas_entregues, faltam_entregar]
labels = ['Entregues', 'A Entregar']
cores = [cor_entregue, cor_falta]

# Personalização do Donut
wedges, texts, autotexts = ax_donut.pie(
    valores, labels=labels, colors=cores, autopct='%1.1f%%', startangle=140, 
    textprops=dict(color=cor_texto, fontsize=12, fontweight='bold'),
    wedgeprops=dict(width=0.4, edgecolor=cor_fundo, linewidth=3),
    center=(-0.3, 0) 
)
ax_donut.axis('equal') # Garante que o círculo não fique ovalado com o reposicionamento

# --- Gráfico de Barras (Embaixo, Direita) ---
#  gráfico de barras horizontal, invertendo a ordem do dataframe pra ficar do maior pro menor
ax_bar = fig.add_subplot(gs[1, 3:6]) 
ax_bar.set_facecolor(cor_fundo)
bars = ax_bar.barh(df['Empresa'], df['Frequencia'], color=cor_falta)

ax_bar.spines['top'].set_visible(False)
ax_bar.spines['right'].set_visible(False)
ax_bar.spines['left'].set_color(cor_texto)
ax_bar.spines['bottom'].set_color(cor_texto)
ax_bar.tick_params(axis='x', colors=cor_texto)
ax_bar.tick_params(axis='y', colors=cor_texto, labelsize=10)

# Valores nas barras
for bar in bars:
    width = bar.get_width()
    ax_bar.text(width + max(df['Frequencia'])*0.01, bar.get_y() + bar.get_height()/2, 
                f'{int(width)}', ha='left', va='center', color=cor_texto, fontweight='bold', fontsize=11)

ax_bar.set_title("Top 10 Empresas + Outros", color=cor_texto, fontsize=14, fontweight='bold')

#plt.tight_layout()
plt.show()