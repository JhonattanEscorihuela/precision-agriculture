"""
Módulo de autenticación OAuth2 para Copernicus DataSpace.
Responsabilidad: Gestionar tokens de acceso.
"""

import os
import logging
from typing import Optional
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

logger = logging.getLogger(__name__)


class SentinelAuth:
    """Gestiona autenticación OAuth2 con Copernicus DataSpace."""

    TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

    def __init__(self):
        """Inicializa credenciales desde variables de entorno."""
        self.client_id = os.getenv("SENTINEL_CLIENT_ID")
        self.client_secret = os.getenv("SENTINEL_CLIENT_SECRET")

        if not self.client_id or not self.client_secret:
            raise ValueError(
                "Missing credentials: Set SENTINEL_CLIENT_ID and SENTINEL_CLIENT_SECRET "
                "environment variables"
            )

        self._access_token: Optional[str] = None

    def authenticate(self) -> str:
        """
        Obtiene token de acceso OAuth2.

        Returns:
            str: Token de acceso válido

        Raises:
            Exception: Si falla la autenticación
        """
        logger.info("🔐 Authenticating with Copernicus DataSpace...")
        client = BackendApplicationClient(client_id=self.client_id)
        oauth = OAuth2Session(client=client)

        token_response = oauth.fetch_token(
            token_url=self.TOKEN_URL,
            client_id=self.client_id,
            client_secret=self.client_secret,
            include_client_id=True
        )

        self._access_token = token_response["access_token"]
        logger.info(f"✅ Authentication successful! Token: {self._access_token[:20]}...")
        return self._access_token

    def ensure_authenticated(self) -> str:
        """
        Verifica token existente o autentica.

        Returns:
            str: Token de acceso válido
        """
        if not self._access_token:
            self.authenticate()
        return self._access_token

    @property
    def token(self) -> Optional[str]:
        """Retorna el token actual (puede ser None)."""
        return self._access_token
