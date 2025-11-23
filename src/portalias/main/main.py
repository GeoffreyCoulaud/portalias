import logging
import logging.config as logging_config
import sys
from os import getenv
from time import sleep

from docker import DockerClient

from portalias.main.services.docker_service import DockerService
from portalias.main.services.iptables_service import IptablesService


def mgetenv(name: str) -> str:
    """Get an environment variable or exit if it is not set"""
    if (value := getenv(name)) is None:
        logging.critical("Environment variable %s is required", name)
        sys.exit(1)
    return value


class Application:
    __interval: int
    __docker_service: DockerService
    __iptables_service: IptablesService

    def _setup_logging(self) -> None:
        log_level = (
            environment_log_level
            if (environment_log_level := getenv("LOG_LEVEL"))
            in logging.getLevelNamesMapping()
            else "INFO"
        )
        logging_config.dictConfig(
            {
                "version": 1,
                "formatters": {
                    "default": {
                        "format": "%(asctime)s [%(name)s] [%(levelname)s] %(message)s",
                    }
                },
                "root": {"level": log_level},
            }
        )

    def _setup(self) -> None:
        """Setup the application"""
        self._setup_logging()
        self.__interval = int(mgetenv("INTERVAL"))
        self.__docker_service = DockerService(
            client=DockerClient.from_env(),
        )
        self.__iptables_service = IptablesService(
            rules_id=mgetenv("RULES_ID"),
            dry_run=getenv("DRY_RUN", "false") != "false",
        )

    def _loop(self) -> None:
        """Function called in a loop to check for changes in the forwarded port"""
        port_aliases = self.__docker_service.get_port_aliases()
        for port_alias in port_aliases:
            logging.debug("Port alias: %s", port_alias)
        self.__iptables_service.set_port_aliases(port_aliases)

    def run(self) -> None:
        """App entry point, in charge of setting up the app and starting the loop"""
        self._setup()
        while True:
            self._loop()
            sleep(self.__interval)


if __name__ == "__main__":
    Application().run()
