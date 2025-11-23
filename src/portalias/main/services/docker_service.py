from typing import cast
from docker.client import DockerClient
from docker.models.containers import Container
from docker.models.networks import Network

from portalias.main.models.port_alias import PortAlias


class DockerService:
    __client: DockerClient

    def _create_client(self) -> None:
        self.__client = DockerClient.from_env()

    def _get_enabled_networks(self) -> list[Network]:
        if not self.__client:
            self._create_client()
        return self.__client.networks.list(filters={"label": "portalias.enabled=true"})

    def _is_container_enabled(self, container: Container) -> bool:
        return 0 < len(
            [label for label in container.labels if label.startswith("portalias.")]
        )

    def _get_enabled_containers_on_network(self, network: Network) -> list[Container]:
        return [
            container
            for container in network.containers
            if self._is_container_enabled(container)
        ]

    def _get_container_ip_on_network(
        self,
        container: Container,
        network: Network,
    ) -> str:
        return cast(
            str,
            container.attrs["NetworkSettings"]["Networks"][network.name]["IPAddress"],
        )

    def _get_source_port_from_label(self, label: str) -> tuple[int, list[str]]:
        parts = label.split(".")
        port = parts[1]
        try:
            protocols_raw = parts[2]
        except IndexError:
            protocols_raw = "tcp"
        protocols = protocols_raw.split(",")
        for protocol in protocols:
            if protocol not in ("tcp", "udp"):
                raise ValueError(f"Invalid protocol: {protocol}")
        if len(protocols) == 0:
            protocols.append("tcp")
        return (int(port), protocols)

    def _get_aliases_from_label_value(self, value: str) -> list[int]:
        return [int(port) for port in value.split(",")]

    def _get_container_portalias_labels(self, container: Container) -> dict[str, str]:
        return {
            label: value
            for label, value in container.labels.items()
            if label.startswith("portalias.")
        }

    def _get_portalias_from_label(
        self, label: str, value: str, ip_address: str
    ) -> PortAlias:
        port, protocols = self._get_source_port_from_label(label)
        aliases = self._get_aliases_from_label_value(value)
        return PortAlias(
            ip_address=ip_address,
            port=port,
            aliases=aliases,
            protocols=protocols,
        )

    def get_port_aliases(self) -> list[PortAlias]:
        """Get all the port aliases from the docker API"""
        port_aliases = []
        for network in self._get_enabled_networks():
            network.reload()
            for container in self._get_enabled_containers_on_network(network):
                container.reload()
                ip_address = self._get_container_ip_on_network(container, network)
                labels = self._get_container_portalias_labels(container)
                for label, value in labels.items():
                    port_alias = self._get_portalias_from_label(
                        label=label,
                        value=value,
                        ip_address=ip_address,
                    )
                    port_aliases.append(port_alias)
        return port_aliases
