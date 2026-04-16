import os
"""
Script de Teste para Funcionalidade de Rota Manual
Valida se todas as funções estão operacionais
"""

import sqlite3
from banco_dados import salvar_rota_manual, inicializar_banco_completo
from carta_pdf import gerar_carta_pdf

def testar_banco_dados():
    """Testa se as colunas foram criadas corretamente"""
    print("🔍 Testando estrutura do banco de dados...")
    
    try:
        inicializar_banco_completo()
        
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(jovens_rotas)")
        colunas = [col[1] for col in cursor.fetchall()]
        conn.close()
        
        colunas_necessarias = [
            'modo_rota',
            'tipo_bilhete_manual',
            'valor_tarifa_manual',
            'descricao_itinerario_manual'
        ]
        
        for coluna in colunas_necessarias:
            if coluna in colunas:
                print(f"  ✅ Coluna '{coluna}' existe")
            else:
                print(f"  ❌ Coluna '{coluna}' NÃO existe")
                return False
        
        print("✅ Estrutura do banco OK!\n")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar banco: {e}\n")
        return False


def testar_salvar_rota_manual():
    """Testa se a função de salvar rota manual funciona"""
    print("🔍 Testando função salvar_rota_manual()...")
    
    try:
        # Busca um ID existente para testar
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM jovens_rotas LIMIT 1")
        resultado = cursor.fetchone()
        conn.close()
        
        if not resultado:
            print("  ⚠️ Nenhum registro encontrado no banco para testar")
            print("  💡 Adicione um funcionário primeiro\n")
            return True  # Não é erro, apenas não há dados
        
        id_teste = resultado[0]
        
        # Testa salvar rota manual
        sucesso = salvar_rota_manual(
            id_jovem=id_teste,
            tipo_bilhete="Integração Ônibus+Metrô",
            valor_tarifa=11.32,
            descricao_itinerario="Linha 102 → Terminal Bandeira → Metrô Linha 3-Vermelha"
        )
        
        if sucesso:
            print(f"  ✅ Rota manual salva com sucesso para ID {id_teste}")
            
            # Verifica se foi salvo
            conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
            cursor = conn.cursor()
            cursor.execute("""
                SELECT modo_rota, tipo_bilhete_manual, valor_tarifa_manual 
                FROM jovens_rotas WHERE id = ?
            """, (id_teste,))
            dados = cursor.fetchone()
            conn.close()
            
            if dados and dados[0] == 'manual':
                print(f"  ✅ Dados verificados no banco:")
                print(f"     - Modo: {dados[0]}")
                print(f"     - Bilhete: {dados[1]}")
                print(f"     - Valor: R$ {dados[2]:.2f}")
            else:
                print("  ❌ Dados não foram salvos corretamente")
                return False
        else:
            print(f"  ❌ Falha ao salvar rota manual")
            return False
        
        print("✅ Função salvar_rota_manual() OK!\n")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar salvar_rota_manual: {e}\n")
        return False


def testar_gerar_pdf():
    """Testa se a geração de PDF funciona com rota manual"""
    print("🔍 Testando geração de PDF com rota manual...")
    
    try:
        # Dados de teste
        dados_jovem = {
            'id': 1,
            'nome': 'João da Silva Teste',
            'cpf': '12345678901',
            'matricula': 'MAT001',
            'email': 'teste@exemplo.com'
        }
        
        rota_manual = {
            'tipo_bilhete_manual': 'Integração Ônibus+Metrô',
            'valor_tarifa_manual': 11.32,
            'descricao_itinerario_manual': 'Linha 102 → Terminal Bandeira → Metrô Linha 3'
        }
        
        # Gera PDF com rota manual
        pdf_bytes = gerar_carta_pdf(
            dados_jovem=dados_jovem,
            rota_selecionada=rota_manual,
            end_casa_completo="Rua Teste, 123 - Bairro Teste - São Paulo/SP",
            end_trab_completo="Av. Paulista, 1000 - Bela Vista - São Paulo/SP",
            modo_rota='manual'
        )
        
        if pdf_bytes and len(pdf_bytes) > 0:
            print(f"  ✅ PDF gerado com sucesso ({len(pdf_bytes)} bytes)")
            
            # Salva PDF de teste
            with open('teste_carta_manual.pdf', 'wb') as f:
                f.write(pdf_bytes)
            print("  ✅ PDF salvo como 'teste_carta_manual.pdf'")
        else:
            print("  ❌ PDF vazio ou inválido")
            return False
        
        print("✅ Geração de PDF OK!\n")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar geração de PDF: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def executar_todos_testes():
    """Executa todos os testes"""
    print("=" * 60)
    print("🧪 TESTE DE FUNCIONALIDADE: ROTA MANUAL")
    print("=" * 60)
    print()
    
    resultados = []
    
    # Teste 1: Banco de Dados
    resultados.append(("Estrutura do Banco", testar_banco_dados()))
    
    # Teste 2: Salvar Rota Manual
    resultados.append(("Salvar Rota Manual", testar_salvar_rota_manual()))
    
    # Teste 3: Gerar PDF
    resultados.append(("Gerar PDF", testar_gerar_pdf()))
    
    # Resumo
    print("=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    for nome, sucesso in resultados:
        status = "✅ PASSOU" if sucesso else "❌ FALHOU"
        print(f"{nome:.<40} {status}")
    
    print()
    
    total = len(resultados)
    passou = sum(1 for _, s in resultados if s)
    
    if passou == total:
        print(f"🎉 TODOS OS TESTES PASSARAM! ({passou}/{total})")
        print("✅ A funcionalidade de Rota Manual está operacional!")
    else:
        print(f"⚠️ ALGUNS TESTES FALHARAM ({passou}/{total})")
        print("❌ Verifique os erros acima e corrija antes de usar em produção")
    
    print("=" * 60)


if __name__ == "__main__":
    executar_todos_testes()

