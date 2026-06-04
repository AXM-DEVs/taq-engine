# TaQ Engine — Tactical Analysis & Qualification Engine

[![Version](https://img.shields.io/badge/version-1.0.0-6c5ce7?style=for-the-badge)]()
[![Python](https://img.shields.io/badge/python-3.12-3776AB?style=for-the-badge&logo=python)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi)]()
[![License](https://img.shields.io/badge/license-MIT-a29bfe?style=for-the-badge)]()

**desarrollado por [AXM](https://github.com/AXM-D)**

---

TaQ Engine es un motor de inteligencia y automatización para plataformas OSINT. Proporciona orquestación de investigaciones mediante playbooks, scoring multi-factor de amenazas, y consultas en lenguaje natural.

Pensado como núcleo extensible: cualquier plataforma externa (SENTINEL, MISP, Shodan, etc.) puede conectarse mediante el **sistema de conectores**.

## Capabilities

- **Playbook Orchestrator** — Define flujos de investigación en YAML con branching condicional
- **Analysis & Scoring Engine** — Threat scoring multi-factor (freshness, source, correlation, reputation)
- **Query Engine** — Lenguaje natural → SQL / Cypher
- **Connector System** — Plugins para integrar cualquier plataforma externa
- **REST API** — FastAPI, 15+ endpoints, Swagger docs

## Products built on TaQ

| Product | Description | License |
|---|---|---|
| **TaQ Engine Core** | Motor genérico (este repositorio) | MIT |
| **TaQ Engine for SENTINEL** | Versión con conector nativo para SENTINEL OSINT | TaQ Community |
| **DySH General** | Producto open source basado en TaQ | MIT |
| **DySH Premium** | Versión enterprise con dashboard, WebSocket, ML | Comercial |

## Quick Start

```bash
pip install -r requirements.txt
make dev
# → http://localhost:8400/docs
```

## Connectors

TaQ Engine usa un sistema de conectores para integrarse con plataformas externas. Los conectores se registran en el `ConnectorRegistry` y pueden ser llamados desde playbooks mediante el step `connector_call`.

```python
from taq.connectors.registry import connector_registry
from taq.connectors.base import BaseConnector, ConnectorResult

class MyConnector(BaseConnector):
    def name(self) -> str: return "my_platform"
    async def health(self) -> dict: return {"status": "ok"}
    async def call(self, action: str, params: dict) -> ConnectorResult:
        # ... implementar llamada a la plataforma externa
        return ConnectorResult(success=True, data=result)

connector_registry.register(MyConnector())
```

## License

MIT — Open source, libre uso y modificación.
