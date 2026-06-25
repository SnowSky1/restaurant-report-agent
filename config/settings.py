"""Configuration settings for the restaurant report agent."""

import os
from typing import Literal
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # LLM Provider Selection
    llm_provider: Literal["openai", "deepseek", "qwen", "siliconflow"] = Field(
        default="openai",
        description="LLM provider to use"
    )
    
    # OpenAI Configuration
    openai_api_key: str = Field(default="", description="OpenAI API Key")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model name")
    
    # DeepSeek Configuration
    deepseek_api_key: str = Field(default="", description="DeepSeek API Key")
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com/v1",
        description="DeepSeek API base URL"
    )
    deepseek_model: str = Field(default="deepseek-chat", description="DeepSeek model name")
    
    # Qwen (通义千问) Configuration
    qwen_api_key: str = Field(default="", description="Qwen API Key")
    qwen_base_url: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        description="Qwen API base URL"
    )
    qwen_model: str = Field(default="qwen-plus", description="Qwen model name")
    
    # SiliconFlow Configuration
    siliconflow_api_key: str = Field(default="", description="SiliconFlow API Key")
    siliconflow_base_url: str = Field(
        default="https://api.siliconflow.cn/v1",
        description="SiliconFlow API base URL"
    )
    siliconflow_model: str = Field(default="Qwen/Qwen2.5-72B-Instruct", description="SiliconFlow model name")
    
    # MCP Services Configuration
    amap_maps_api_key: str = Field(default="", description="高德地图 API Key")
    amap_mcp_url: str = Field(
        default="https://mcp.modelscope.cn/sse/@amap/amap-maps",
        description="高德地图 MCP Server URL"
    )
    chart_mcp_url: str = Field(
        default="https://mcp.modelscope.cn/sse/@antvis/mcp-server-chart",
        description="可视化图表 MCP Server URL"
    )
    
    # Output Configuration
    output_dir: str = Field(default="./reports", description="Report output directory")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
    
    def get_llm_config(self) -> dict:
        """Get LLM configuration based on selected provider."""
        if self.llm_provider == "openai":
            return {
                "provider": "openai",
                "api_key": self.openai_api_key,
                "model": self.openai_model,
            }
        elif self.llm_provider == "deepseek":
            return {
                "provider": "deepseek",
                "api_key": self.deepseek_api_key,
                "base_url": self.deepseek_base_url,
                "model": self.deepseek_model,
            }
        elif self.llm_provider == "qwen":
            return {
                "provider": "qwen",
                "api_key": self.qwen_api_key,
                "base_url": self.qwen_base_url,
                "model": self.qwen_model,
            }
        elif self.llm_provider == "siliconflow":
            return {
                "provider": "siliconflow",
                "api_key": self.siliconflow_api_key,
                "base_url": self.siliconflow_base_url,
                "model": self.siliconflow_model,
            }
        else:
            return {
                "provider": "qwen",
                "api_key": self.qwen_api_key,
                "base_url": self.qwen_base_url,
                "model": self.qwen_model,
            }
    
    def validate_config(self) -> list[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        # Check LLM API key based on provider
        llm_config = self.get_llm_config()
        if not llm_config.get("api_key"):
            errors.append(f"{self.llm_provider.upper()}_API_KEY is not set")
        
        # Check Amap API key
        if not self.amap_maps_api_key:
            errors.append("AMAP_MAPS_API_KEY is not set")
        
        return errors
    
    def get_openai_client_config(self) -> dict:
        """Get configuration for OpenAI-compatible client."""
        config = self.get_llm_config()
        return {
            "api_key": config["api_key"],
            "base_url": config.get("base_url"),
            "model": config["model"],
        }


# Global settings instance
settings = Settings()




