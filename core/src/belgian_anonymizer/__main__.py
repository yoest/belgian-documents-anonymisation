import logging

import uvicorn

from belgian_anonymizer.api import create_app
from belgian_anonymizer.config import AppConfig


class ApiServer:
    def __init__(self, config: AppConfig) -> None:
        self._config = config

    def run(self) -> None:
        logging.basicConfig(
            level=self._config.logging.level, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
        )
        # Single worker: the document store lives in memory and the model is loaded once
        uvicorn.run(
            create_app(self._config),
            host=self._config.api.host,
            port=self._config.api.port,
            log_level=self._config.logging.level.lower(),
            workers=1,
        )


if __name__ == "__main__":
    ApiServer(AppConfig.load()).run()
