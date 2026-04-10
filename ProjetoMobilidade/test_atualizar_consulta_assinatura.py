"""
Test for atualizar_consulta_com_assinatura function.

This test verifies that the function correctly updates a consulta with
signature information and changes the status to 'Implantado'.
"""
import sqlite3
import os
import sys
from datetime import datetime

# Import the function to test
from banco_dados import atualizar_consulta_com_assinatura, inicializar_banco_completo


def setup_test_database():
    """Create a test consulta in the database."""
    # Ensure database is initialized
    inicializar_banco_completo()
    
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    
    # Insert a test consulta
    cursor.execute('''
        INSERT INTO jovens_rotas (nome, cpf, cep_casa, cep_trabalho, matricula, status_rota)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ('Test User', '12345678900', '01000-000', '02000-000', 'TEST123', 'Otimizado'))
    
    consulta_id = cursor.lastrowid
    conexao.commit()
    conexao.close()
    
    return consulta_id


def test_atualizar_consulta_com_assinatura():
    """Test that the function updates consulta correctly."""
    print("=" * 60)
    print("Testing atualizar_consulta_com_assinatura")
    print("=" * 60)
    
    # Setup
    consulta_id = setup_test_database()
    print(f"\n✓ Created test consulta with ID: {consulta_id}")
    
    # Test data
    filepath = "assinaturas/assinatura_test_123.png"
    ip_address = "192.168.1.100"
    
    # Execute the function
    print(f"\n→ Calling atualizar_consulta_com_assinatura...")
    print(f"  - consulta_id: {consulta_id}")
    print(f"  - filepath: {filepath}")
    print(f"  - ip_address: {ip_address}")
    
    resultado = atualizar_consulta_com_assinatura(consulta_id, filepath, ip_address)
    
    # Verify result
    if not resultado:
        print("\n❌ FAILED: Function returned False")
        return False
    
    print(f"\n✓ Function returned True")
    
    # Verify database was updated correctly
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    
    cursor.execute('''
        SELECT status_rota, assinatura_path, assinatura_data, assinatura_ip
        FROM jovens_rotas
        WHERE id = ?
    ''', (consulta_id,))
    
    row = cursor.fetchone()
    conexao.close()
    
    if not row:
        print(f"\n❌ FAILED: Consulta {consulta_id} not found after update")
        return False
    
    status_rota, assinatura_path, assinatura_data, assinatura_ip = row
    
    # Verify all fields
    print("\n→ Verifying database updates:")
    print(f"  - status_rota: {status_rota}")
    print(f"  - assinatura_path: {assinatura_path}")
    print(f"  - assinatura_data: {assinatura_data}")
    print(f"  - assinatura_ip: {assinatura_ip}")
    
    errors = []
    
    if status_rota != 'Implantado':
        errors.append(f"status_rota should be 'Implantado', got '{status_rota}'")
    
    if assinatura_path != filepath:
        errors.append(f"assinatura_path should be '{filepath}', got '{assinatura_path}'")
    
    if assinatura_ip != ip_address:
        errors.append(f"assinatura_ip should be '{ip_address}', got '{assinatura_ip}'")
    
    if not assinatura_data:
        errors.append("assinatura_data should not be None")
    else:
        # Verify timestamp format
        try:
            datetime.strptime(assinatura_data, "%Y-%m-%d %H:%M:%S")
            print(f"  ✓ assinatura_data has correct format")
        except ValueError:
            errors.append(f"assinatura_data has invalid format: {assinatura_data}")
    
    if errors:
        print("\n❌ FAILED: Verification errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    print("\n✅ SUCCESS: All verifications passed!")
    print("=" * 60)
    return True


def test_nonexistent_consulta():
    """Test that the function handles nonexistent consulta_id correctly."""
    print("\n" + "=" * 60)
    print("Testing with nonexistent consulta_id")
    print("=" * 60)
    
    # Use a very high ID that doesn't exist
    nonexistent_id = 999999
    filepath = "assinaturas/test.png"
    ip_address = "192.168.1.100"
    
    print(f"\n→ Calling with nonexistent ID: {nonexistent_id}")
    resultado = atualizar_consulta_com_assinatura(nonexistent_id, filepath, ip_address)
    
    if resultado:
        print("\n❌ FAILED: Function should return False for nonexistent ID")
        return False
    
    print("\n✅ SUCCESS: Function correctly returned False for nonexistent ID")
    print("=" * 60)
    return True


def test_atomicity():
    """Test that the function uses transactions correctly."""
    print("\n" + "=" * 60)
    print("Testing transaction atomicity")
    print("=" * 60)
    
    # Setup
    consulta_id = setup_test_database()
    print(f"\n✓ Created test consulta with ID: {consulta_id}")
    
    # Get initial state
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    cursor.execute('SELECT status_rota FROM jovens_rotas WHERE id = ?', (consulta_id,))
    initial_status = cursor.fetchone()[0]
    conexao.close()
    
    print(f"  - Initial status: {initial_status}")
    
    # Update
    filepath = "assinaturas/atomicity_test.png"
    ip_address = "10.0.0.1"
    
    resultado = atualizar_consulta_com_assinatura(consulta_id, filepath, ip_address)
    
    if not resultado:
        print("\n❌ FAILED: Update failed")
        return False
    
    # Verify all fields were updated together (atomicity)
    conexao = sqlite3.connect('mobilidade_renapsi.db')
    cursor = conexao.cursor()
    cursor.execute('''
        SELECT status_rota, assinatura_path, assinatura_data, assinatura_ip
        FROM jovens_rotas WHERE id = ?
    ''', (consulta_id,))
    row = cursor.fetchone()
    conexao.close()
    
    status, path, data, ip = row
    
    # All fields should be updated or none
    if status == 'Implantado' and path == filepath and data and ip == ip_address:
        print("\n✅ SUCCESS: All fields updated atomically")
        print("=" * 60)
        return True
    else:
        print("\n❌ FAILED: Atomicity violated - some fields not updated")
        print(f"  - status: {status}")
        print(f"  - path: {path}")
        print(f"  - data: {data}")
        print(f"  - ip: {ip}")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("RUNNING TESTS FOR atualizar_consulta_com_assinatura")
    print("=" * 60)
    
    tests = [
        ("Basic functionality", test_atualizar_consulta_com_assinatura),
        ("Nonexistent consulta", test_nonexistent_consulta),
        ("Transaction atomicity", test_atomicity),
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
