#!/bin/bash
# OE5 - Test E2E del flujo completo de usuario
# Simula: Login → Crear parcela → Adquirir → NDVI → Segmentación → Textura

set -e  # Exit on error

BASE_URL="http://localhost:8000"
EMAIL="test-e2e@example.com"
PASSWORD="testpassword123"

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== OE5 E2E Workflow Test ===${NC}\n"

# Limpiar cookies previas
rm -f /tmp/e2e-cookies.txt

echo -e "${YELLOW}[1/8] Registrar usuario...${NC}"
REGISTER_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\",\"full_name\":\"Test E2E User\"}")

REGISTER_STATUS=$(echo "$REGISTER_RESPONSE" | tail -n1)
REGISTER_BODY=$(echo "$REGISTER_RESPONSE" | head -n1)

if [[ "$REGISTER_STATUS" == "201" ]] || [[ "$REGISTER_STATUS" == "400" ]]; then
  # 400 significa que el usuario ya existe (esperado en re-runs)
  echo -e "${GREEN}✅ Usuario registrado o ya existe${NC}"
else
  echo -e "${RED}❌ Error registrando usuario: HTTP $REGISTER_STATUS${NC}"
  echo "$REGISTER_BODY"
  exit 1
fi

echo -e "\n${YELLOW}[2/8] Login...${NC}"
LOGIN_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")

LOGIN_STATUS=$(echo "$LOGIN_RESPONSE" | tail -n1)
LOGIN_BODY=$(echo "$LOGIN_RESPONSE" | head -n1)

if [[ "$LOGIN_STATUS" == "200" ]]; then
  TOKEN=$(echo "$LOGIN_BODY" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
  echo -e "${GREEN}✅ Login exitoso${NC}"
  echo "Token: ${TOKEN:0:20}..."
else
  echo -e "${RED}❌ Error en login: HTTP $LOGIN_STATUS${NC}"
  echo "$LOGIN_BODY"
  exit 1
fi

echo -e "\n${YELLOW}[3/8] Crear parcela (Parcela 211 SRRG)...${NC}"
POLYGON_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/polygons/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test E2E - Parcela 211",
    "coordinates": [
      [-67.528058, 8.8441233],
      [-67.5153475, 8.8386166],
      [-67.5103962, 8.8478932],
      [-67.522828, 8.8534209],
      [-67.528058, 8.8441233]
    ]
  }')

POLYGON_STATUS=$(echo "$POLYGON_RESPONSE" | tail -n1)
POLYGON_BODY=$(echo "$POLYGON_RESPONSE" | head -n1)

if [[ "$POLYGON_STATUS" == "201" ]]; then
  POLYGON_ID=$(echo "$POLYGON_BODY" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
  echo -e "${GREEN}✅ Parcela creada: ID=$POLYGON_ID${NC}"
else
  echo -e "${RED}❌ Error creando parcela: HTTP $POLYGON_STATUS${NC}"
  echo "$POLYGON_BODY"
  exit 1
fi

echo -e "\n${YELLOW}[4/8] Obtener fechas disponibles (STAC)...${NC}"
DATES_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET \
  "$BASE_URL/api/sentinel/available-dates/$POLYGON_ID?start_date=2025-01-01&end_date=2025-06-30&max_cloud=20" \
  -H "Authorization: Bearer $TOKEN")

DATES_STATUS=$(echo "$DATES_RESPONSE" | tail -n1)
DATES_BODY=$(echo "$DATES_RESPONSE" | head -n1)

if [[ "$DATES_STATUS" == "200" ]]; then
  DATES_COUNT=$(echo "$DATES_BODY" | grep -o '"date"' | wc -l)
  echo -e "${GREEN}✅ Fechas obtenidas: $DATES_COUNT disponibles${NC}"

  if [[ $DATES_COUNT -eq 0 ]]; then
    echo -e "${RED}⚠️  No hay fechas disponibles. Verificar conectividad Copernicus.${NC}"
    exit 1
  fi

  # Extraer primera fecha
  ACQUISITION_DATE=$(echo "$DATES_BODY" | grep -o '"date":"[^"]*' | head -1 | cut -d'"' -f4)
  echo "Fecha seleccionada: $ACQUISITION_DATE"
else
  echo -e "${RED}❌ Error obteniendo fechas: HTTP $DATES_STATUS${NC}"
  echo "$DATES_BODY"
  exit 1
fi

echo -e "\n${YELLOW}[5/8] Adquirir bandas B04+B08 (Process API)...${NC}"
echo "(Este paso puede tardar ~15-30 segundos, descargando desde Copernicus...)"

ACQUIRE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/sentinel/acquire" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"polygon_id\":$POLYGON_ID,\"date\":\"$ACQUISITION_DATE\"}")

