
import pytest

from dashboard.services.network_service import (
    NetworkConfigurationError,
    allocate_subnets,
    assign_host_ips,
    build_network_plan,
)


def test_allocate_subnets_without_overlap():
    result = allocate_subnets("10.0.0.0/16", subnet_prefix=24, count=3)

    assert result == [
        "10.0.0.0/24",
        "10.0.1.0/24",
        "10.0.2.0/24",
    ]


def test_assign_host_ips_excludes_network_and_broadcast():
    result = assign_host_ips("192.168.1.0/29", count=3)

    assert result == [
        "192.168.1.1",
        "192.168.1.2",
        "192.168.1.3",
    ]


def test_rejects_invalid_cidr():
    with pytest.raises(NetworkConfigurationError):
        allocate_subnets("10.0.0.1/24")


def test_rejects_insufficient_address_space():
    with pytest.raises(NetworkConfigurationError):
        assign_host_ips("192.168.1.0/29", count=7)


def test_rejects_subnet_prefix_larger_than_parent():
    with pytest.raises(NetworkConfigurationError):
        allocate_subnets("10.0.0.0/24", subnet_prefix=23)


def test_build_network_plan():
    plan = build_network_plan(
        cidr="10.0.0.0/16",
        public_subnets=2,
        private_subnets=2,
        subnet_prefix=24,
        public_hosts_per_subnet=3,
        private_hosts_per_subnet=5,
    )

    assert len(plan["public_subnets"]) == 2
    assert len(plan["private_subnets"]) == 2
    assert plan["public_subnets"][0]["cidr"] == "10.0.0.0/24"
    assert plan["private_subnets"][0]["cidr"] == "10.0.2.0/24"
    assert len(plan["private_subnets"][0]["hosts"]) == 5
    assert plan["deployment_status"] == "not_deployed"


def test_rejects_zero_total_subnets():
    with pytest.raises(NetworkConfigurationError):
        build_network_plan(
            "10.0.0.0/16",
            public_subnets=0,
            private_subnets=0,
        )
