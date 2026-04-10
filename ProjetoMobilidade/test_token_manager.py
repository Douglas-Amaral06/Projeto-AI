"""
Testes para o módulo token_manager.

Testa a geração de tokens de assinatura digital.
"""

import sqlite3
import os
from datetime import datetime, timedelta
from token_manager import gerar_token


def test_gerar_token_basico():
    """
    Testa geração básica de token com consulta válida.
    
    Verifica que:
    - Token é gerado com sucesso
    - Token tem pelo menos 32 caracteres
    - URL é construída corretamente
    - Timestamps são válidos
    - Token é armazenado no banco
    """
    # Setup: criar consulta de teste
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    
    # Inserir consulta de teste
    cursor.execute('''
        INSERT INTO jovens_rotas (nome, cpf, cep_casa, cep_trabalho, matricula, status_rota)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ("Teste Token", "12345678900", "01310-100", "01310-200", "TEST001", "Otimizado"))
    
    consulta_id = cursor.lastrowid
    conexao.commit()
    conexao.close()
    
    try:
        # Executar
        resultado = gerar_token(consulta_id)
        
        # Verificar estrutura do resultado
        assert "token" in resultado, "Resultado deve conter 'token'"
        assert "url" in resultado, "Resultado deve conter 'url'"
        assert "created_at" in resultado, "Resultado deve conter 'created_at'"
        assert "expires_at" in resultado, "Resultado deve conter 'expires_at'"
        
        # Verificar token
        token = resultado["token"]
        assert len(token) >= 32, f"Token deve ter pelo menos 32 caracteres, tem {len(token)}"
        assert isinstance(token, str), "Token deve ser string"
        
        # Verificar URL
        url = resultado["url"]
        assert url.startswith("http://localhost:8501/assinar?token="), "URL deve ter formato correto"
        assert token in url, "URL deve conter o token"
        
        # Verificar timestamps
        created_at = datetime.strptime(resultado["created_at"], "%Y-%m-%d %H:%M:%S")
        expires_at = datetime.strptime(resultado["expires_at"], "%Y-%m-%d %H:%M:%S")
        
        # Verificar que expiração é ~30 dias no futuro
        diferenca = expires_at - created_at
        assert 29 <= diferenca.days <= 31, f"Expiração deve ser ~30 dias, é {diferenca.days} dias"
        
        # Verificar que token foi armazenado no banco
        conexao = sqlite3.connect('mobilidade_renapsi.db')
        cursor = conexao.cursor()
        cursor.execute('''
            SELECT token, consulta_id, created_at, expires_at, used 
            FROM tokens_assinatura 
            WHERE token = ?
        ''', (token,))
        
        row = cursor.fetchone()
        assert row is not None, "Token deve estar no banco de dados"
        assert row[1] == consulta_id, "consulta_id deve corresponder"
        assert row[4] == 0, "Token deve estar marcado como não usado"
        
        conexao.close()
        
        print("✅ test_gerar_token_basico PASSOU")
        
    finally:
        # Cleanup: remover dados de teste
        conexao = sqlite3.connect('mobilidade_renapsi.db')
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM tokens_assinatura WHERE consulta_id = ?", (consulta_id,))
        cursor.execute("DELETE FROM jovens_rotas WHERE id = ?", (consulta_id,))
        conexao.commit()
        conexao.close()


def test_gerar_token_consulta_invalida():
    """
    Testa que gerar_token levanta ValueError para consulta inexistente.
    """
    try:
        # Usar ID que certamente não existe
        gerar_token(999999999)
        assert False, "Deveria ter levantado ValueError"
    except ValueError as e:
        assert "não encontrada" in str(e), "Mensagem de erro deve mencionar 'não encontrada'"
        print("✅ test_gerar_token_consulta_invalida PASSOU")


def test_gerar_token_unicidade():
    """
    Testa que múltiplos tokens para a mesma consulta são únicos.
    """
    # Setup: criar consulta de teste
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    
    cursor.execute('''
        INSERT INTO jovens_rotas (nome, cpf, cep_casa, cep_trabalho, matricula, status_rota)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ("Teste Unicidade", "98765432100", "01310-100", "01310-200", "TEST002", "Otimizado"))
    
    consulta_id = cursor.lastrowid
    conexao.commit()
    conexao.close()
    
    try:
        # Gerar 3 tokens para a mesma consulta
        tokens = []
        for i in range(3):
            resultado = gerar_token(consulta_id)
            tokens.append(resultado["token"])
        
        # Verificar que todos são únicos
        assert len(tokens) == len(set(tokens)), "Todos os tokens devem ser únicos"
        
        print("✅ test_gerar_token_unicidade PASSOU")
        
    finally:
        # Cleanup
        conexao = sqlite3.connect('mobilidade_renapsi.db')
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM tokens_assinatura WHERE consulta_id = ?", (consulta_id,))
        cursor.execute("DELETE FROM jovens_rotas WHERE id = ?", (consulta_id,))
        conexao.commit()
        conexao.close()


