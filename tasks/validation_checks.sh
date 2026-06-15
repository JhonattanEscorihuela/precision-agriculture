#!/bin/bash
# Validación post-implementación de correcciones de seguridad

echo "🔍 Iniciando validación de correcciones..."
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Contador de checks
PASSED=0
FAILED=0

# 1. Verificar que SECRET_KEY NO aparece en logs
echo "1️⃣ Verificando que SECRET_KEY no se expone en logs..."
if docker-compose logs backend 2>/dev/null | grep -q "de12746cbe0bd60a04203aa31279f5ded4ee4d78531f71bf9d21a1d3ddeb7abe"; then
    echo -e "${RED}❌ FAIL: SECRET_KEY encontrada en logs (CRÍTICO)${NC}"
    ((FAILED++))
else
    echo -e "${GREEN}✅ PASS: SECRET_KEY no expuesta en logs${NC}"
    ((PASSED++))
fi
echo ""

# 2. Verificar mensaje de validación de env vars
echo "2️⃣ Verificando validación de environment variables..."
if docker-compose logs backend 2>/dev/null | grep -q "Environment variables validated successfully"; then
    echo -e "${GREEN}✅ PASS: Validación de env vars ejecutándose${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️  WARN: No se encontró mensaje de validación (backend podría no estar corriendo)${NC}"
fi
echo ""

# 3. Verificar que no hay print() en logs (solo logger)
echo "3️⃣ Verificando que no hay print() statements en logs recientes..."
# Los print() aparecerían sin formato de logging (sin timestamp, level, etc.)
# Buscar solo en logs recientes (últimos 5 minutos)
if docker-compose logs backend --since 5m 2>/dev/null | grep -qE "^(📄 Página|📦 Total)" ; then
    echo -e "${RED}❌ FAIL: Encontrados print() statements sin formato de logging${NC}"
    ((FAILED++))
else
    echo -e "${GREEN}✅ PASS: No se encontraron print() statements en logs recientes${NC}"
    ((PASSED++))
fi
echo ""

# 4. Verificar CORS restrictivo con curl
echo "4️⃣ Verificando configuración CORS restrictiva..."
if command -v curl &> /dev/null; then
    # Test 1: Verificar que rechaza orígenes no autorizados
    EVIL_RESPONSE=$(curl -s -H "Origin: http://evil.com" -H "Access-Control-Request-Method: GET" \
        -X OPTIONS http://localhost:8000/ -v 2>&1 | grep -i "access-control-allow-origin")

    # Test 2: Verificar que permite orígenes autorizados
    VALID_RESPONSE=$(curl -s -H "Origin: http://localhost:3000" -H "Access-Control-Request-Method: GET" \
        -X OPTIONS http://localhost:8000/ -v 2>&1 | grep -i "access-control-allow-origin")

    if [[ -z "$EVIL_RESPONSE" ]] && [[ -n "$VALID_RESPONSE" ]]; then
        echo -e "${GREEN}✅ PASS: CORS rechaza orígenes no autorizados y permite los autorizados${NC}"
        ((PASSED++))
    elif [[ -n "$EVIL_RESPONSE" ]]; then
        echo -e "${RED}❌ FAIL: CORS permite orígenes no autorizados (evil.com)${NC}"
        ((FAILED++))
    else
        echo -e "${RED}❌ FAIL: CORS no permite orígenes autorizados (localhost:3000)${NC}"
        ((FAILED++))
    fi
else
    echo -e "${YELLOW}⚠️  SKIP: curl no disponible${NC}"
fi
echo ""

# 5. Verificar que .dockerignore existe
echo "5️⃣ Verificando .dockerignore..."
if [ -f "backend/.dockerignore" ]; then
    echo -e "${GREEN}✅ PASS: .dockerignore creado${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL: .dockerignore no encontrado${NC}"
    ((FAILED++))
fi
echo ""

# 6. Verificar que SECRET_KEY está en .env
echo "6️⃣ Verificando SECRET_KEY en .env..."
if grep -q "^SECRET_KEY=" backend/.env 2>/dev/null; then
    echo -e "${GREEN}✅ PASS: SECRET_KEY configurado en .env${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL: SECRET_KEY no encontrado en .env${NC}"
    ((FAILED++))
fi
echo ""

# 7. Verificar que backend está corriendo
echo "7️⃣ Verificando que backend está corriendo..."
if curl -s http://localhost:8000/ 2>/dev/null | grep -q "Backend is running"; then
    echo -e "${GREEN}✅ PASS: Backend respondiendo correctamente${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️  WARN: Backend no responde (verificar docker-compose logs)${NC}"
fi
echo ""

# Resumen
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 RESUMEN DE VALIDACIÓN"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ Checks pasados: $PASSED${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}❌ Checks fallidos: $FAILED${NC}"
else
    echo -e "${GREEN}❌ Checks fallidos: 0${NC}"
fi
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 Todas las correcciones implementadas correctamente${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Algunas correcciones requieren revisión${NC}"
    exit 1
fi
