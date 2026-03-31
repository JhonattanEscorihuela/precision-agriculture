"""
Tests para el servicio de adquisición Sentinel-2.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.sentinel_service import SentinelService


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Configura variables de entorno para testing."""
    monkeypatch.setenv("SENTINEL_CLIENT_ID", "test_client_id")
    monkeypatch.setenv("SENTINEL_CLIENT_SECRET", "test_client_secret")


@pytest.fixture
def sentinel_service(mock_env_vars):
    """Crea una instancia del servicio Sentinel para testing."""
    return SentinelService()


@pytest.fixture
def sample_polygon_geojson():
    """Polígono de ejemplo en formato GeoJSON."""
    return {
        "type": "Polygon",
        "coordinates": [[
            [-67.477732, 8.890243],
            [-67.472585, 8.891811],
            [-67.482623, 8.921237],
            [-67.487942, 8.916531],
            [-67.479534, 8.892108],
            [-67.47859, 8.892151],
            [-67.477732, 8.890243]
        ]]
    }


def test_sentinel_service_initialization(sentinel_service):
    """Verifica que el servicio se inicialice correctamente."""
    assert sentinel_service.client_id == "test_client_id"
    assert sentinel_service.client_secret == "test_client_secret"
    assert sentinel_service._access_token is None


def test_sentinel_service_missing_credentials():
    """Verifica que falle sin credenciales."""
    with pytest.raises(ValueError, match="Missing credentials"):
        SentinelService()


@patch('app.services.sentinel_service.OAuth2Session')
def test_authenticate_success(mock_oauth_session, sentinel_service):
    """Verifica autenticación exitosa."""
    # Mock del token response
    mock_token = {"access_token": "test_token_123"}
    mock_session_instance = Mock()
    mock_session_instance.fetch_token.return_value = mock_token
    mock_oauth_session.return_value = mock_session_instance

    # Ejecutar autenticación
    token = sentinel_service.authenticate()

    # Verificar
    assert token == "test_token_123"
    assert sentinel_service._access_token == "test_token_123"
    mock_session_instance.fetch_token.assert_called_once()


@pytest.mark.asyncio
@patch('httpx.AsyncClient')
@patch.object(SentinelService, 'authenticate')
async def test_download_ndvi_success(
    mock_auth,
    mock_httpx_client,
    sentinel_service,
    sample_polygon_geojson
):
    """Verifica descarga exitosa de NDVI."""
    # Mock de autenticación
    mock_auth.return_value = "test_token"
    sentinel_service._access_token = "test_token"

    # Mock de respuesta HTTP
    mock_response = Mock()
    mock_response.content = b"fake_tiff_data"
    mock_response.raise_for_status = Mock()

    mock_client_instance = Mock()
    mock_client_instance.post = AsyncMock(return_value=mock_response)
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock()

    mock_httpx_client.return_value = mock_client_instance

    # Ejecutar descarga
    result = await sentinel_service.download_ndvi(
        polygon_geojson=sample_polygon_geojson,
        start_date="2024-01-15",
        end_date="2024-01-20"
    )

    # Verificar
    assert result == b"fake_tiff_data"
    mock_client_instance.post.assert_called_once()


@pytest.mark.asyncio
@patch('httpx.AsyncClient')
@patch.object(SentinelService, 'authenticate')
async def test_download_bands_success(
    mock_auth,
    mock_httpx_client,
    sentinel_service,
    sample_polygon_geojson
):
    """Verifica descarga exitosa de bandas específicas."""
    # Mock de autenticación
    mock_auth.return_value = "test_token"
    sentinel_service._access_token = "test_token"

    # Mock de respuesta HTTP
    mock_response = Mock()
    mock_response.content = b"fake_multiban_tiff_data"
    mock_response.raise_for_status = Mock()

    mock_client_instance = Mock()
    mock_client_instance.post = AsyncMock(return_value=mock_response)
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock()

    mock_httpx_client.return_value = mock_client_instance

    # Ejecutar descarga
    result = await sentinel_service.download_bands(
        polygon_geojson=sample_polygon_geojson,
        bands=["B04", "B08"],
        start_date="2024-01-15",
        end_date="2024-01-20"
    )

    # Verificar
    assert result == b"fake_multiban_tiff_data"
    mock_client_instance.post.assert_called_once()

    # Verificar que el evalscript incluya las bandas solicitadas
    call_args = mock_client_instance.post.call_args
    request_payload = call_args.kwargs['json']
    assert 'B04' in request_payload['evalscript']
    assert 'B08' in request_payload['evalscript']


@pytest.mark.asyncio
@patch('httpx.AsyncClient')
@patch.object(SentinelService, 'authenticate')
async def test_check_availability_available(
    mock_auth,
    mock_httpx_client,
    sentinel_service,
    sample_polygon_geojson
):
    """Verifica check de disponibilidad cuando hay imágenes."""
    # Mock de autenticación
    mock_auth.return_value = "test_token"
    sentinel_service._access_token = "test_token"

    # Mock de respuesta HTTP exitosa
    mock_response = Mock()
    mock_response.content = b"test_data"
    mock_response.raise_for_status = Mock()

    mock_client_instance = Mock()
    mock_client_instance.post = AsyncMock(return_value=mock_response)
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock()

    mock_httpx_client.return_value = mock_client_instance

    # Ejecutar verificación
    result = await sentinel_service.check_availability(
        polygon_geojson=sample_polygon_geojson,
        start_date="2024-01-15",
        end_date="2024-01-20"
    )

    # Verificar
    assert result["available"] is True
    assert result["date_range"]["from"] == "2024-01-15"
    assert result["date_range"]["to"] == "2024-01-20"
    assert "available" in result["message"].lower()