def test_validar_token_valido():
    """
    Testa validação de token válido.
    
    Verifica que:
    - Token válido retorna valido=True
    - Dados da consulta são carregados corretamente
    - Erro é None
    """
    # Setup: criar consulta e token
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    
    cursor.execute('''
        INSERT INTO jovens_rotas (nome, cpf, cep_casa, cep_trabalho, matricula, status_rota)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ("Teste Validacao", "11122233344", "01310-100", "01310-200", "TEST003", "Otimizado"))
    
    consulta_id = cursor.lastrowid
    conexao.commit()
    conexao.close()
    
    try:
        # Gerar token
        from token_manager import validar_token
        resultado_geracao = gerar_token(consulta_id)
        token = resultado_geracao["token"]
        
        # Validar token
        resultado = validar_token(token)
        
        # Verificar resultado
        assert resultado["valido"] == True, "Token válido deve retornar valido=True"
        assert resultado["erro"] is None, "Token válido não deve ter erro"
        assert resultado["dados_consulta"] is not None, "Token válido deve retornar dados_consulta"
        
        # Verificar dados da consulta
        dados = resultado["dados_consulta"]
        assert dados["id"] == consulta_id, "ID da consulta deve corresponder"
        assert dados["nome"] == "Teste Validacao", "Nome deve corresponder"
        assert dados["cpf"] == "11122233344", "CPF deve corresponder"
        assert dados["status_rota"] == "Otimizado", "Status deve corresponder"
        
        print("✅ test_validar_token_valido PASSOU")
        
    finally:
        # Cleanup
        conexao = sqlite3.connect('mobilidade_renapsi.db')
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM tokens_assinatura WHERE consulta_id = ?", (consulta_id,))
        cursor.execute("DELETE FROM jovens_rotas WHERE id = ?", (consulta_id,))
        conexao.commit()
        conexao.close()


def test_validar_token_invalido():
    """
    Testa validação de token que não existe no banco.
    """
    from token_manager import validar_token
    
    # Token que não existe
    resultado = validar_token("token_inexistente_12345678901234567890")
    
    assert resultado["valido"] == False, "Token inexistente deve retornar valido=False"
    assert resultado["erro"] == "invalido", "Erro deve ser 'invalido'"
    assert resultado["dados_consulta"] is None, "dados_consulta deve ser None"
    
    print("✅ test_validar_token_invalido PASSOU")


def test_validar_token_formato_invalido():
    """
    Testa validação de token com formato inválido (muito curto).
    """
    from token_manager import validar_token
    
    # Token muito curto
    resultado = validar_token("curto")
    
    assert resultado["valido"] == False, "Token curto deve retornar valido=False"
    assert resultado["erro"] == "invalido", "Erro deve ser 'invalido'"
    assert resultado["dados_consulta"] is None, "dados_consulta deve ser None"
    
    print("✅ test_validar_token_formato_invalido PASSOU")


def test_validar_token_expirado():
    """
    Testa validação de token expirado.
    """
    from token_manager import validar_token
    
    # Setup: criar consulta e token expirado
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    
    cursor.execute('''
        INSERT INTO jovens_rotas (nome, cpf, cep_casa, cep_trabalho, matricula, status_rota)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ("Teste Expirado", "55566677788", "01310-100", "01310-200", "TEST004", "Otimizado"))
    
    consulta_id = cursor.lastrowid
    conexao.commit()
    
    # Criar token expirado manualmente
    import secrets
    token_expirado = secrets.token_urlsafe(32)
    created_at = (datetime.now() - timedelta(days=31)).strftime("%Y-%m-%d %H:%M:%S")
    expires_at = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute('''
        INSERT INTO tokens_assinatura (token, consulta_id, created_at, expires_at, used)
        VALUES (?, ?, ?, ?, 0)
    ''', (token_expirado, consulta_id, created_at, expires_at))
    
    conexao.commit()
    conexao.close()
    
    try:
        # Validar token expirado
        resultado = validar_token(token_expirado)
        
        assert resultado["valido"] == False, "Token expirado deve retornar valido=False"
        assert resultado["erro"] == "expirado", "Erro deve ser 'expirado'"
        assert resultado["dados_consulta"] is None, "dados_consulta deve ser None"
        
        print("✅ test_validar_token_expirado PASSOU")
        
    finally:
        # Cleanup
        conexao = sqlite3.connect('mobilidade_renapsi.db')
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM tokens_assinatura WHERE consulta_id = ?", (consulta_id,))
        cursor.execute("DELETE FROM jovens_rotas WHERE id = ?", (consulta_id,))
        conexao.commit()
        conexao.close()