ACQUIRE_STATUS=$(echo "$ACQUIRE_RESPONSE" | tail -n1)
ACQUIRE_BODY=$(echo "$ACQUIRE_RESPONSE" | head -n1)

if [[ "$ACQUIRE_STATUS" == "201" ]] || [[ "$ACQUIRE_STATUS" == "200" ]]; then
  ACQUISITION_ID=$(echo "$ACQUIRE_BODY" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
  echo -e "${GREEN}✅ Adquisición completa: ID=$ACQUISITION_ID${NC}"
else
  echo -e "${RED}❌ Error adquiriendo bandas: HTTP $ACQUIRE_STATUS${NC}"
  echo "$ACQUIRE_BODY"
  exit 1
fi

echo -e "\n${YELLOW}[6/8] Calcular NDVI...${NC}"
NDVI_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/ndvi/calculate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"acquisition_id\":$ACQUISITION_ID}")

NDVI_STATUS=$(echo "$NDVI_RESPONSE" | tail -n1)
NDVI_BODY=$(echo "$NDVI_RESPONSE" | head -n1)

if [[ "$NDVI_STATUS" == "201" ]] || [[ "$NDVI_STATUS" == "200" ]]; then
  NDVI_MEAN=$(echo "$NDVI_BODY" | grep -o '"ndvi_mean":[0-9.]*' | cut -d':' -f2)
  echo -e "${GREEN}✅ NDVI calculado: mean=$NDVI_MEAN${NC}"
else
  echo -e "${RED}❌ Error calculando NDVI: HTTP $NDVI_STATUS${NC}"
  echo "$NDVI_BODY"
  exit 1
fi

echo -e "\n${YELLOW}[7/8] Calcular segmentación...${NC}"
SEGMENTATION_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/segmentation/calculate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"acquisition_id\":$ACQUISITION_ID,\"threshold\":0.3}")

SEGMENTATION_STATUS=$(echo "$SEGMENTATION_RESPONSE" | tail -n1)
SEGMENTATION_BODY=$(echo "$SEGMENTATION_RESPONSE" | head -n1)

if [[ "$SEGMENTATION_STATUS" == "201" ]] || [[ "$SEGMENTATION_STATUS" == "200" ]]; then
  CULTIVATED_PCT=$(echo "$SEGMENTATION_BODY" | grep -o '"cultivated_percentage":[0-9.]*' | cut -d':' -f2)
  SEGMENTATION_ID=$(echo "$SEGMENTATION_BODY" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
  echo -e "${GREEN}✅ Segmentación completa: ${CULTIVATED_PCT}% cultivado, ID=$SEGMENTATION_ID${NC}"
else
  echo -e "${RED}❌ Error calculando segmentación: HTTP $SEGMENTATION_STATUS${NC}"
  echo "$SEGMENTATION_BODY"
  exit 1
fi

echo -e "\n${YELLOW}[8/8] Calcular descriptores de textura...${NC}"
TEXTURE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/texture/calculate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"segmentation_result_id\":$SEGMENTATION_ID}")

TEXTURE_STATUS=$(echo "$TEXTURE_RESPONSE" | tail -n1)
TEXTURE_BODY=$(echo "$TEXTURE_RESPONSE" | head -n1)

if [[ "$TEXTURE_STATUS" == "201" ]] || [[ "$TEXTURE_STATUS" == "200" ]]; then
  DESCRIPTORS_COUNT=$(echo "$TEXTURE_BODY" | grep -o '"kernel_type"' | wc -l)
  echo -e "${GREEN}✅ Textura calculada: $DESCRIPTORS_COUNT descriptores${NC}"
else
  echo -e "${RED}❌ Error calculando textura: HTTP $TEXTURE_STATUS${NC}"
  echo "$TEXTURE_BODY"
  exit 1
fi

echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN}✅ WORKFLOW E2E COMPLETO${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "Resumen:"
echo "  - Usuario: $EMAIL"
echo "  - Parcela: ID=$POLYGON_ID (Parcela 211 SRRG)"
echo "  - Fecha: $ACQUISITION_DATE"
echo "  - Adquisición: ID=$ACQUISITION_ID"
echo "  - NDVI: mean=$NDVI_MEAN"
echo "  - Segmentación: ${CULTIVATED_PCT}% cultivado (ID=$SEGMENTATION_ID)"
echo "  - Textura: $DESCRIPTORS_COUNT descriptores"
echo ""
echo -e "${YELLOW}Verificar frontend en: http://localhost:3000${NC}"
echo -e "${YELLOW}Dashboard parcela: http://localhost:3000/cultivos/$POLYGON_ID${NC}"
