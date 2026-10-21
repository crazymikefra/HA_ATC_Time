"""ATC Time Sync : met à l'heure les capteurs sous firmware ATC / pvvx."""
from __future__ import annotations

import asyncio
import logging

import voluptuous as vol
from bleak.exc import BleakError
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

from homeassistant.components import bluetooth
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

DOMAIN = "atc_time"
WRITE_UUID = "00001f1f-0000-1000-8000-00805f9b34fb"
CMD_SET_TIME = 0x23

CONF_ADDRESS = "device_address"
CONF_WAIT_TIME = "wait_time"

CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)

SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ADDRESS): vol.All(cv.string, vol.Upper),
        vol.Optional(CONF_WAIT_TIME, default=30): vol.All(
            vol.Coerce(float), vol.Range(min=5, max=300)
        ),
    }
)

# Un verrou par appareil : deux appels simultanés ne doivent pas ouvrir
# chacun leur propre connexion.
_LOCKS: dict[str, asyncio.Lock] = {}


def _build_time_payload() -> bytes:
    """Commande 0x23 + timestamp en heure locale (fuseau de HA), little-endian."""
    now = dt_util.now()  # fuseau configuré dans HA, pas celui du conteneur
    offset = now.utcoffset()
    local_ts = int(now.timestamp() + (offset.total_seconds() if offset else 0))
    return bytes([CMD_SET_TIME]) + local_ts.to_bytes(4, "little")


async def _connect(hass: HomeAssistant, address: str) -> BleakClientWithServiceCache:
    """Ouvre une connexion via la pile Bluetooth de HA (adaptateur local ou proxy)."""
    ble_device = bluetooth.async_ble_device_from_address(
        hass, address, connectable=True
    )
    if ble_device is None:
        raise HomeAssistantError(
            f"{address} n'a pas été vu récemment par un adaptateur "
            "ou un proxy Bluetooth capable de s'y connecter"
        )
    return await establish_connection(
        BleakClientWithServiceCache,
        ble_device,
        address,
        max_attempts=3,
    )


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Enregistre les actions du composant."""

    async def handle_set_time(call: ServiceCall) -> None:
        address: str = call.data[CONF_ADDRESS]
        payload = _build_time_payload()
        lock = _LOCKS.setdefault(address, asyncio.Lock())

        try:
            async with lock, asyncio.timeout(call.data[CONF_WAIT_TIME]):
                client = await _connect(hass, address)
                try:
                    _LOGGER.debug("%s : envoi %s", address, payload.hex())
                    await client.write_gatt_char(WRITE_UUID, payload, response=True)
                finally:
                    await client.disconnect()
        except (BleakError, TimeoutError) as err:
            raise HomeAssistantError(
                f"Mise à l'heure de {address} impossible : {err!r}"
            ) from err

        _LOGGER.debug("%s : heure mise à jour", address)

    async def handle_get_characteristics(call: ServiceCall) -> ServiceResponse:
        address: str = call.data[CONF_ADDRESS]
        lock = _LOCKS.setdefault(address, asyncio.Lock())
        services: dict[str, dict[str, str | None]] = {}

        try:
            async with lock, asyncio.timeout(call.data[CONF_WAIT_TIME]):
                client = await _connect(hass, address)
                try:
                    for service in client.services:
                        chars: dict[str, str | None] = {}
                        for char in service.characteristics:
                            value = None
                            if "read" in char.properties:
                                try:
                                    value = (await client.read_gatt_char(char)).hex()
                                except BleakError as err:
                                    value = f"erreur : {err}"
                            chars[f"{char.uuid} {char.properties}"] = value
                            _LOGGER.debug("%s -> %s ==> %s", service.uuid, char, value)
                        services[service.uuid] = chars
                finally:
                    await client.disconnect()
        except (BleakError, TimeoutError) as err:
            raise HomeAssistantError(
                f"Lecture des caractéristiques de {address} impossible : {err!r}"
            ) from err

        return {"services": services}

    hass.services.async_register(
        DOMAIN, "set_atc_time", handle_set_time, schema=SERVICE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN,
        "get_characteristics",
        handle_get_characteristics,
        schema=SERVICE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    return True