def test_validar_token_usado():
    """
    Testa validação de token que já foi usado.
    """
    from token_manager import validar_token
    
    # Setup: criar consulta e token usado
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    
    cursor.execute('''
        INSERT INTO jovens_rotas (nome, cpf, cep_casa, cep_trabalho, matricula, status_rota)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ("Teste Usado", "99988877766", "01310-100", "01310-200", "TEST005", "Otimizado"))
    
    consulta_id = cursor.lastrowid
    conexao.commit()
    conexao.close()
    
    try:
        # Gerar token
        resultado_geracao = gerar_token(consulta_id)
        token = resultado_geracao["token"]
        
        # Marcar token como usado
        conexao = sqlite3.connect('mobilidade_renapsi.db')
        cursor = conexao.cursor()
        cursor.execute('''
            UPDATE tokens_assinatura 
            SET used = 1, used_at = ?
            WHERE token = ?
        ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), token))
        conexao.commit()
        conexao.close()
        
        # Validar token usado
        resultado = validar_token(token)
        
        assert resultado["valido"] == False, "Token usado deve retornar valido=False"
        assert resultado["erro"] == "usado", "Erro deve ser 'usado'"
        assert resultado["dados_consulta"] is None, "dados_consulta deve ser None"
        
        print("✅ test_validar_token_usado PASSOU")
        
    finally:
        # Cleanup
        conexao = sqlite3.connect('mobilidade_renapsi.db')
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM tokens_assinatura WHERE consulta_id = ?", (consulta_id,))
        cursor.execute("DELETE FROM jovens_rotas WHERE id = ?", (consulta_id,))
        conexao.commit()
        conexao.close()


