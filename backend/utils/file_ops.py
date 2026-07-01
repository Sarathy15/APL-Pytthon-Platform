import os

class EnvLoader:
    @staticmethod
    def get(key: str, default: str = None):
        return os.getenv(key, default)

class FileHandler:
    @staticmethod
    def save_temp(content: str, filename: str):
        path = f"/tmp/{filename}"
        with open(path, "w") as f:
            f.write(content)
        return path
