# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

"""Blueprint EVPN Interconnect Domain utilities.

Provides reusable helpers for managing EVPN Interconnect Domains
(``evpn_interconnect_group`` in the Apstra API) within a blueprint
using the AOS SDK ``evpn_interconnect_groups`` resource.

Usage inside a module::

    from ansible_collections.juniper.apstra.plugins.module_utils.apstra.bp_interconnect_domain import (
        list_interconnect_domains,
        get_interconnect_domain,
        create_interconnect_domain,
        update_interconnect_domain,
        delete_interconnect_domain,
        find_interconnect_domain_by_label,
    )
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type


def _get_bp_resource(client_factory, blueprint_id):
    """Return the SDK ``evpn_interconnect_groups`` resource for a blueprint."""
    client = client_factory.get_l3clos_client()
    return client.blueprints[blueprint_id].evpn_interconnect_groups


# ──────────────────────────────────────────────────────────────────
#  Collection operations
# ──────────────────────────────────────────────────────────────────


def list_interconnect_domains(client_factory, blueprint_id):
    """List all EVPN Interconnect Domains in a blueprint.

    Returns:
        list[dict]: List of interconnect domain dicts.  Returns an
        empty list when none exist.
    """
    resource = _get_bp_resource(client_factory, blueprint_id)
    result = resource.list()
    if result is None:
        return []
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        return list(result.values())
    return []


def find_interconnect_domain_by_label(client_factory, blueprint_id, label):
    """Find an interconnect domain by its label.

    Returns:
        dict or None: The matching domain dict, or *None*.
    """
    domains = list_interconnect_domains(client_factory, blueprint_id)
    for domain in domains:
        if domain.get("label") == label:
            return domain
    return None


# ──────────────────────────────────────────────────────────────────
#  Single-object operations
# ──────────────────────────────────────────────────────────────────


def get_interconnect_domain(client_factory, blueprint_id, domain_id):
    """Get a specific EVPN Interconnect Domain.

    Returns:
        dict or None: The domain dict, or *None* if not found.
    """
    resource = _get_bp_resource(client_factory, blueprint_id)
    try:
        return resource[domain_id].get()
    except Exception:
        return None


def _map_body_to_sdk(data):
    """Map user-facing body keys to the SDK parameter names.

    User body uses short names (``route_target``, ``esi_mac``);
    the SDK expects ``interconnect_route_target`` and
    ``interconnect_esi_mac``.
    """
    mapped = {}
    if "label" in data:
        mapped["label"] = data["label"]
    if "route_target" in data:
        mapped["interconnect_route_target"] = data["route_target"]
    elif "interconnect_route_target" in data:
        mapped["interconnect_route_target"] = data["interconnect_route_target"]
    if "esi_mac" in data:
        mapped["interconnect_esi_mac"] = data["esi_mac"]
    elif "interconnect_esi_mac" in data:
        mapped["interconnect_esi_mac"] = data["interconnect_esi_mac"]
    return mapped


def create_interconnect_domain(client_factory, blueprint_id, data):
    """Create an EVPN Interconnect Domain.

    Returns:
        dict: The API response (typically contains ``id``).
    """
    resource = _get_bp_resource(client_factory, blueprint_id)
    sdk_params = _map_body_to_sdk(data)
    return resource.create(**sdk_params)


def update_interconnect_domain(client_factory, blueprint_id, domain_id, data):
    """Update an EVPN Interconnect Domain (PATCH).

    Returns:
        dict or None: The API response.
    """
    resource = _get_bp_resource(client_factory, blueprint_id)
    sdk_params = _map_body_to_sdk(data)
    return resource[domain_id].update(**sdk_params)


def delete_interconnect_domain(client_factory, blueprint_id, domain_id):
    """Delete an EVPN Interconnect Domain."""
    resource = _get_bp_resource(client_factory, blueprint_id)
    resource[domain_id].delete()
