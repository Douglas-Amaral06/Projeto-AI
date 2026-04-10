@echo off
REM Script para extrair apenas São Paulo do arquivo do Sudeste
REM Bounding box de São Paulo: -46.8,-24.0,-46.3,-23.3

echo Verificando se osmium está instalado...
where osmium >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERRO: osmium não está instalado.
    echo.
    echo Instale o osmium-tool:
    echo 1. Baixe de: https://osmcode.org/osmium-tool/
    echo 2. Ou use: winget install osmium-tool
    echo.
    pause
    exit /b 1
)

echo Extraindo região de São Paulo...
cd saopaulo
osmium extract -b -46.8,-24.0,-46.3,-23.3 sao-paulo.osm.pbf -o sao-paulo-city.osm.pbf

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Extração concluída com sucesso!
    echo Arquivo gerado: sao-paulo-city.osm.pbf
    echo.
    echo Renomeando arquivos...
    ren sao-paulo.osm.pbf sao-paulo-sudeste-backup.osm.pbf
    ren sao-paulo-city.osm.pbf sao-paulo.osm.pbf
    echo.
    echo Pronto! Agora você pode executar o build do OTP.
) else (
    echo.
    echo ERRO na extração!
)

pause
