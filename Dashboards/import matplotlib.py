import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Data - Somas e separação das cidades
data_faltam = {'Guarulhos': 29, 'Mogi das Cruzes': 13, 'Santo André': 17,'Campinas': 15, 'Ribeirão Preto': 2, 'São Paulo': 132}
confirmados = 460
analises = 60
total = sum(data_faltam.values()) + confirmados + analises

# Setup Figure - Full HD (1920x1080)
fig = plt.figure(figsize=(19.2, 10.8), dpi=70)
fig.patch.set_facecolor('#0f172a') # Dark slate background

# Titulo Principal do Dashboard
plt.suptitle('Análise VT - Gestão RH', fontsize=42, color='white', fontweight='bold', y=0.95)

# 1. Cartões de KPIs principais (Represenção visual usando caixas de texto)
def draw_kpi(ax, label, value, color, pos_y):
    ax.text(0.5, pos_y, str(value), fontsize=60, color=color, fontweight='bold', ha='center')
    ax.text(0.5, pos_y-0.12, label, fontsize=20, color='white', alpha=0.8, ha='center')

ax_kpis = fig.add_axes([0.05, 0.1, 0.25, 0.75])
ax_kpis.axis('off')
draw_kpi(ax_kpis, 'Total na Base', total, '#f8fafc', 0.85)
draw_kpi(ax_kpis, 'Confirmados', confirmados, '#10b981', 0.60)
draw_kpi(ax_kpis, 'Análises Pendentes', analises, '#8b5cf6', 0.35)
draw_kpi(ax_kpis, 'Faltam Enviar (Total)', sum(data_faltam.values()), '#f59e0b', 0.10)

# 2. Gráfico de Pizza - Visão Geral - (Donut Chart)
ax_donut = fig.add_axes([0.35, 0.45, 0.25, 0.4])
labels_donut = ['Confirmados', 'Faltam', 'Análises']
sizes_donut = [confirmados, sum(data_faltam.values()), analises]
colors_donut = ['#10b981', '#f59e0b', '#8b5cf6']
wedges, texts, autotexts = ax_donut.pie(sizes_donut, labels=None, autopct='%1.1f%%',# Auto Formação percentual - vendi minha alma para chegar nesse resultado
                                       startangle=90, colors=colors_donut, pctdistance=0.85,
                                       textprops={'color':"w", 'weight':'bold', 'fontsize':15})
centre_circle = plt.Circle((0,0), 0.70, fc='#0f172a')
ax_donut.add_artist(centre_circle)
ax_donut.set_title('Distribuição Percentual', color='white', fontsize=22, pad=18)

# 3. Gráfico das barras - "Pendências por Cidade"
ax_bar = fig.add_axes([0.65, 0.15, 0.3, 0.7])
ax_bar.set_facecolor('#1e293b')
cities = list(data_faltam.keys())
counts = list(data_faltam.values())
bars = ax_bar.barh(cities, counts, color='#f59e0b', edgecolor='white', alpha=0.9)
ax_bar.set_title('Pendências por Cidade', color='white', fontsize=22, pad=18)
ax_bar.tick_params(axis='both', colors='white', labelsize=14)
ax_bar.spines['top'].set_visible(False)
ax_bar.spines['right'].set_visible(False)
ax_bar.spines['bottom'].set_color("#FFA600D6")
ax_bar.spines['left'].set_color("#FFA600D6")

# Adicionar valores às barras
for bar in bars:
    width = bar.get_width()
    ax_bar.text(width + 1, bar.get_y() + bar.get_height()/2, f'{int(width)}',
                ha='left', va='center', color='white', fontsize=16, fontweight='bold')


plt.savefig('analise_vt_dashboard_fullhd.png', facecolor=fig.get_facecolor(), dpi=100)

# Salvar CSV para gerenciamento
df_report = pd.DataFrame({
    'Categoria': ['Confirmados', 'Análises não concluídas', 'Faltam (Guarulhos)', 'Faltam (Mogi)', 'Faltam (Santo André)', 'Faltam(Campinas)', 'Faltam(Ribeirão Preto)', 'Faltam(São Paulo)'],
    'Quantidade': [460, 60, 29, 13, 17, 15, 2, 132] 
})
plt.show()
df_report.to_csv('relatorio_gestao_vt.csv', index=False)