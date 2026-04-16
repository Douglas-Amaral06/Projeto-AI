#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Teste para verificar se as coordenadas do mapa estão corretas
"""

from apis import buscar_endereco_viacep, motor_de_rotas_gratuito

# Testa com 2 CEPs reais de São Paulo
cep_casa = '01310100'  # Av. Paulista
cep_trab = '01046000'  # Centro (Praça da Sé)

print('='*60)
print('TESTANDO FLUXO COMPLETO DE COORDENADAS')
print('='*60)
print()

# Busca endereços
print('1. Buscando endereços via ViaCEP...')
end_casa = buscar_endereco_viacep(cep_casa)
end_trab = buscar_endereco_viacep(cep_trab)

print(f'   Casa: {end_casa.get("completo")}')
print(f'   Trabalho: {end_trab.get("completo")}')
print()

# Calcula rota
print('2. Calculando rota e obtendo coordenadas...')
rota = motor_de_rotas_gratuito(
    end_casa.get('completo'),
    end_trab.get('completo')
)

print()
print('='*60)
print('RESULTADO FINAL:')
print('='*60)
print(f'Distância: {rota["distancia_km"]:.2f} km')
print(f'Coordenadas Casa (C): LAT={rota["coords_reais"][0][0]}, LON={rota["coords_reais"][0][1]}')
print(f'Coordenadas Trabalho (T): LAT={rota["coords_reais"][1][0]}, LON={rota["coords_reais"][1][1]}')
print()

# Valida se as coordenadas estão em São Paulo
lat_c, lon_c = rota["coords_reais"][0]
lat_t, lon_t = rota["coords_reais"][1]

# São Paulo está aproximadamente entre:
# Latitude: -24.0 a -23.3
# Longitude: -46.9 a -46.3

if -24.0 <= lat_c <= -23.3 and -46.9 <= lon_c <= -46.3:
    print('✅ Coordenadas da CASA estão dentro de São Paulo')
else:
    print('❌ ERRO: Coordenadas da CASA estão FORA de São Paulo!')
    
if -24.0 <= lat_t <= -23.3 and -46.9 <= lon_t <= -46.3:
    print('✅ Coordenadas do TRABALHO estão dentro de São Paulo')
else:
    print('❌ ERRO: Coordenadas do TRABALHO estão FORA de São Paulo!')

print()
print('='*60)
print('✅ TESTE COMPLETO!')
print('='*60)
