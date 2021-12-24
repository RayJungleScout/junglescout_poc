import dotenv
import os

PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))

class Config():
    REDIS_URL = "redis://localhost:6379/0"

    WECHAT_WORK_TOKEN = "test"
    WECHAT_WORK_AES_KEY = "test"

    def __init__(self) -> None:
        dotenv.load_dotenv(dotenv_path=os.path.join(PROJECT_PATH, '.env'))
        for key, value in os.environ.items():
            if hasattr(self, key):
                if value in ['True', 'False']:
                    value = eval(value)
                setattr(self, key, value)
