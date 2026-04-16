import os
#!/usr/bin/env python3
"""
Teste de importação e inicialização do app_piloto.py
"""
import sys
import os

def testar_imports_app():
    """Testa se todos os imports do app funcionam"""
    print("🧪 Testando imports do app_piloto.py...\n")
    
    try:
        print("📦 Importando streamlit...")
        import streamlit as st
        print("✅ streamlit OK")
        
        print("📦 Importando sqlite3...")
        import sqlite3
        print("✅ sqlite3 OK")
        
        print("📦 Importando pandas...")
        import pandas as pd
        print("✅ pandas OK")
        
        print("📦 Importando requests...")
        import requests
        print("✅ requests OK")
        
        print("📦 Importando plotly...")
        import plotly.express as px
        print("✅ plotly OK")
        
        print("📦 Importando folium...")
        import folium
        print("✅ folium OK")
        
        print("📦 Importando streamlit_folium...")
        from streamlit_folium import st_folium
        print("✅ streamlit_folium OK")
        
        print("📦 Importando banco_dados...")
        import banco_dados
        print("✅ banco_dados OK")
        
        print("📦 Importando apis...")
        import apis
        print("✅ apis OK")
        
        print("📦 Importando agente_ia...")
        import agente_ia
        print("✅ agente_ia OK")
        
        print("📦 Importando carta_pdf...")
        from carta_pdf import gerar_carta_pdf
        print("✅ carta_pdf OK")
        
        print("📦 Importando email_sender...")
        from email_sender import enviar_carta_por_email
        print("✅ email_sender OK")
        
        return True
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False

def testar_funcoes_banco():
    """Testa se as funções do banco estão acessíveis"""
    print("\n🧪 Testando funções do banco_dados.py...\n")
    
    try:
        from banco_dados import (
            carregar_dados,
            inserir_novo_jovem,
            cpf_ja_existe,
            excluir_jovem,
            atualizar_dados_funcionario,
            obter_dados_dashboard,
            registrar_contestacao,
            resolver_contestacao,
            inicializar_banco_completo,
            atualizar_consulta_com_assinatura,
            obter_status_consulta,
            verificar_token_usado
        )
        
        print("✅ Todas as funções do banco_dados.py estão acessíveis")
        return True
    except Exception as e:
        print(f"❌ ERRO ao importar funções: {e}")
        return False

def testar_funcoes_apis():
    """Testa se as funções das APIs estão acessíveis"""
    print("\n🧪 Testando funções do apis.py...\n")
    
    try:
        from apis import (
            buscar_endereco_viacep,
            motor_de_rotas_gratuito,
            obter_coordenadas_reais
        )
        
        print("✅ Todas as funções do apis.py estão acessíveis")
        return True
    except Exception as e:
        print(f"❌ ERRO ao importar funções: {e}")
        return False

def testar_conexao_banco():
    """Testa conexão com o banco"""
    print("\n🧪 Testando conexão com o banco...\n")
    
    try:
        import sqlite3
        conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
        cursor = conexao.cursor()
        
        # Testa cada tabela
        tabelas = ['jovens_rotas', 'contestacoes', 'tokens_assinatura']
        for tabela in tabelas:
            cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
            count = cursor.fetchone()[0]
            print(f"✅ Tabela '{tabela}': {count} registros")
        
        conexao.close()
        return True
    except Exception as e:
        print(f"❌ ERRO na conexão: {e}")
        return False

if __name__ == "__main__":
    print("="*70)
    print("🔍 TESTE DE INICIALIZAÇÃO DO APP")
    print("="*70)
    
    testes = [
        ("Imports do app", testar_imports_app),
        ("Funções do banco_dados", testar_funcoes_banco),
        ("Funções das APIs", testar_funcoes_apis),
        ("Conexão com banco", testar_conexao_banco),
    ]
    
    resultados = []
    
    for nome, teste in testes:
        print(f"\n{'─'*70}")
        print(f"📝 {nome}")
        print(f"{'─'*70}")
        resultado = teste()
        resultados.append((nome, resultado))
    
    print(f"\n{'='*70}")
    print("📊 RESUMO DOS TESTES")
    print(f"{'='*70}")
    
    sucessos = sum(1 for _, r in resultados if r)
    falhas = len(resultados) - sucessos
    
    for nome, resultado in resultados:
        status = "✅ PASSOU" if resultado else "❌ FALHOU"
        print(f"{status} - {nome}")
    
    print(f"\n{'─'*70}")
    print(f"Total: {sucessos}/{len(resultados)} testes passaram")
    print(f"{'─'*70}")
    
    if falhas == 0:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("✅ O app está pronto para ser executado")
        print("\n🚀 Execute com: streamlit run app_piloto.py")
        sys.exit(0)
    else:
        print(f"\n⚠️  ATENÇÃO: {falhas} teste(s) falharam")
        print("❌ Corrija os problemas antes de executar o app")
        sys.exit(1)

