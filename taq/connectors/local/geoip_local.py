import asyncio
import json
import urllib.request
from typing import Any
from urllib.parse import quote

from taq.connectors.base import BaseConnector, ConnectorResult


class GeoIPConnector(BaseConnector):
    def name(self) -> str:
        return "geoip"

    async def health(self) -> dict:
        return {"status": "ok", "connector": self.name()}

    async def call(self, action: str, params: dict) -> ConnectorResult:
        if action == "lookup":
            return await self._lookup(params)
        return ConnectorResult(False, error=f"Unknown action: {action}")

    async def _lookup(self, params: dict) -> ConnectorResult:
        ip = params.get("ip", "")
        if not ip:
            return ConnectorResult(False, error="ip required")
        try:
            data = await asyncio.get_event_loop().run_in_executor(
                None, self._fetch_freegeoip, ip
            )
            if data:
                return ConnectorResult(True, data=data)
            return await self._rdap_lookup(ip)
        except Exception as e:
            return ConnectorResult(False, error=str(e))

    def _fetch_freegeoip(self, ip: str) -> dict | None:
        try:
            url = f"https://ip-api.com/json/{ip}?fields=66846719"
            req = urllib.request.Request(url, headers={"User-Agent": "TaQ-Engine/1.0"})
            resp = urllib.request.urlopen(req, timeout=5)
            data = json.loads(resp.read().decode())
            if data.get("status") == "success":
                return {
                    "ip": ip,
                    "country": data.get("country"),
                    "country_code": data.get("countryCode"),
                    "region": data.get("regionName"),
                    "city": data.get("city"),
                    "zip": data.get("zip"),
                    "lat": data.get("lat"),
                    "lon": data.get("lon"),
                    "isp": data.get("isp"),
                    "org": data.get("org"),
                    "as": data.get("as"),
                    "source": "ip-api.com",
                }
        except Exception:
            pass
        return None

    async def _rdap_lookup(self, ip: str) -> ConnectorResult:
        loop = asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(None, self._fetch_rdap, ip)
            if data:
                return ConnectorResult(True, data={
                    "ip": ip,
                    "org": data.get("name", ""),
                    "country": (data.get("entities") or [{}])[0].get("vcardArray", [[], []])[1][0][3] if data.get("entities") else "",
                    "source": "rdap",
                })
        except Exception:
            pass
        return ConnectorResult(True, data={"ip": ip, "source": "none"})

    def _fetch_rdap(self, ip: str) -> dict | None:
        try:
            url = f"https://rdap.db.ripe.net/ip/{ip}"
            req = urllib.request.Request(url, headers={"User-Agent": "TaQ-Engine/1.0", "Accept": "application/json"})
            resp = urllib.request.urlopen(req, timeout=5)
            return json.loads(resp.read().decode())
        except Exception:
            return None
