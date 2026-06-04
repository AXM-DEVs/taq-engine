from taq.connectors.base import BaseConnector, ConnectorResult


class AbuseIPDBConnector(BaseConnector):
    def __init__(self):
        self._api_key = ""

    def configure(self, api_key: str):
        self._api_key = api_key

    def name(self) -> str:
        return "abuseipdb"

    async def health(self) -> dict:
        if not self._api_key:
            return {"status": "no_key", "connector": self.name()}
        # Perform a lightweight connectivity check by querying AbuseIPDB API for a known IP
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(
                    "https://api.abuseipdb.com/api/v2/check",
                    params={"ipAddress": "8.8.8.8", "maxAgeInDays": 90},
                    headers={"Key": self._api_key, "Accept": "application/json"},
                )
                if resp.status_code == 200:
                    return {"status": "ok", "connector": self.name()}
                elif resp.status_code == 401:
                    return {"status": "error", "connector": self.name(), "error": "Invalid AbuseIPDB API key"}
                elif resp.status_code == 403:
                    return {"status": "error", "connector": self.name(), "error": "AbuseIPDB API access forbidden"}
                else:
                    return {"status": "error", "connector": self.name(), "error": f"AbuseIPDB API error: {resp.status_code}"}
        except ImportError:
            return {"status": "error", "connector": self.name(), "error": "httpx not installed"}
        except Exception as e:
            return {"status": "error", "connector": self.name(), "error": str(e)}

    async def call(self, action: str, params: dict) -> ConnectorResult:
        if not self._api_key:
            return ConnectorResult(False, error="AbuseIPDB API key not configured. Get a free key at https://www.abuseipdb.com")
        if action == "check":
            return await self._check_ip(params)
        elif action == "report":
            return await self._report_ip(params)
        return ConnectorResult(False, error=f"Unknown action: {action}")

    async def _check_ip(self, params: dict) -> ConnectorResult:
        ip = params.get("ip", "")
        if not ip:
            return ConnectorResult(False, error="ip required")
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://api.abuseipdb.com/api/v2/check",
                    params={"ipAddress": ip, "maxAgeInDays": 90},
                    headers={"Key": self._api_key, "Accept": "application/json"},
                )
                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    return ConnectorResult(True, data={
                        "ip": ip,
                        "is_public": data.get("isPublic"),
                        "is_whitelisted": data.get("isWhitelisted"),
                        "abuse_confidence_score": data.get("abuseConfidenceScore", 0),
                        "country_code": data.get("countryCode"),
                        "domain": data.get("domain"),
                        "total_reports": data.get("totalReports", 0),
                        "last_reported_at": data.get("lastReportedAt"),
                    })
                return ConnectorResult(False, error=f"AbuseIPDB error: {resp.status_code}")
        except ImportError:
            return ConnectorResult(False, error="httpx not installed")
        except Exception as e:
            return ConnectorResult(False, error=str(e))

    async def _report_ip(self, params: dict) -> ConnectorResult:
        ip = params.get("ip", "")
        categories = params.get("categories", "21")
        comment = params.get("comment", "Reported by Retro - TaQ Engine")
        if not ip:
            return ConnectorResult(False, error="ip required")
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    "https://api.abuseipdb.com/api/v2/report",
                    json={"ip": ip, "categories": categories, "comment": comment},
                    headers={"Key": self._api_key, "Accept": "application/json"},
                )
                if resp.status_code in (200, 201):
                    return ConnectorResult(True, data=resp.json().get("data", {}))
                return ConnectorResult(False, error=f"AbuseIPDB report error: {resp.status_code}")
        except ImportError:
            return ConnectorResult(False, error="httpx not installed")
        except Exception as e:
            return ConnectorResult(False, error=str(e))
