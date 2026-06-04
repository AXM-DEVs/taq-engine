from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional

import yaml


@dataclass
class DatabaseConfig:
    engine: Literal["sqlite", "postgresql"] = "sqlite"
    host: str = "localhost"
    port: int = 5432
    user: str = "taq"
    password: str = ""
    database: str = "taq"

    @property
    def dsn(self) -> str:
        if self.engine == "sqlite":
            return f"sqlite+aiosqlite:///{self.database}.db"
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    @property
    def dsn_sync(self) -> str:
        if self.engine == "sqlite":
            return f"sqlite:///{self.database}.db"
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class LLMConfig:
    provider: Literal["ollama", "openai"] = "ollama"
    model: str = "mistral:7b"
    base_url: str = "http://localhost:11434"
    api_key: str = ""
    temperature: float = 0.1
    max_tokens: int = 2048


@dataclass
class LoggingConfig:
    level: str = "INFO"
    format: str = "console"


@dataclass
class CacheConfig:
    enabled: bool = True
    default_ttl: int = 300


@dataclass
class AppConfig:
    debug: bool = False
    secret_key: str = ""
    data_dir: Path = Path("./data")
    db: DatabaseConfig = field(default_factory=DatabaseConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)

    @classmethod
    def from_yaml(cls, path: str | Path) -> AppConfig:
        path = Path(path)
        if not path.exists():
            return cls()
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls._from_dict(data or {})

    @classmethod
    def from_env(cls) -> AppConfig:
        return cls(
            debug=os.getenv("TAQ_DEBUG", "false").lower() == "true",
            secret_key=os.getenv("TAQ_SECRET_KEY", "change-me"),
            db=DatabaseConfig(
                engine=os.getenv("TAQ_DB_ENGINE", "sqlite"),
                host=os.getenv("TAQ_DB_HOST", "localhost"),
                port=int(os.getenv("TAQ_DB_PORT", "5432")),
                user=os.getenv("TAQ_DB_USER", "taq"),
                password=os.getenv("TAQ_DB_PASSWORD", ""),
                database=os.getenv("TAQ_DB_NAME", "taq"),
            ),
            llm=LLMConfig(
                provider=os.getenv("TAQ_LLM_PROVIDER", "ollama"),
                model=os.getenv("TAQ_LLM_MODEL", "mistral:7b"),
                base_url=os.getenv("TAQ_LLM_BASE_URL", "http://localhost:11434"),
                api_key=os.getenv("TAQ_LLM_API_KEY", ""),
            ),
            logging=LoggingConfig(
                level=os.getenv("TAQ_LOG_LEVEL", "INFO"),
            ),
            cache=CacheConfig(
                enabled=os.getenv("TAQ_CACHE_ENABLED", "true").lower() == "true",
                default_ttl=int(os.getenv("TAQ_CACHE_TTL", "300")),
            ),
        )

    @classmethod
    def _from_dict(cls, data: dict) -> AppConfig:
        db = data.get("database", {})
        llm = data.get("llm", {})
        logging_ = data.get("logging", {})
        cache_ = data.get("cache", {})
        return cls(
            debug=data.get("debug", False),
            secret_key=data.get("secret_key", "change-me"),
            data_dir=Path(data.get("data_dir", "./data")),
            db=DatabaseConfig(
                engine=db.get("engine", "sqlite"),
                host=db.get("host", "localhost"),
                port=db.get("port", 5432),
                user=db.get("user", "taq"),
                password=db.get("password", ""),
                database=db.get("database", "taq"),
            ),
            llm=LLMConfig(
                provider=llm.get("provider", "ollama"),
                model=llm.get("model", "mistral:7b"),
                base_url=llm.get("base_url", "http://localhost:11434"),
                api_key=llm.get("api_key", ""),
            ),
            logging=LoggingConfig(
                level=logging_.get("level", "INFO"),
            ),
            cache=CacheConfig(
                enabled=cache_.get("enabled", True),
                default_ttl=cache_.get("default_ttl", 300),
            ),
        )


config: AppConfig = AppConfig.from_env()


def load_config(path: str | Path | None = None) -> AppConfig:
    global config
    if path:
        config = AppConfig.from_yaml(path)
    else:
        config = AppConfig.from_env()
    return config
