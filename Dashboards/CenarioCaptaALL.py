import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Seus dados aqui (é só alterar os números que o percentual atualiza sozinho)
data = {
    'Categoria': [
        'Roteirizado total', 
        'Roteirizado casa x curso', 
        'Roteirizado casa x trabalho',
        'Implantados total', 
        'Implantados casa x curso', 
        'Implantados casa x trabalho'
    ],
    'Valores': [157, 126, 89, 641, 680, 707]
}
df = pd.DataFrame(data)

# Configurando o estilo tecnológico (Dark Theme)
plt.style.use('dark_background')
fig = plt.figure(figsize=(15, 7))
fig.patch.set_facecolor('#1a1a2e') # Fundo tech dark blue/gray

# Título Principal do Dashboard
fig.suptitle('Cenario Capta ROTEIRIZADOS', fontsize=22, fontweight='bold', color='#ffffff', y=0.98)

# --- 1. Gráfico Donut (Esquerda/Centro) ---
ax_donut = fig.add_subplot(1, 2, 1)
ax_donut.set_facecolor('#1a1a2e')

# Pegando apenas os totais para a pizza calcular o 100% corretamente
labels_donut = ['Roteirizados (Total)', 'Implantados (Total)']
sizes_donut = [df['Valores'][0], df['Valores'][3]] # Puxando do DataFrame
colors_donut = ['#f59e0b', '#10b981']

# Criando o Donut automatizado
wedges, texts, autotexts = ax_donut.pie(
    sizes_donut, 
    labels=labels_donut, 
    colors=colors_donut,
    autopct='%1.1f%%', 
    startangle=140, 
    pctdistance=0.75,
    textprops=dict(color="white", fontsize=12, fontweight='bold'),
    wedgeprops=dict(width=0.4, edgecolor='#1a1a2e', linewidth=2) # Faz o "furo" no meio
)

ax_donut.set_title("Proporção de Totais", color='white', fontsize=14, pad=20)
ax_donut.axis('equal')

# --- 2. Gráfico de Barras (Direita) ---
ax_bar = fig.add_subplot(1, 2, 2)
ax_bar.set_facecolor('#1a1a2e')

# Invertendo a ordem para os totais ficarem no topo visualmente
categorias = df['Categoria'][::-1]
valores = df['Valores'][::-1]
cores = ['#10b981', '#10b981', '#10b981', '#f59e0b', '#f59e0b', '#f59e0b']

# Criando as barras horizontais
bars = ax_bar.barh(categorias, valores, color=cores, height=0.6)

# Adicionando os números de forma automática no final de cada barra
ax_bar.bar_label(bars, padding=8, color='white', fontsize=11, fontweight='bold')

# Estilizando as linhas e eixos
ax_bar.set_title("Detalhamento por Categoria", color='white', fontsize=14, pad=20)
ax_bar.spines['top'].set_visible(False)
ax_bar.spines['right'].set_visible(False)
ax_bar.spines['left'].set_color('#444444')
ax_bar.spines['bottom'].set_color('#444444')
ax_bar.tick_params(axis='x', colors='white')
ax_bar.tick_params(axis='y', colors='white', labelsize=11)
ax_bar.set_xlabel('Quantidade', color='white', fontsize=12)

# Ajustando layout e salvando
plt.tight_layout(pad=3.0)
plt.savefig('meu_dashboard.png', dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
print("Dashboard gerado com sucesso!")