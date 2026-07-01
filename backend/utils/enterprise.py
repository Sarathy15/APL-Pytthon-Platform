import logging

class Logger:
    @staticmethod
    def get_logger(name: str):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

class Constants:
    MIGRATION_VERSION = "2.4.1"
    SUPPORTED_LANGUAGES = ["APL", "Dyalog"]
    TARGET_PLATFORM = "Python 3.12/NumPy"
