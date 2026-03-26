import matplotlib.pyplot as plt
import pandas as pd

# 1. Dados e Configurações
data_faltam = {
    "TAM LINHAS AEREAS S/A": 75,
    "CET": 108,
    "PEPSICO": 37,
    "COCA COLA": 14,
    "Outros": 171
}

confirmados = 32
analises = 1

# --- Lógica para o Gráfico Donut (Unificando tudo) ---
dados_donut = data_faltam.copy()
dados_donut["CONFIRMADOS"] = confirmados  # Adiciona confirmados
dados_donut["EM ANÁLISE"] = analises      # Adiciona análises

df_donut = pd.DataFrame(list(dados_donut.items()), columns=['Legenda', 'Valor'])
df_barras = pd.DataFrame(list(data_faltam.items()), columns=['Empresa', 'Quantidade']).sort_values('Quantidade')

# O total geral agora é a soma de tudo que está no dicionário do donut
total_geral = sum(dados_donut.values())

# 2. Configuração Visual (Tema Dark GitHub)
plt.style.use('dark_background')
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))
fig.suptitle(f'STATUS OPERACIONAL - TOTAL: {total_geral}', fontsize=22, color="#ffffff", fontweight='bold')

# --- GRÁFICO 1: DONUT ---
# Cores: Tons de azul (empresas), Verde (Confirmados) e Amarelo/Laranja (Análises)
cores_donut = ['#FFA600D6', '#FFA600D6', '#FFA600D6', '#FFA600D6', '#FFA600D6', '#238636', '#8b5cf6'] 

ax1.pie(df_donut['Valor'], labels=df_donut['Legenda'], autopct='%1.1f%%', 
        startangle=140, colors=cores_donut, pctdistance=0.80, 
        wedgeprops={'edgecolor': '#0d1117', 'linewidth': 2})

# Buraco do Donut
centro = plt.Circle((0,0), 0.65, fc='#0d1117')
ax1.add_artist(centro)
ax1.set_title("Visão Geral do Processo (%)", fontsize=15, pad=20)

# --- GRÁFICO 2: BARRAS (Pendências por Empresa) ---
bars = ax2.barh(df_barras['Empresa'], df_barras['Quantidade'], color='#FFA600D6')
ax2.set_title("Faltam Por Empresa", fontsize=15, pad=20)
ax2.bar_label(bars, padding=5, color='white', fontweight='bold')

# Estética Barras
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
ax2.set_xlabel("Quantidade de Casos")

# 3. Rodapé com Informações Extras
info_texto = f"Em Análise: {analises}  |  Total Pendentes: {sum(data_faltam.values())}  |  Total Confirmados: {confirmados}"
plt.figtext(0.5, 0.05, info_texto, ha="center", fontsize=12, 
            bbox={"facecolor":"#161b22", "alpha":0.8, "pad":8, "edgecolor":"#30363d"})

plt.tight_layout(rect=[0, 0.08, 1, 0.95])
plt.show()