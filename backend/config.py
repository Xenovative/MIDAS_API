from pydantic_settings import BaseSettings
from typing import List
import secrets


class Settings(BaseSettings):
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Security
    secret_key: str = secrets.token_urlsafe(32)
    
    # LLM API Keys
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    google_api_key: str | None = None
    openrouter_api_key: str | None = None
    volcano_api_key: str | None = None
    volcano_endpoint_id: str | None = None
    volcano_image_endpoint: str | None = None
    volcano_video_endpoint: str | None = None
    volcano_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    deepseek_api_key: str | None = None
    ollama_base_url: str = "http://localhost:11434"
    
    # Image Generation API Keys
    stability_api_key: str | None = None
    replicate_api_key: str | None = None
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./midas.db"
    
    # MCP (Model Context Protocol)
    mcp_config_path: str = "mcp_servers.json"
    
    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"
    }


settings = Settings()
