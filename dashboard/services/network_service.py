
from __future__ import annotations

from ipaddress import IPv4Address, IPv4Network, ip_network
from typing import Any


class NetworkConfigurationError(ValueError):
    """Raised when a network configuration is invalid."""


def parse_ipv4_network(cidr: str) -> IPv4Network:
    """Parse and validate an IPv4 network in strict mode."""
    try:
        network = ip_network(cidr, strict=True)
    except ValueError as exc:
        raise NetworkConfigurationError(
            f"Invalid network CIDR: {cidr}"
        ) from exc

    if not isinstance(network, IPv4Network):
        raise NetworkConfigurationError("Only IPv4 networks are supported.")

    return network


def allocate_subnets(
        cidr: str,
        subnet_prefix: int = 24,
        count: int = 1,
) -> list[str]:
    """Allocate non-overlapping subnets from a parent IPv4 network."""
    parent = parse_ipv4_network(cidr)

    if not isinstance(subnet_prefix, int) or isinstance(subnet_prefix, bool):
        raise NetworkConfigurationError("subnet_prefix must be an integer.")

    if not isinstance(count, int) or isinstance(count, bool) or count < 1:
        raise NetworkConfigurationError("count must be a positive integer.")

    if not parent.prefixlen <= subnet_prefix <= 32:
        raise NetworkConfigurationError(
            f"Subnet prefix must be between {parent.prefixlen} and 32."
        )

    candidates = parent.subnets(new_prefix=subnet_prefix)
    result: list[str] = []

    for _ in range(count):
        try:
            result.append(str(next(candidates)))
        except StopIteration as exc:
            raise NetworkConfigurationError(
                f"Not enough /{subnet_prefix} subnets in {parent}."
            ) from exc

    return result


def assign_host_ips(cidr: str, count: int) -> list[str]:
    """Assign usable host IPs from a subnet, excluding network/broadcast."""
    network = parse_ipv4_network(cidr)

    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        raise NetworkConfigurationError(
            "count must be a non-negative integer."
        )

    available = network.num_addresses - 2

    if count > available:
        raise NetworkConfigurationError(
            f"Requested {count} hosts, but {network} supports "
            f"at most {available} usable host IPs."
        )

    return [
        str(IPv4Address(int(network.network_address) + offset))
        for offset in range(1, count + 1)
    ]


def build_network_plan(
        cidr: str,
        public_subnets: int = 1,
        private_subnets: int = 1,
        subnet_prefix: int = 24,
        public_hosts_per_subnet: int = 2,
        private_hosts_per_subnet: int = 2,
) -> dict[str, Any]:
    """Build a deterministic network plan without deploying resources."""
    parent = parse_ipv4_network(cidr)

    for name, value in (
            ("public_subnets", public_subnets),
            ("private_subnets", private_subnets),
            ("public_hosts_per_subnet", public_hosts_per_subnet),
            ("private_hosts_per_subnet", private_hosts_per_subnet),
    ):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise NetworkConfigurationError(
                f"{name} must be a non-negative integer."
            )

    if public_subnets + private_subnets < 1:
        raise NetworkConfigurationError(
            "At least one subnet must be configured."
        )

    subnets = allocate_subnets(
        str(parent),
        subnet_prefix=subnet_prefix,
        count=public_subnets + private_subnets,
    )

    public_networks = subnets[:public_subnets]
    private_networks = subnets[public_subnets:]

    def make_segment(
            network_cidr: str,
            segment_type: str,
            host_count: int,
            index: int,
    ) -> dict[str, Any]:
        network = parse_ipv4_network(network_cidr)
        return {
            "name": f"{segment_type}-{index + 1}",
            "type": segment_type,
            "cidr": str(network),
            "hosts": [
                {
                    "name": f"{segment_type}-host-{index + 1}-{host_index + 1}",
                    "ip": ip,
                }
                for host_index, ip in enumerate(
                    assign_host_ips(str(network), host_count)
                )
            ],
        }

    return {
        "network": str(parent),
        "subnet_prefix": subnet_prefix,
        "public_subnets": [
            make_segment(cidr_value, "public", public_hosts_per_subnet, i)
            for i, cidr_value in enumerate(public_networks)
        ],
        "private_subnets": [
            make_segment(cidr_value, "private", private_hosts_per_subnet, i)
            for i, cidr_value in enumerate(private_networks)
        ],
        "deployment_status": "not_deployed",
    }