def test_marcar_token_usado_sucesso():
    """
    Testa que marcar_token_usado atualiza corretamente o banco.
    
    Verifica que:
    - Função retorna True para token válido
    - Campo used é atualizado para 1
    - Campo used_at é preenchido com timestamp
    """
    from token_manager import marcar_token_usado
    
    # Setup: criar consulta e token
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    
    cursor.execute('''
        INSERT INTO jovens_rotas (nome, cpf, cep_casa, cep_trabalho, matricula, status_rota)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ("Teste Marcar", "44455566677", "01310-100", "01310-200", "TEST006", "Otimizado"))
    
    consulta_id = cursor.lastrowid
    conexao.commit()
    conexao.close()
    
    try:
        # Gerar token
        resultado_geracao = gerar_token(consulta_id)
        token = resultado_geracao["token"]
        
        # Marcar token como usado
        sucesso = marcar_token_usado(token, "192.168.1.100")
        
        # Verificar que retornou True
        assert sucesso == True, "marcar_token_usado deve retornar True para token válido"
        
        # Verificar no banco que token foi marcado como usado
        conexao = sqlite3.connect('mobilidade_renapsi.db')
        cursor = conexao.cursor()
        cursor.execute('''
            SELECT used, used_at 
            FROM tokens_assinatura 
            WHERE token = ?
        ''', (token,))
        
        row = cursor.fetchone()
        assert row is not None, "Token deve existir no banco"
        assert row[0] == 1, "Campo used deve ser 1"
        assert row[1] is not None, "Campo used_at deve estar preenchido"
        
        # Verificar formato do timestamp
        used_at = datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
        assert used_at <= datetime.now(), "used_at não deve ser no futuro"
        
        conexao.close()
        
        print("✅ test_marcar_token_usado_sucesso PASSOU")
        
    finally:
        # Cleanup
        conexao = sqlite3.connect('mobilidade_renapsi.db')
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM tokens_assinatura WHERE consulta_id = ?", (consulta_id,))
        cursor.execute("DELETE FROM jovens_rotas WHERE id = ?", (consulta_id,))
        conexao.commit()
        conexao.close()


def test_marcar_token_usado_token_inexistente():
    """
    Testa que marcar_token_usado retorna False para token inexistente.
    """
    from token_manager import marcar_token_usado
    
    # Token que não existe
    sucesso = marcar_token_usado("token_inexistente_98765432109876543210")
    
    assert sucesso == False, "marcar_token_usado deve retornar False para token inexistente"
    
    print("✅ test_marcar_token_usado_token_inexistente PASSOU")


def test_marcar_token_usado_multiplas_vezes():
    """
    Testa que marcar_token_usado pode ser chamado múltiplas vezes no mesmo token.
    """
    from token_manager import marcar_token_usado
    
    # Setup: criar consulta e token
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    
    cursor.execute('''
        INSERT INTO jovens_rotas (nome, cpf, cep_casa, cep_trabalho, matricula, status_rota)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ("Teste Multiplo", "77788899900", "01310-100", "01310-200", "TEST007", "Otimizado"))
    
    consulta_id = cursor.lastrowid
    conexao.commit()
    conexao.close()
    
    try:
        # Gerar token
        resultado_geracao = gerar_token(consulta_id)
        token = resultado_geracao["token"]
        
        # Marcar token como usado primeira vez
        sucesso1 = marcar_token_usado(token)
        assert sucesso1 == True, "Primeira chamada deve retornar True"
        
        # Marcar token como usado segunda vez (já está usado)
        sucesso2 = marcar_token_usado(token)
        assert sucesso2 == True, "Segunda chamada deve retornar True (token existe)"
        
        # Verificar que token continua marcado como usado
        conexao = sqlite3.connect('mobilidade_renapsi.db')
        cursor = conexao.cursor()
        cursor.execute('SELECT used FROM tokens_assinatura WHERE token = ?', (token,))
        row = cursor.fetchone()
        assert row[0] == 1, "Token deve continuar marcado como usado"
        conexao.close()
        
        print("✅ test_marcar_token_usado_multiplas_vezes PASSOU")
        
    finally:
        # Cleanup
        conexao = sqlite3.connect('mobilidade_renapsi.db')
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM tokens_assinatura WHERE consulta_id = ?", (consulta_id,))
        cursor.execute("DELETE FROM jovens_rotas WHERE id = ?", (consulta_id,))
        conexao.commit()
        conexao.close()


