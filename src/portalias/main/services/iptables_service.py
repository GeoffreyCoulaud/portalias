import logging
import re
import subprocess
from subprocess import CompletedProcess
from typing import cast

from portalias.main.models.port_alias import PortAlias


class IptablesService:
    __COMMENT_MAX_SIZE: int = 256  # Defined by iptables
    __COMMENT_PREFIX: str = "portalias."

    __rules_id: str
    __dry_run: bool

    def _get_rules_id_max_size(self) -> int:
        return self.__COMMENT_MAX_SIZE - len(self.__COMMENT_PREFIX)

    def _get_identifying_comment(self) -> str:
        return f"{self.__COMMENT_PREFIX}{self.__rules_id}"

    def __init__(self, rules_id: str, dry_run: bool = True) -> None:
        if len(rules_id) > (max_size := self._get_rules_id_max_size()):
            raise ValueError(f"RULES_ID exceeds max size {max_size}")
        self.__rules_id = rules_id
        self.__dry_run = dry_run

    def _run_command(self, command: list[str]) -> CompletedProcess:
        result = subprocess.run(
            args=command,
            check=False,  # Manual check instead
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            message_parts = [
                "Command exited with non-zero code.",
                "command: %s",
                "stdout: %s",
                "stderr: %s",
            ]
            logging.error(
                "\n".join(message_parts),
                " ".join(command),
                result.stdout,
                result.stderr,
            )
            raise subprocess.CalledProcessError(
                returncode=result.returncode,
                cmd=command,
                output=result.stdout,
                stderr=result.stderr,
            )
        return result

    def _get_all_rule_numbers(self) -> list[PortAlias]:
        """Get all iptables rules handled by portalias"""
        # fmt: off
        command = [
            "iptables", 
            "-t", "nat", 
            "-L", "PREROUTING", 
            "--line-numbers", 
            "-n",
        ]
        # fmt: on
        result = self._run_command(command=command)
        needle = f"/* {self._get_identifying_comment()} */"
        numbers = []
        for line in cast(list[str], result.stdout.splitlines()[2:]):
            if needle in line:
                n = int(line.split(" ")[0])
                formatted_line = re.sub(r"\s+", " ", line)
                logging.debug('Found rule %d: "%s"', n, formatted_line)
                numbers.append(n)
        return numbers

    def _remove_rules(self, rule_numbers: list[int]) -> None:
        """Remove all port aliases handled by portalias"""
        for n in sorted(rule_numbers, reverse=True):
            command = ["iptables", "-t", "nat", "-D", "PREROUTING", str(n)]
            logging.debug("Removing rule %d", n)
            if not self.__dry_run:
                self._run_command(command=command)

    def _add_rule(self, protocol: str, ip_address: str, port: int, alias: int) -> None:
        # fmt: off
        command = [
            "iptables",
            "-t", "nat",
            "-A", "PREROUTING",
            "-p", protocol,
            "-d", ip_address,
            "--dport", str(alias),
            "-j", "DNAT",
            "--to-destination", f"{ip_address}:{port}",
            "-m", "comment",
            "--comment", self._get_identifying_comment(),
        ]
        # fmt: on
        logging.debug('Adding rule: "%s"', " ".join(command))
        if not self.__dry_run:
            self._run_command(command=command)

    def _add_port_aliases(self, port_aliases: list[PortAlias]) -> None:
        """Add port aliases to iptables"""
        for port_alias in port_aliases:
            for protocol in port_alias["protocols"]:
                for alias in port_alias["aliases"]:
                    self._add_rule(
                        protocol=protocol,
                        ip_address=port_alias["ip_address"],
                        port=port_alias["port"],
                        alias=alias,
                    )

    def set_port_aliases(self, port_aliases: list[PortAlias]) -> None:
        """Set port aliases"""
        logging.debug("Setting port aliases")

        # Get all rules handled by portalias
        logging.debug("Getting index of all rules handled by portalias")
        rule_numbers = self._get_all_rule_numbers()

        # Remove all existing rules
        logging.debug(
            "Removing all exising rules with the identifying comment: %s",
            self._get_identifying_comment(),
        )
        self._remove_rules(rule_numbers=rule_numbers)

        # Add new port aliases
        logging.debug("Adding new port aliases")
        self._add_port_aliases(port_aliases)
