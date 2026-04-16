#!/usr/bin/env python3
"""
Script de Validação de Caminhos
Verifica se todos os arquivos Python conseguem conectar ao banco de dados
após a reestruturação para microsserviços.
"""

import os
import sys
import sqlite3

def validar_caminho_banco():
    """Valida se o caminho do banco de dados está correto"""
    print("=" * 60)
    print("🔍 VALIDAÇÃO DE CAMINHOS - ARQUITETURA DE MICROSSERVIÇOS")
    print("=" * 60)
    
    # Caminho esperado
    db_path = os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db')
    
    print(f"\n📍 Arquivo atual: {__file__}")
    print(f"📍 Diretório do arquivo: {os.path.dirname(__file__)}")
    print(f"📍 Caminho do banco de dados: {db_path}")
    print(f"📍 Caminho absoluto: {os.path.abspath(db_path)}")
    
    # Verifica se o banco existe
    if os.path.exists(db_path):
        print(f"\n✅ Banco de dados encontrado!")
        print(f"   Tamanho: {os.path.getsize(db_path) / 1024:.2f} KB")
    else:
        print(f"\n❌ Banco de dados NÃO encontrado em: {db_path}")
        return False
    
    # Tenta conectar
    try:
        conexao = sqlite3.connect(db_path)
        cursor = conexao.cursor()
        
        # Verifica tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tabelas = cursor.fetchall()
        
        print(f"\n✅ Conexão com banco de dados estabelecida!")
        print(f"   Tabelas encontradas: {len(tabelas)}")
        
        for tabela in tabelas:
            print(f"     • {tabela[0]}")
        
        conexao.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Erro ao conectar ao banco de dados:")
        print(f"   {str(e)}")
        return False

def validar_imports():
    """Valida se os imports necessários estão disponíveis"""
    print("\n" + "=" * 60)
    print("📦 VALIDAÇÃO DE IMPORTS")
    print("=" * 60)
    
    imports_necessarios = [
        ('os', 'Sistema operacional'),
        ('sqlite3', 'Banco de dados SQLite'),
        ('pandas', 'Manipulação de dados'),
        ('streamlit', 'Framework web'),
        ('dotenv', 'Variáveis de ambiente'),
    ]
    
    todos_ok = True
    for modulo, descricao in imports_necessarios:
        try:
            __import__(modulo)
            print(f"✅ {modulo:15} - {descricao}")
        except ImportError:
            print(f"❌ {modulo:15} - {descricao} (NÃO INSTALADO)")
            todos_ok = False
    
    return todos_ok

def validar_estrutura():
    """Valida a estrutura de diretórios"""
    print("\n" + "=" * 60)
    print("📁 VALIDAÇÃO DE ESTRUTURA")
    print("=" * 60)
    
    estrutura_esperada = {
        'Projeto_RH': 'Microsserviço de RH',
        'Portal_Candidato': 'Microsserviço do Portal',
        'Portal_Candidato/uploads_documentos': 'Armazenamento de documentos',
    }
    
    raiz = os.path.dirname(os.path.dirname(__file__))
    todos_ok = True
    
    for caminho, descricao in estrutura_esperada.items():
        caminho_completo = os.path.join(raiz, caminho)
        if os.path.exists(caminho_completo):
            print(f"✅ {caminho:40} - {descricao}")
        else:
            print(f"❌ {caminho:40} - {descricao} (NÃO ENCONTRADO)")
            todos_ok = False
    
    # Verifica banco de dados na raiz
    db_path = os.path.join(raiz, 'mobilidade_renapsi.db')
    if os.path.exists(db_path):
        print(f"✅ {'mobilidade_renapsi.db':40} - Banco de dados central")
    else:
        print(f"❌ {'mobilidade_renapsi.db':40} - Banco de dados central (NÃO ENCONTRADO)")
        todos_ok = False
    
    return todos_ok

def main():
    """Executa todas as validações"""
    print("\n")
    
    resultado_caminho = validar_caminho_banco()
    resultado_imports = validar_imports()
    resultado_estrutura = validar_estrutura()
    
    print("\n" + "=" * 60)
    print("📊 RESUMO DA VALIDAÇÃO")
    print("=" * 60)
    
    if resultado_caminho and resultado_imports and resultado_estrutura:
        print("\n✅ TODAS AS VALIDAÇÕES PASSARAM!")
        print("\n🚀 O projeto está pronto para ser executado:")
        print("   streamlit run Projeto_RH/app_piloto.py")
        return 0
    else:
        print("\n❌ ALGUMAS VALIDAÇÕES FALHARAM!")
        print("\nVerifique os erros acima e corrija-os antes de prosseguir.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
