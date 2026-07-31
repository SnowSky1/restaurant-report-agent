"""Application configuration.

Secrets are loaded from ``.env`` and never returned by the public API.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Data acquisition. ``auto`` prefers real data and falls back per call.
    data_mode: Literal["auto", "real", "mock"] = "auto"
    amap_transport: Literal["rest", "mcp"] = "rest"
    request_timeout_seconds: float = 30.0
    amap_cache_ttl_seconds: float = 300.0
    amap_max_retries: int = 2
    amap_max_parallel_requests: int = 4

    # LLM provider selection.
    llm_provider: Literal["openai", "deepseek", "qwen", "siliconflow"] = "qwen"
    llm_timeout_seconds: float = 60.0
    llm_max_retries: int = 0
    enable_krill_fallback: bool = True

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"

    qwen_api_key: str = ""
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    qwen_model: str = "qwen-plus"

    siliconflow_api_key: str = ""
    siliconflow_base_url: str = "https://api.siliconflow.cn/v1"
    siliconflow_model: str = "Qwen/Qwen2.5-72B-Instruct"

    # Map services. REST is the reliable primary path; MCP remains supported.
    amap_maps_api_key: str = ""
    amap_mcp_url: str = "https://mcp.modelscope.cn/sse/@amap/amap-maps"
    output_dir: str = "./reports"
    save_api_reports: bool = False
    report_retention_days: int = 30
    allowed_origins: str = Field(default="http://localhost:3000,http://127.0.0.1:3000")
    api_access_token: str = ""
    api_rate_limit_per_minute: int = 20
    max_concurrent_analyses: int = 2
    analysis_timeout_seconds: float = 180.0
    log_level: str = "INFO"

    def get_llm_config(self) -> dict[str, str]:
        configs = {
            "openai": {
                "provider": "openai",
                "api_key": self.openai_api_key,
                "base_url": self.openai_base_url,
                "model": self.openai_model,
            },
            "deepseek": {
                "provider": "deepseek",
                "api_key": self.deepseek_api_key,
                "base_url": self.deepseek_base_url,
                "model": self.deepseek_model,
            },
            "qwen": {
                "provider": "qwen",
                "api_key": self.qwen_api_key,
                "base_url": self.qwen_base_url,
                "model": self.qwen_model,
            },
            "siliconflow": {
                "provider": "siliconflow",
                "api_key": self.siliconflow_api_key,
                "base_url": self.siliconflow_base_url,
                "model": self.siliconflow_model,
            },
        }
        return configs[self.llm_provider]

    def validate_config(self, *, require_llm: bool = True) -> list[str]:
        errors: list[str] = []
        if require_llm and not self.get_llm_config().get("api_key"):
            errors.append(f"{self.llm_provider.upper()}_API_KEY is not set")
        if self.data_mode == "real" and not self.amap_maps_api_key:
            errors.append("AMAP_MAPS_API_KEY is not set while DATA_MODE=real")
        return errors

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()
