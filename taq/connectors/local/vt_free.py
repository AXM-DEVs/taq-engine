from taq.connectors.base import BaseConnector, ConnectorResult


class VirusTotalFreeConnector(BaseConnector):
    def __init__(self):
        self._api_key = ""

    def configure(self, api_key: str):
        self._api_key = api_key

    def name(self) -> str:
        return "virustotal_free"

    async def health(self) -> dict:
        if not self._api_key:
            return {"status": "no_key", "connector": self.name()}
        # Perform a lightweight connectivity check by querying VirusTotal API for a known hash
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5) as client:
                # Using the hash of EICAR test file (a known harmless test file)
                resp = await client.get(
                    "https://www.virustotal.com/api/v3/files/44d88612fea8a8f36de82e1278abb02f",
                    headers={"x-apikey": self._api_key}
                )
                if resp.status_code == 200:
                    return {"status": "ok", "connector": self.name()}
                elif resp.status_code == 401:
                    return {"status": "error", "connector": self.name(), "error": "Invalid VirusTotal API key"}
                elif resp.status_code == 403:
                    return {"status": "error", "connector": self.name(), "error": "VirusTotal API access forbidden"}
                else:
                    return {"status": "error", "connector": self.name(), "error": f"VirusTotal API error: {resp.status_code}"}
        except ImportError:
            return {"status": "error", "connector": self.name(), "error": "httpx not installed"}
        except Exception as e:
            return {"status": "error", "connector": self.name(), "error": str(e)}

    async def call(self, action: str, params: dict) -> ConnectorResult:
        if not self._api_key:
            return ConnectorResult(False, error="VirusTotal API key not configured. Get a free key at https://www.virustotal.com")
        if action == "ip":
            return await self._ip_report(params)
        elif action == "domain":
            return await self._domain_report(params)
        elif action == "hash":
            return await self._hash_report(params)
        elif action == "url":
            return await self._url_report(params)
        return ConnectorResult(False, error=f"Unknown action: {action}")

    async def _ip_report(self, params: dict) -> ConnectorResult:
        ip = params.get("ip", "")
        if not ip:
            return ConnectorResult(False, error="ip required")
        return await self._get(f"https://www.virustotal.com/api/v3/ip_addresses/{ip}")

    async def _domain_report(self, params: dict) -> ConnectorResult:
        domain = params.get("domain", "")
        if not domain:
            return ConnectorResult(False, error="domain required")
        return await self._get(f"https://www.virustotal.com/api/v3/domains/{domain}")

    async def _hash_report(self, params: dict) -> ConnectorResult:
        h = params.get("hash", "")
        if not h:
            return ConnectorResult(False, error="hash required")
        return await self._get(f"https://www.virustotal.com/api/v3/files/{h}")

    async def _url_report(self, params: dict) -> ConnectorResult:
        url = params.get("url", "")
        if not url:
            return ConnectorResult(False, error="url required")
        import base64
        url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
        return await self._get(f"https://www.virustotal.com/api/v3/urls/{url_id}")

    async def _get(self, url: str) -> ConnectorResult:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url, headers={"x-apikey": self._api_key})
                if resp.status_code == 200:
                    data = resp.json()
                    attrs = data.get("data", {}).get("attributes", {})
                    last_stats = attrs.get("last_analysis_stats", {})
                    return ConnectorResult(True, data={
                        "malicious": last_stats.get("malicious", 0),
                        "suspicious": last_stats.get("suspicious", 0),
                        "harmless": last_stats.get("harmless", 0),
                        "undetected": last_stats.get("undetected", 0),
                        "reputation": attrs.get("reputation", 0),
                        "last_analysis_date": attrs.get("last_analysis_date"),
                    })
                elif resp.status_code == 404:
                    return ConnectorResult(True, data={"malicious": 0, "suspicious": 0})
                return ConnectorResult(False, error=f"VT error: {resp.status_code}")
        except ImportError:
            return ConnectorResult(False, error="httpx not installed")
        except Exception as e:
            return ConnectorResult(False, error=str(e))
