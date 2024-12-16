from pydantic import HttpUrl
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    api_url: HttpUrl

    class Config:
        env_file = '.env'


config = Config()
