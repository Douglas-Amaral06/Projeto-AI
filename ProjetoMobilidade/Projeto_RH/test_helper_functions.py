import os
"""
Test for helper functions: obter_status_consulta and verificar_token_usado.

These tests verify that the helper functions correctly retrieve status
and check token usage from the database.
"""
import sqlite3
import sys
from banco_dados import (
    obter_status_consulta,
    verificar_token_usado,
    inicializar_banco_completo
)


def setup_test_data():
    """Create test data in the database."""
    from datetime import datetime, timedelta
    import random
    
    inicializar_banco_completo()
    
    conexao = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'mobilidade_renapsi.db'))
    cursor = conexao.cursor()
    
    # Generate unique identifiers to avoid conflicts
    unique_id = random.randint(100000, 999999)
    
    # Create a test consulta
    cursor.execute('''
        INSERT INTO jovens_rotas (nome, cpf, cep_casa, cep_trabalho, matricula, status_rota)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (f'Helper Test User {unique_id}', f'{unique_id}', '01000-000', '02000-000', f'HELP{unique_id}', 'Otimizado'))
    
    consulta_id = cursor.lastrowid
    
    # Create test tokens with unique names
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    expires_at = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    
    # Token not used
    cursor.execute('''
        INSERT INTO tokens_assinatura (token, consulta_id, created_at, expires_at, used)
        VALUES (?, ?, ?, ?, ?)
    ''', (f'test_token_unused_{unique_id}', consulta_id, created_at, expires_at, 0))
    
    # Token used
    cursor.execute('''
        INSERT INTO tokens_assinatura (token, consulta_id, created_at, expires_at, used, used_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (f'test_token_used_{unique_id}', consulta_id, created_at, expires_at, 1, created_at))
    
    conexao.commit()
    conexao.close()
    
    return consulta_id, unique_id


def test_obter_status_consulta_existente():
    """Test obter_status_consulta with existing consulta."""
    print("=" * 60)
    print("Testing obter_status_consulta with existing consulta")
    print("=" * 60)
    
    consulta_id, _ = setup_test_data()
    print(f"\n✓ Created test consulta with ID: {consulta_id}")
    
    # Test getting status
    print(f"\n→ Calling obter_status_consulta({consulta_id})")
    status = obter_status_consulta(consulta_id)
    
    print(f"  - Returned status: {status}")
    
    if status != 'Otimizado':
        print(f"\n❌ FAILED: Expected 'Otimizado', got '{status}'")
        return False
    
    print("\n✅ SUCCESS: Correctly retrieved status 'Otimizado'")
    print("=" * 60)
    return True


def test_obter_status_consulta_inexistente():
    """Test obter_status_consulta with nonexistent consulta."""
    print("\n" + "=" * 60)
    print("Testing obter_status_consulta with nonexistent consulta")
    print("=" * 60)
    
    nonexistent_id = 999999
    print(f"\n→ Calling obter_status_consulta({nonexistent_id})")
    status = obter_status_consulta(nonexistent_id)
    
    print(f"  - Returned status: {status}")
    
    if status is not None:
        print(f"\n❌ FAILED: Expected None, got '{status}'")
        return False
    
    print("\n✅ SUCCESS: Correctly returned None for nonexistent consulta")
    print("=" * 60)
    return True


def test_verificar_token_usado_nao_usado():
    """Test verificar_token_usado with unused token."""
    print("\n" + "=" * 60)
    print("Testing verificar_token_usado with unused token")
    print("=" * 60)
    
    consulta_id, unique_id = setup_test_data()
    
    token = f'test_token_unused_{unique_id}'
    print(f"\n→ Calling verificar_token_usado('{token}')")
    usado = verificar_token_usado(token)
    
    print(f"  - Returned: {usado}")
    
    if usado:
        print(f"\n❌ FAILED: Expected False (not used), got {usado}")
        return False
    
    print("\n✅ SUCCESS: Correctly returned False for unused token")
    print("=" * 60)
    return True


def test_verificar_token_usado_usado():
    """Test verificar_token_usado with used token."""
    print("\n" + "=" * 60)
    print("Testing verificar_token_usado with used token")
    print("=" * 60)
    
    consulta_id, unique_id = setup_test_data()
    
    token = f'test_token_used_{unique_id}'
    print(f"\n→ Calling verificar_token_usado('{token}')")
    usado = verificar_token_usado(token)
    
    print(f"  - Returned: {usado}")
    
    if not usado:
        print(f"\n❌ FAILED: Expected True (used), got {usado}")
        return False
    
    print("\n✅ SUCCESS: Correctly returned True for used token")
    print("=" * 60)
    return True


def test_verificar_token_usado_inexistente():
    """Test verificar_token_usado with nonexistent token."""
    print("\n" + "=" * 60)
    print("Testing verificar_token_usado with nonexistent token")
    print("=" * 60)
    
    token = 'nonexistent_token_xyz'
    print(f"\n→ Calling verificar_token_usado('{token}')")
    usado = verificar_token_usado(token)
    
    print(f"  - Returned: {usado}")
    
    if usado:
        print(f"\n❌ FAILED: Expected False for nonexistent token, got {usado}")
        return False
    
    print("\n✅ SUCCESS: Correctly returned False for nonexistent token")
    print("=" * 60)
    return True


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("RUNNING TESTS FOR HELPER FUNCTIONS")
    print("=" * 60)
    
    tests = [
        ("obter_status_consulta - existing", test_obter_status_consulta_existente),
        ("obter_status_consulta - nonexistent", test_obter_status_consulta_inexistente),
        ("verificar_token_usado - unused", test_verificar_token_usado_nao_usado),
        ("verificar_token_usado - used", test_verificar_token_usado_usado),
        ("verificar_token_usado - nonexistent", test_verificar_token_usado_inexistente),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ EXCEPTION in {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 60)
    
    sys.exit(0 if passed == total else 1)

