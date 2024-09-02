from pydantic import BaseSettings, HttpUrl


class Config(BaseSettings):
    api_url: HttpUrl

    class Config:
        env_file = '.env'


config = Config()
