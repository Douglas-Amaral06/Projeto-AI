import os
#!/usr/bin/env python3
"""
Script de validação completa do sistema após reversão para SQLite
"""
import sys
import sqlite3
import os

def validar_arquivo_banco():
    """Valida se o arquivo do banco existe"""
    if os.path.exists('mobilidade_renapsi.db'):
        tamanho = os.path.getsize('mobilidade_renapsi.db')
        print(f"✅ Arquivo do banco existe ({tamanho} bytes)")
        return True
    else:
        print("❌ Arquivo do banco não encontrado")
        return False

def validar_tabelas():
    """Valida se todas as tabelas necessárias existem"""
    tabelas_necessarias = ['jovens_rotas', 'contestacoes', 'tokens_assinatura']
    
    try:
        conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
        cursor = conexao.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tabelas_existentes = [t[0] for t in cursor.fetchall()]
        conexao.close()
        
        faltando = []
        for tabela in tabelas_necessarias:
            if tabela in tabelas_existentes:
                print(f"✅ Tabela '{tabela}' existe")
            else:
                print(f"❌ Tabela '{tabela}' NÃO existe")
                faltando.append(tabela)
        
        return len(faltando) == 0
    except Exception as e:
        print(f"❌ Erro ao validar tabelas: {e}")
        return False

def validar_imports():
    """Valida se todos os imports necessários funcionam"""
    imports_necessarios = [
        ('sqlite3', 'SQLite3'),
        ('pandas', 'Pandas'),
        ('streamlit', 'Streamlit'),
        ('plotly', 'Plotly'),
        ('folium', 'Folium'),
        ('requests', 'Requests'),
        ('fpdf', 'FPDF2'),
    ]
    
    falhas = []
    for modulo, nome in imports_necessarios:
        try:
            __import__(modulo)
            print(f"✅ {nome} importado com sucesso")
        except ImportError:
            print(f"❌ {nome} NÃO está instalado")
            falhas.append(nome)
    
    return len(falhas) == 0

def validar_arquivos_principais():
    """Valida se os arquivos principais existem"""
    arquivos = [
        'app_piloto.py',
        'banco_dados.py',
        'apis.py',
        'agente_ia.py',
        'carta_pdf.py',
        'email_sender.py',
        'requirements.txt',
    ]
    
    faltando = []
    for arquivo in arquivos:
        if os.path.exists(arquivo):
            print(f"✅ {arquivo} existe")
        else:
            print(f"❌ {arquivo} NÃO existe")
            faltando.append(arquivo)
    
    return len(faltando) == 0

def validar_sem_postgres():
    """Valida que não há referências ao PostgreSQL nos arquivos principais"""
    arquivos_verificar = ['banco_dados.py', 'app_piloto.py', 'apis.py']
    termos_proibidos = ['sqlalchemy', 'psycopg2', 'create_engine', 'postgresql']
    
    problemas = []
    for arquivo in arquivos_verificar:
        if os.path.exists(arquivo):
            with open(arquivo, 'r', encoding='utf-8') as f:
                conteudo = f.read().lower()
                for termo in termos_proibidos:
                    if termo in conteudo:
                        problemas.append(f"{arquivo} contém '{termo}'")
    
    if problemas:
        for problema in problemas:
            print(f"⚠️  {problema}")
        return False
    else:
        print("✅ Nenhuma referência ao PostgreSQL encontrada")
        return True

def validar_estrutura_tabela_jovens():
    """Valida se a tabela jovens_rotas tem todas as colunas necessárias"""
    colunas_necessarias = [
        'id', 'nome', 'cpf', 'cep_casa', 'cep_trabalho', 'matricula',
        'status_rota', 'email', 'celular', 'numero_casa', 'coordenadas',
        'data_consulta', 'sla_segundos', 'assinatura_path', 'assinatura_data', 'assinatura_ip'
    ]
    
    try:
        conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
        cursor = conexao.cursor()
        cursor.execute("PRAGMA table_info(jovens_rotas)")
        colunas_existentes = [col[1] for col in cursor.fetchall()]
        conexao.close()
        
        faltando = []
        for coluna in colunas_necessarias:
            if coluna in colunas_existentes:
                print(f"✅ Coluna '{coluna}' existe")
            else:
                print(f"❌ Coluna '{coluna}' NÃO existe")
                faltando.append(coluna)
        
        return len(faltando) == 0
    except Exception as e:
        print(f"❌ Erro ao validar estrutura: {e}")
        return False

if __name__ == "__main__":
    print("="*70)
    print("🔍 VALIDAÇÃO COMPLETA DO SISTEMA - REVERSÃO SQLITE")
    print("="*70)
    
    testes = [
        ("Arquivo do banco de dados", validar_arquivo_banco),
        ("Tabelas do banco", validar_tabelas),
        ("Estrutura da tabela jovens_rotas", validar_estrutura_tabela_jovens),
        ("Bibliotecas Python", validar_imports),
        ("Arquivos principais", validar_arquivos_principais),
        ("Ausência de PostgreSQL", validar_sem_postgres),
    ]
    
    resultados = []
    
    for nome, teste in testes:
        print(f"\n{'─'*70}")
        print(f"📝 Validando: {nome}")
        print(f"{'─'*70}")
        resultado = teste()
        resultados.append((nome, resultado))
    
    print(f"\n{'='*70}")
    print("📊 RESUMO DA VALIDAÇÃO")
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
        print("\n🎉 SISTEMA VALIDADO COM SUCESSO!")
        print("✅ Todos os componentes estão funcionando corretamente")
        print("✅ Reversão para SQLite concluída com êxito")
        print("\n🚀 Você pode executar o app com: streamlit run app_piloto.py")
        sys.exit(0)
    else:
        print(f"\n⚠️  ATENÇÃO: {falhas} validação(ões) falharam")
        print("❌ Corrija os problemas acima antes de executar o app")
        sys.exit(1)

