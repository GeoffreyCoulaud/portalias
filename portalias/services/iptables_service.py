import logging
import subprocess
from portalias.models.port_alias import PortAlias


class IptablesService:

    __rules_id: str
    __dry_run: bool

    def __init__(self, rules_id: str, dry_run: bool = True) -> None:
        self.__rules_id = rules_id
        self.__dry_run = dry_run

    def _get_identifying_comment(self) -> str:
        return f"portalias.{self.__rules_id}"

    def _get_all_rule_numbers(self) -> list[PortAlias]:
        """Get all iptables rules handled by portalias"""
        # fmt: off
        command = ["iptables", "-t", "nat", "-L", "PREROUTING", "--line-numbers", "-n", "-v"] # pylint: disable=line-too-long
        # fmt: on
        result = subprocess.run(
            args=command, capture_output=True, check=True, text=True
        )
        rules = []
        for line in result.stdout.splitlines()[2:]:
            if self._get_identifying_comment() in line:
                logging.debug("Found rule: %s", line)
                rules.append(line)
        return [line.split()[0] for line in rules]

    def _remove_rules(self, rule_numbers: list[int]) -> None:
        """Remove all port aliases handled by portalias"""
        for n in sorted(rule_numbers, reverse=True):
            args = ["iptables", "-t", "nat", "-D", "PREROUTING", n]
            logging.debug("Removing rule %d: %s", n, args)
            if not self.__dry_run:
                subprocess.run(args=args, check=True)

    def _add_rule(self, protocol: str, ip_address: str, port: int, alias: int) -> None:
        # fmt: off
        command = [
            "iptables", 
            "-t", "nat", 
            "-A", "PREROUTING", 
            "-p", protocol, 
            "-d", ip_address, 
            "--dport", str(alias), 
            "--comment", self._get_identifying_comment(), 
            "-j", "DNAT", 
            "--to-destination", f"{ip_address}:{port}"
        ]
        # fmt: on
        logging.debug('Adding rule: "%s"', " ".join(command))
        if not self.__dry_run:
            subprocess.run(args=command, check=True)

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
