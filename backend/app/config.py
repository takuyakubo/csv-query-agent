from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    openai_api_key: str
    redis_url: str = "redis://localhost:6379"
    max_file_size: int = 10485760  # 10MB
    allowed_origins: List[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        
    def model_post_init(self, __context):
        if isinstance(self.allowed_origins, str):
            self.allowed_origins = json.loads(self.allowed_origins)


settings = Settings()