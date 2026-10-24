
from __future__ import annotations

from typing import Any


class TopologyError(ValueError):
    """Raised when a network plan cannot be converted into a topology."""


def build_topology(plan: dict[str, Any]) -> dict[str, Any]:
    """
    Convert a network plan into a graph of nodes and edges.

    Supported nodes:
    - VPC / main network
    - Public and private subnets
    - Virtual hosts

    The result can be consumed by the frontend to display the topology.
    No cloud resources are created.
    """
    if not isinstance(plan, dict):
        raise TopologyError("The network plan must be a dictionary.")

    network_cidr = plan.get("network")
    if not isinstance(network_cidr, str) or not network_cidr:
        raise TopologyError("The network plan must contain a network CIDR.")

    nodes: list[dict[str, Any]] = [
        {
            "id": "vpc",
            "label": f"VPC · {network_cidr}",
            "kind": "network",
            "cidr": network_cidr,
            "status": "planned",
        }
    ]

    edges: list[dict[str, str]] = []
    used_ids = {"vpc"}
    subnet_count = 0
    host_count = 0

    for group_name, expected_type in (
            ("public_subnets", "public"),
            ("private_subnets", "private"),
    ):
        subnets = plan.get(group_name, [])

        if not isinstance(subnets, list):
            raise TopologyError(f"{group_name} must be a list.")

        for subnet in subnets:
            if not isinstance(subnet, dict):
                raise TopologyError("Each subnet must be a dictionary.")

            subnet_name = subnet.get("name")
            subnet_cidr = subnet.get("cidr")

            if not isinstance(subnet_name, str) or not subnet_name.strip():
                raise TopologyError("Each subnet must have a name.")

            if not isinstance(subnet_cidr, str) or not subnet_cidr:
                raise TopologyError(
                    f"Subnet '{subnet_name}' must have a CIDR."
                )

            subnet_id = subnet_name.strip()

            if subnet_id in used_ids:
                raise TopologyError(
                    f"Duplicate topology node ID: '{subnet_id}'."
                )

            used_ids.add(subnet_id)
            subnet_type = subnet.get("type", expected_type)

            nodes.append(
                {
                    "id": subnet_id,
                    "label": subnet_id,
                    "kind": subnet_type,
                    "cidr": subnet_cidr,
                    "status": "planned",
                }
            )

            edges.append(
                {
                    "source": "vpc",
                    "target": subnet_id,
                }
            )
            subnet_count += 1

            hosts = subnet.get("hosts", [])

            if not isinstance(hosts, list):
                raise TopologyError(
                    f"Hosts for subnet '{subnet_id}' must be a list."
                )

            for host in hosts:
                if not isinstance(host, dict):
                    raise TopologyError(
                        f"Invalid host in subnet '{subnet_id}'."
                    )

                host_name = host.get("name")
                host_ip = host.get("ip")

                if not isinstance(host_name, str) or not host_name.strip():
                    raise TopologyError(
                        f"Each host in '{subnet_id}' must have a name."
                    )

                if not isinstance(host_ip, str) or not host_ip:
                    raise TopologyError(
                        f"Host '{host_name}' must have an IP address."
                    )

                host_id = host_name.strip()

                if host_id in used_ids:
                    raise TopologyError(
                        f"Duplicate topology node ID: '{host_id}'."
                    )

                used_ids.add(host_id)

                nodes.append(
                    {
                        "id": host_id,
                        "label": host_id,
                        "kind": "host",
                        "ip": host_ip,
                        "subnet": subnet_id,
                        "status": "planned",
                    }
                )

                edges.append(
                    {
                        "source": subnet_id,
                        "target": host_id,
                    }
                )
                host_count += 1

    return {
        "network": network_cidr,
        "nodes": nodes,
        "edges": edges,
        "statistics": {
            "total_nodes": len(nodes),
            "total_subnets": subnet_count,
            "total_hosts": host_count,
            "public_subnets": sum(
                node["kind"] == "public" for node in nodes
            ),
            "private_subnets": sum(
                node["kind"] == "private" for node in nodes
            ),
        },
        "deployment_status": "not_deployed",
    }
