import asyncio
import socket
from typing import Any

from taq.connectors.base import BaseConnector, ConnectorResult


class DNSResolverConnector(BaseConnector):
    def name(self) -> str:
        return "dns_resolver"

    async def health(self) -> dict:
        return {"status": "ok", "connector": self.name()}

    async def call(self, action: str, params: dict) -> ConnectorResult:
        if action == "resolve":
            return await self._resolve(params)
        elif action == "reverse":
            return await self._reverse(params)
        elif action == "mx":
            return await self._mx(params)
        elif action == "txt":
            return await self._txt(params)
        return ConnectorResult(False, error=f"Unknown action: {action}")

    async def _resolve(self, params: dict) -> ConnectorResult:
        hostname = params.get("hostname", "")
        if not hostname:
            return ConnectorResult(False, error="hostname required")
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(None, socket.gethostbyname_ex, hostname)
            return ConnectorResult(True, data={
                "hostname": hostname,
                "ips": result[2],
                "aliases": result[0],
            })
        except Exception as e:
            return ConnectorResult(False, error=str(e))

    async def _reverse(self, params: dict) -> ConnectorResult:
        ip = params.get("ip", "")
        if not ip:
            return ConnectorResult(False, error="ip required")
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(None, socket.gethostbyaddr, ip)
            return ConnectorResult(True, data={"ip": ip, "hostname": result[0]})
        except socket.herror:
            # DNS resolution failed - return hostname as None
            return ConnectorResult(True, data={"ip": ip, "hostname": None})
        except Exception as e:
            # Other unexpected errors
            return ConnectorResult(False, error=str(e))

    async def _mx(self, params: dict) -> ConnectorResult:
        domain = params.get("domain", "")
        if not domain:
            return ConnectorResult(False, error="domain required")
        try:
            import dns.resolver
            loop = asyncio.get_event_loop()
            answers = await loop.run_in_executor(
                None, lambda: [str(r.exchange) for r in dns.resolver.resolve(domain, 'MX')]
            )
            return ConnectorResult(True, data={"domain": domain, "mx": answers})
        except ImportError:
            return ConnectorResult(False, error="dnspython not installed")
        except Exception as e:
            return ConnectorResult(False, error=str(e))

    async def _txt(self, params: dict) -> ConnectorResult:
        domain = params.get("domain", "")
        if not domain:
            return ConnectorResult(False, error="domain required")
        try:
            import dns.resolver
            answers = await asyncio.get_event_loop().run_in_executor(
                None, lambda: [str(r) for r in dns.resolver.resolve(domain, "TXT")]
            )
            return ConnectorResult(True, data={"domain": domain, "txt": answers})
        except ImportError:
            return ConnectorResult(False, error="dnspython not installed")
        except Exception as e:
            return ConnectorResult(False, error=str(e))
