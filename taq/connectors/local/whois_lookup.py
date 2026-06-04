import asyncio
import socket

from taq.connectors.base import BaseConnector, ConnectorResult


class WhoisConnector(BaseConnector):
    WHOIS_SERVERS = {
        "com": "whois.verisign-grs.com",
        "net": "whois.verisign-grs.com",
        "org": "whois.pir.org",
        "io": "whois.nic.io",
        "xyz": "whois.nic.xyz",
        "dev": "whois.nic.google",
        "app": "whois.nic.google",
    }

    def name(self) -> str:
        return "whois"

    async def health(self) -> dict:
        # Perform a lightweight connectivity check by querying a known domain
        try:
            # Try to query whois.iana.org for a simple domain to verify connectivity
            loop = asyncio.get_event_loop()
            raw = await loop.run_in_executor(None, self._query_whois, "example.com", "whois.iana.org")
            if raw:
                return {"status": "ok", "connector": self.name()}
            else:
                return {"status": "error", "connector": self.name(), "error": "No response from WHOIS server"}
        except Exception as e:
            return {"status": "error", "connector": self.name(), "error": str(e)}

    async def call(self, action: str, params: dict) -> ConnectorResult:
        if action == "lookup":
            return await self._lookup(params)
        elif action == "ip":
            return await self._ip_lookup(params)
        return ConnectorResult(False, error=f"Unknown action: {action}")

    async def _lookup(self, params: dict) -> ConnectorResult:
        domain = params.get("domain", "")
        if not domain:
            return ConnectorResult(False, error="domain required")
        tld = domain.rsplit(".", 1)[-1].lower() if "." in domain else ""
        server = self.WHOIS_SERVERS.get(tld, "whois.iana.org")
        loop = asyncio.get_event_loop()
        try:
            raw = await loop.run_in_executor(None, self._query_whois, domain, server)
            parsed = self._parse_whois(raw)
            return ConnectorResult(True, data={"domain": domain, "raw": raw[:2000], "parsed": parsed})
        except Exception as e:
            return ConnectorResult(False, error=str(e))

    async def _ip_lookup(self, params: dict) -> ConnectorResult:
        ip = params.get("ip", "")
        if not ip:
            return ConnectorResult(False, error="ip required")
        loop = asyncio.get_event_loop()
        try:
            raw = await loop.run_in_executor(None, self._query_whois, ip, "whois.arin.net")
            return ConnectorResult(True, data={"ip": ip, "raw": raw[:2000]})
        except Exception as e:
            return ConnectorResult(False, error=str(e))

    def _query_whois(self, query: str, server: str, port: int = 43) -> str:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        try:
            sock.connect((server, port))
            sock.send(f"{query}\r\n".encode())
            response = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
            return response.decode("utf-8", errors="ignore")
        finally:
            sock.close()

    def _parse_whois(self, raw: str) -> dict:
        parsed = {}
        important_keys = [
            "Domain Name", "Registrar", "Creation Date", "Expiry Date",
            "Name Server", "Registrant Organization", "Registrant Country",
            "Admin Email", "Tech Email",
        ]
        for line in raw.split("\n"):
            for key in important_keys:
                if line.lower().startswith(key.lower() + ":"):
                    value = line.split(":", 1)[1].strip()
                    if key in parsed:
                        if isinstance(parsed[key], list):
                            parsed[key].append(value)
                        else:
                            parsed[key] = [parsed[key], value]
                    else:
                        parsed[key] = value
        return parsed
