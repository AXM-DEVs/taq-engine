from taq.connectors.base import BaseConnector, ConnectorResult


class ShodanFreeConnector(BaseConnector):
    def __init__(self):
        self._api_key = ""

    def configure(self, api_key: str):
        self._api_key = api_key

    def name(self) -> str:
        return "shodan_free"

    async def health(self) -> dict:
        if not self._api_key:
            return {"status": "no_key", "connector": self.name()}
        # Perform a lightweight connectivity check by querying Shodan API for a known IP
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(
                    "https://api.shodan.io/shodan/host/8.8.8.8",
                    params={"key": self._api_key, "minify": True}
                )
                if resp.status_code == 200:
                    return {"status": "ok", "connector": self.name()}
                elif resp.status_code == 401:
                    return {"status": "error", "connector": self.name(), "error": "Invalid Shodan API key"}
                elif resp.status_code == 403:
                    return {"status": "error", "connector": self.name(), "error": "Shodan API access forbidden"}
                else:
                    return {"status": "error", "connector": self.name(), "error": f"Shodan API error: {resp.status_code}"}
        except ImportError:
            return {"status": "error", "connector": self.name(), "error": "httpx not installed"}
        except Exception as e:
            return {"status": "error", "connector": self.name(), "error": str(e)}

    async def call(self, action: str, params: dict) -> ConnectorResult:
        if not self._api_key:
            return ConnectorResult(False, error="Shodan API key not configured. Get a free key at https://account.shodan.io")
        if action == "ip":
            return await self._ip_lookup(params)
        return ConnectorResult(False, error=f"Unknown action: {action}")

    async def _ip_lookup(self, params: dict) -> ConnectorResult:
        ip = params.get("ip", "")
        if not ip:
            return ConnectorResult(False, error="ip required")
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"https://api.shodan.io/shodan/host/{ip}",
                    params={"key": self._api_key, "minify": True},
                )
                if resp.status_code == 200:
                    return ConnectorResult(True, data=resp.json())
                elif resp.status_code == 401:
                    return ConnectorResult(False, error="Invalid Shodan API key")
                elif resp.status_code == 404:
                    return ConnectorResult(True, data={"ip": ip, "ports": [], "hostnames": []})
                return ConnectorResult(False, error=f"Shodan error: {resp.status_code}")
        except ImportError:
            return ConnectorResult(False, error="httpx not installed")
        except Exception as e:
            return ConnectorResult(False, error=str(e))
