from provenaclient import ProvenaClient, Config
from provenaclient.auth import DeviceFlow
from pydantic import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # The provena deployment to target
    provena_domain: str = "mds.gbrrestoration.org"
    # The keycloak realm name
    provena_realm_name: str = "rrap"
    # The keycloak client ID
    provena_client_id: str = "automated-access"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """Uses the Pydantic settings management to read settings from defaults/the
    environment.

    Returns
    -------
    Settings
        The instantiated settings object.
    """
    return Settings()


def get_provena_client(settings: Optional[Settings] = None) -> ProvenaClient:
    """Returns an authorised provena client ready to interact with the M&DS IS.

    Returns
    -------
    ProvenaClient
        The instantiated and authenticated client.
    """
    _settings = settings if settings else get_settings()
    config = Config(
        domain=_settings.provena_domain, realm_name=_settings.provena_realm_name
    )
    return ProvenaClient(
        auth=DeviceFlow(config=config, client_id=_settings.provena_client_id),
        config=config,
    )
