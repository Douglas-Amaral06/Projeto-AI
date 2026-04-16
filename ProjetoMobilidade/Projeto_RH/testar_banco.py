import os
#!/usr/bin/env python3
"""
Script de teste para verificar se todas as funções do banco_dados.py funcionam
"""
import sqlite3
from banco_dados import *

def testar_conexao():
    """Testa se consegue conectar ao banco"""
    try:
        conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
        cursor = conexao.cursor()
        cursor.execute("SELECT COUNT(*) FROM jovens_rotas")
        total = cursor.fetchone()[0]
        conexao.close()
        print(f"✅ Conexão OK - {total} registros na tabela jovens_rotas")
        return True
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return False

def testar_carregar_dados():
    """Testa a função carregar_dados()"""
    try:
        df = carregar_dados()
        print(f"✅ carregar_dados() OK - {len(df)} registros carregados")
        return True
    except Exception as e:
        print(f"❌ Erro em carregar_dados(): {e}")
        return False

def testar_cpf_existe():
    """Testa a função cpf_ja_existe()"""
    try:
        resultado = cpf_ja_existe("12345678900")
        print(f"✅ cpf_ja_existe() OK - Resultado: {resultado}")
        return True
    except Exception as e:
        print(f"❌ Erro em cpf_ja_existe(): {e}")
        return False

def testar_dashboard():
    """Testa a função obter_dados_dashboard()"""
    try:
        total, sla = obter_dados_dashboard()
        print(f"✅ obter_dados_dashboard() OK - Total: {total}, SLA: {sla:.2f}s")
        return True
    except Exception as e:
        print(f"❌ Erro em obter_dados_dashboard(): {e}")
        return False

def testar_inicializacao():
    """Testa a função inicializar_banco_completo()"""
    try:
        inicializar_banco_completo()
        print(f"✅ inicializar_banco_completo() OK")
        return True
    except Exception as e:
        print(f"❌ Erro em inicializar_banco_completo(): {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testando funções do banco_dados.py...\n")
    
    testes = [
        ("Conexão ao banco", testar_conexao),
        ("Inicialização completa", testar_inicializacao),
        ("Carregar dados", testar_carregar_dados),
        ("Verificar CPF", testar_cpf_existe),
        ("Dashboard", testar_dashboard),
    ]
    
    sucessos = 0
    falhas = 0
    
    for nome, teste in testes:
        print(f"\n📝 Testando: {nome}")
        if teste():
            sucessos += 1
        else:
            falhas += 1
    
    print(f"\n{'='*60}")
    print(f"📊 Resultado dos testes:")
    print(f"   ✅ Sucessos: {sucessos}")
    print(f"   ❌ Falhas: {falhas}")
    print(f"{'='*60}")
    
    if falhas == 0:
        print("\n🎉 Todos os testes passaram! O banco está funcionando corretamente.")
    else:
        print(f"\n⚠️  {falhas} teste(s) falharam. Verifique os erros acima.")

