import sqlite3
import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

# ─── Carrega variáveis de ambiente ───────────────────────────────────────────
load_dotenv()

# ─── Validação de credenciais ───────────────────────────────────────────────
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError(
        "❌ ERRO CRÍTICO: Variável DATABASE_URL não encontrada!\n"
        "Certifique-se de que o arquivo .env existe na raiz do projeto com:\n"
        "DATABASE_URL=postgresql://user:password@host:port/database"
    )

# 1. Conecta no banco local antigo
con_local = sqlite3.connect('mobilidade_renapsi.db')
df = pd.read_sql_query("SELECT * FROM jovens_rotas", con_local)
con_local.close()

print(f"✅ {len(df)} registros lidos do arquivo local.")

# 2. Conecta no Supabase (Nuvem)
engine_nuvem = create_engine(DATABASE_URL)

# 3. Envia os dados para a nuvem
print("🚀 Enviando dados para o Supabase... aguarde.")
df.to_sql('jovens_rotas', engine_nuvem, if_exists='replace', index=False)
print("✨ Transplante concluído com sucesso! Seus dados agora moram na nuvem.")