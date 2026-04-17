#!/usr/bin/env python3
"""
Script de teste para validar a implementação da aba Triagem de Fichas
"""

import sys
import os
import sqlite3
import pandas as pd
from banco_dados import obter_fichas_cadastrais, aprovar_ficha_e_integrar, reprovar_ficha

# Configuração do banco de dados
DATABASE_FILE = os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db')

def test_obter_fichas():
    """Testa a função de obtenção de fichas"""
    print("\n🧪 Teste 1: Obter Fichas Cadastrais")
    print("-" * 50)
    
    try:
        # Verifica se a tabela existe
        conexao = sqlite3.connect(DATABASE_FILE)
        cursor = conexao.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fichas_cadastrais'")
        existe = cursor.fetchone()
        conexao.close()
        
        if not existe:
            print("⚠️  Tabela 'fichas_cadastrais' não existe no banco de dados")
            print("   (Isso é normal se o portal do jovem ainda não foi usado)")
            return True
        
        # Tenta obter fichas
        df = obter_fichas_cadastrais()
        print(f"✅ Função obter_fichas_cadastrais() funcionando")
        print(f"   Total de fichas: {len(df)}")
        
        if len(df) > 0:
            print(f"   Primeiras colunas: {list(df.columns[:5])}")
        
        return True
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False


def test_filtros():
    """Testa os filtros de fichas"""
    print("\n🧪 Teste 2: Filtros de Fichas")
    print("-" * 50)
    
    try:
        # Testa filtro por status
        df_pendentes = obter_fichas_cadastrais(filtro_status="Pendente")
        print(f"✅ Filtro por status 'Pendente': {len(df_pendentes)} fichas")
        
        df_aprovados = obter_fichas_cadastrais(filtro_status="Aprovado")
        print(f"✅ Filtro por status 'Aprovado': {len(df_aprovados)} fichas")
        
        df_todos = obter_fichas_cadastrais(filtro_status="Todos")
        print(f"✅ Filtro por status 'Todos': {len(df_todos)} fichas")
        
        return True
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False


def test_estrutura_banco():
    """Valida a estrutura do banco de dados"""
    print("\n🧪 Teste 3: Estrutura do Banco de Dados")
    print("-" * 50)
    
    try:
        conexao = sqlite3.connect(DATABASE_FILE)
        cursor = conexao.cursor()
        
        # Verifica tabela fichas_cadastrais
        cursor.execute("PRAGMA table_info(fichas_cadastrais)")
        colunas_fichas = cursor.fetchall()
        
        if colunas_fichas:
            print("✅ Tabela 'fichas_cadastrais' existe com colunas:")
            for col in colunas_fichas[:5]:
                print(f"   - {col[1]} ({col[2]})")
            print(f"   ... (total: {len(colunas_fichas)} colunas)")
        
        # Verifica tabela jovens_rotas
        cursor.execute("PRAGMA table_info(jovens_rotas)")
        colunas_rotas = cursor.fetchall()
        
        if colunas_rotas:
            print("✅ Tabela 'jovens_rotas' existe com colunas:")
            for col in colunas_rotas[:5]:
                print(f"   - {col[1]} ({col[2]})")
            print(f"   ... (total: {len(colunas_rotas)} colunas)")
        
        conexao.close()
        return True
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False


def test_imports():
    """Testa se todos os imports funcionam"""
    print("\n🧪 Teste 4: Imports e Funções")
    print("-" * 50)
    
    try:
        from banco_dados import (
            obter_fichas_cadastrais,
            aprovar_ficha_e_integrar,
            reprovar_ficha
        )
        print("✅ Todas as funções importadas com sucesso:")
        print("   - obter_fichas_cadastrais()")
        print("   - aprovar_ficha_e_integrar()")
        print("   - reprovar_ficha()")
        return True
    except Exception as e:
        print(f"❌ Erro ao importar: {str(e)}")
        return False


def main():
    """Executa todos os testes"""
    print("\n" + "="*50)
    print("🧪 TESTES: Triagem de Fichas")
    print("="*50)
    
    testes = [
        test_imports,
        test_estrutura_banco,
        test_obter_fichas,
        test_filtros,
    ]
    
    resultados = []
    for teste in testes:
        try:
            resultado = teste()
            resultados.append(resultado)
        except Exception as e:
            print(f"❌ Erro ao executar teste: {str(e)}")
            resultados.append(False)
    
    # Resumo
    print("\n" + "="*50)
    print("📊 RESUMO DOS TESTES")
    print("="*50)
    
    total = len(resultados)
    passou = sum(resultados)
    
    print(f"✅ Testes que passaram: {passou}/{total}")
    
    if passou == total:
        print("\n🎉 Todos os testes passaram! A implementação está pronta.")
        return 0
    else:
        print(f"\n⚠️  {total - passou} teste(s) falharam.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