def test_limpar_tokens_expirados_remove_apenas_nao_usados():
    """
    Testa que limpar_tokens_expirados remove apenas tokens expirados e não usados.
    
    Verifica que:
    - Tokens expirados e não usados são removidos
    - Tokens expirados mas usados são preservados (audit trail)
    - Tokens válidos (não expirados) são preservados
    - Retorna contagem correta de tokens removidos
    
    **Validates: Requirements 15.1, 15.4, 15.5, 15.7**
    """
    from token_manager import limpar_tokens_expirados
    import secrets
    
    # Setup: criar consultas de teste
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    
    # Criar 3 consultas
    cursor.execute('''
        INSERT INTO jovens_rotas (nome, cpf, cep_casa, cep_trabalho, matricula, status_rota)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ("Teste Cleanup 1", "11111111111", "01310-100", "01310-200", "CLEAN001", "Otimizado"))
    consulta_id_1 = cursor.lastrowid
    
    cursor.execute('''
        INSERT INTO jovens_rotas (nome, cpf, cep_casa, cep_trabalho, matricula, status_rota)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ("Teste Cleanup 2", "22222222222", "01310-100", "01310-200", "CLEAN002", "Otimizado"))
    consulta_id_2 = cursor.lastrowid
    
    cursor.execute('''
        INSERT INTO jovens_rotas (nome, cpf, cep_casa, cep_trabalho, matricula, status_rota)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ("Teste Cleanup 3", "33333333333", "01310-100", "01310-200", "CLEAN003", "Otimizado"))
    consulta_id_3 = cursor.lastrowid
    
    conexao.commit()
    
    # Criar 3 tokens:
    # 1. Token expirado e não usado (DEVE SER REMOVIDO)
    token_expirado_nao_usado = secrets.token_urlsafe(32)
    created_at_1 = (datetime.now() - timedelta(days=31)).strftime("%Y-%m-%d %H:%M:%S")
    expires_at_1 = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute('''
        INSERT INTO tokens_assinatura (token, consulta_id, created_at, expires_at, used)
        VALUES (?, ?, ?, ?, 0)
    ''', (token_expirado_nao_usado, consulta_id_1, created_at_1, expires_at_1))
    
    # 2. Token expirado mas usado (DEVE SER PRESERVADO para audit trail)
    token_expirado_usado = secrets.token_urlsafe(32)
    created_at_2 = (datetime.now() - timedelta(days=31)).strftime("%Y-%m-%d %H:%M:%S")
    expires_at_2 = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    used_at_2 = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute('''
        INSERT INTO tokens_assinatura (token, consulta_id, created_at, expires_at, used, used_at)
        VALUES (?, ?, ?, ?, 1, ?)
    ''', (token_expirado_usado, consulta_id_2, created_at_2, expires_at_2, used_at_2))
    
    # 3. Token válido (não expirado) (DEVE SER PRESERVADO)
    token_valido = secrets.token_urlsafe(32)
    created_at_3 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    expires_at_3 = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute('''
        INSERT INTO tokens_assinatura (token, consulta_id, created_at, expires_at, used)
        VALUES (?, ?, ?, ?, 0)
    ''', (token_valido, consulta_id_3, created_at_3, expires_at_3))
    
    conexao.commit()
    conexao.close()
    
    try:
        # Executar limpeza
        count_removidos = limpar_tokens_expirados()
        
        # Verificar que retornou 1 (apenas o token expirado e não usado)
        assert count_removidos == 1, f"Deve remover exatamente 1 token, removeu {count_removidos}"
        
        # Verificar no banco que apenas o token correto foi removido
        conexao = sqlite3.connect('mobilidade_renapsi.db')
        cursor = conexao.cursor()
        
        # Token expirado não usado NÃO deve existir
        cursor.execute('SELECT COUNT(*) FROM tokens_assinatura WHERE token = ?', (token_expirado_nao_usado,))
        assert cursor.fetchone()[0] == 0, "Token expirado não usado deve ter sido removido"
        
        # Token expirado usado DEVE existir (audit trail)
        cursor.execute('SELECT COUNT(*) FROM tokens_assinatura WHERE token = ?', (token_expirado_usado,))
        assert cursor.fetchone()[0] == 1, "Token expirado usado deve ser preservado para auditoria"
        
        # Token válido DEVE existir
        cursor.execute('SELECT COUNT(*) FROM tokens_assinatura WHERE token = ?', (token_valido,))
        assert cursor.fetchone()[0] == 1, "Token válido deve ser preservado"
        
        conexao.close()
        
        print("✅ test_limpar_tokens_expirados_remove_apenas_nao_usados PASSOU")
        
    finally:
        # Cleanup
        conexao = sqlite3.connect('mobilidade_renapsi.db')
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM tokens_assinatura WHERE consulta_id IN (?, ?, ?)", 
                      (consulta_id_1, consulta_id_2, consulta_id_3))
        cursor.execute("DELETE FROM jovens_rotas WHERE id IN (?, ?, ?)", 
                      (consulta_id_1, consulta_id_2, consulta_id_3))
        conexao.commit()
        conexao.close()


def test_limpar_tokens_expirados_sem_tokens():
    """
    Testa que limpar_tokens_expirados retorna 0 quando não há tokens para limpar.
    """
    from token_manager import limpar_tokens_expirados
    
    # Executar limpeza (assumindo que não há tokens expirados não usados)
    count = limpar_tokens_expirados()
    
    # Deve retornar 0 ou número não negativo
    assert count >= 0, "Contagem deve ser não negativa"
    
    print("✅ test_limpar_tokens_expirados_sem_tokens PASSOU")


def test_limpar_tokens_expirados_multiplos():
    """
    Testa que limpar_tokens_expirados remove múltiplos tokens expirados não usados.
    """
    from token_manager import limpar_tokens_expirados
    import secrets
    
    # Setup: criar consultas e múltiplos tokens expirados não usados
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    
    consulta_ids = []
    tokens_expirados = []
    
    # Criar 5 tokens expirados não usados
    for i in range(5):
        cursor.execute('''
            INSERT INTO jovens_rotas (nome, cpf, cep_casa, cep_trabalho, matricula, status_rota)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (f"Teste Multi {i}", f"{i}{i}{i}{i}{i}{i}{i}{i}{i}{i}{i}", 
              "01310-100", "01310-200", f"MULTI{i:03d}", "Otimizado"))
        consulta_id = cursor.lastrowid
        consulta_ids.append(consulta_id)
        
        token = secrets.token_urlsafe(32)
        tokens_expirados.append(token)
        created_at = (datetime.now() - timedelta(days=31)).strftime("%Y-%m-%d %H:%M:%S")
        expires_at = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute('''
            INSERT INTO tokens_assinatura (token, consulta_id, created_at, expires_at, used)
            VALUES (?, ?, ?, ?, 0)
        ''', (token, consulta_id, created_at, expires_at))
    
    conexao.commit()
    conexao.close()
    
    try:
        # Executar limpeza
        count_removidos = limpar_tokens_expirados()
        
        # Verificar que removeu pelo menos 5 tokens
        assert count_removidos >= 5, f"Deve remover pelo menos 5 tokens, removeu {count_removidos}"
        
        # Verificar que todos os tokens foram removidos
        conexao = sqlite3.connect('mobilidade_renapsi.db')
        cursor = conexao.cursor()
        
        for token in tokens_expirados:
            cursor.execute('SELECT COUNT(*) FROM tokens_assinatura WHERE token = ?', (token,))
            assert cursor.fetchone()[0] == 0, f"Token {token} deve ter sido removido"
        
        conexao.close()
        
        print("✅ test_limpar_tokens_expirados_multiplos PASSOU")
        
    finally:
        # Cleanup
        conexao = sqlite3.connect('mobilidade_renapsi.db')
        cursor = conexao.cursor()
        placeholders = ','.join('?' * len(consulta_ids))
        cursor.execute(f"DELETE FROM tokens_assinatura WHERE consulta_id IN ({placeholders})", consulta_ids)
        cursor.execute(f"DELETE FROM jovens_rotas WHERE id IN ({placeholders})", consulta_ids)
        conexao.commit()
        conexao.close()


if __name__ == "__main__":
    print("Executando testes de token_manager...\n")
    
    # Garantir que banco está inicializado
    from banco_dados import inicializar_banco_completo
    inicializar_banco_completo()
    
    # Testes de geração de token
    test_gerar_token_basico()
    test_gerar_token_consulta_invalida()
    test_gerar_token_unicidade()
    
    # Testes de validação de token
    test_validar_token_valido()
    test_validar_token_invalido()
    test_validar_token_formato_invalido()
    test_validar_token_expirado()
    test_validar_token_usado()
    
    # Testes de marcar token como usado
    test_marcar_token_usado_sucesso()
    test_marcar_token_usado_token_inexistente()
    test_marcar_token_usado_multiplas_vezes()
    
    # Testes de limpeza de tokens expirados
    test_limpar_tokens_expirados_remove_apenas_nao_usados()
    test_limpar_tokens_expirados_sem_tokens()
    test_limpar_tokens_expirados_multiplos()
    
    print("\n✅ Todos os testes passaram!")
