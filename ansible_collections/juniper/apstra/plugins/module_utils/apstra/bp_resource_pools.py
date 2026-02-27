# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

"""Blueprint resource pool / resource group utilities.

Provides reusable helpers for managing resource groups within an
Apstra blueprint via ``raw_request``.  Follows the same API-based
pattern as ``bp_property_set.py``.

API endpoints::

    GET   /api/blueprints/{bp_id}/resource_groups                       → list all
    GET   /api/blueprints/{bp_id}/resource_groups/{type}/{name}         → get one
    PUT   /api/blueprints/{bp_id}/resource_groups/{type}/{name}         → update

Usage inside a module::

    from ansible_collections.juniper.apstra.plugins.module_utils.apstra.bp_resource_pools import (
        list_resource_groups,
        get_resource_group,
        assign_resource_pools,
        unassign_resource_pools,
    )
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type


# ──────────────────────────────────────────────────────────────────
#  Collection operations
# ──────────────────────────────────────────────────────────────────


def list_resource_groups(client_factory, blueprint_id):
    """List all resource groups in a blueprint.

    Calls ``GET /api/blueprints/{bp_id}/resource_groups`` via
    ``raw_request``.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.

    Returns:
        list[dict]: List of resource group dicts.  Returns empty list
        when no groups exist.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(f"/blueprints/{blueprint_id}/resource_groups")
    if resp.status_code == 200:
        data = resp.json()
        return data.get("items", [])
    return []


def get_resource_groups_by_type(client_factory, blueprint_id, resource_type):
    """Get resource groups filtered by type.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        resource_type: The resource type to filter by
            (e.g., ``'asn'``, ``'ip'``, ``'vni'``).

    Returns:
        list[dict]: Matching resource group dicts.
    """
    all_groups = list_resource_groups(client_factory, blueprint_id)
    return [g for g in all_groups if g.get("type") == resource_type]


# ──────────────────────────────────────────────────────────────────
#  Single resource-group operations
# ──────────────────────────────────────────────────────────────────


def get_resource_group(client_factory, blueprint_id, resource_type, group_name):
    """Get a specific resource group by type and name.

    Calls ``GET /api/blueprints/{bp_id}/resource_groups/{type}/{name}``
    via ``raw_request``.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        resource_type: The resource type (e.g., ``'asn'``, ``'ip'``).
        group_name: The resource group name.

    Returns:
        dict or None: The resource group dict, or *None* if not found.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(
        f"/blueprints/{blueprint_id}/resource_groups/{resource_type}/{group_name}"
    )
    if resp.status_code == 200:
        return resp.json()
    return None


def update_resource_group(
    client_factory, blueprint_id, resource_type, group_name, data
):
    """Update a resource group (PUT).

    Calls ``PUT /api/blueprints/{bp_id}/resource_groups/{type}/{name}``
    via ``raw_request``.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        resource_type: The resource type.
        group_name: The resource group name.
        data: The update payload (e.g., ``{'pool_ids': [...]}``).

    Returns:
        dict or None: The API response.

    Raises:
        Exception: If the update fails.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(
        f"/blueprints/{blueprint_id}/resource_groups/{resource_type}/{group_name}",
        "PUT",
        data=data,
    )
    if resp.status_code not in (200, 202, 204):
        raise Exception(
            f"Failed to update resource group: {resp.status_code} {resp.text}"
        )
    try:
        return resp.json()
    except Exception:
        return None


# ──────────────────────────────────────────────────────────────────
#  Convenience helpers
# ──────────────────────────────────────────────────────────────────


def assign_resource_pools(
    client_factory, blueprint_id, resource_type, group_name, pool_ids
):
    """Assign resource pools to a resource group.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        resource_type: The resource type.
        group_name: The resource group name.
        pool_ids: List of pool IDs to assign.

    Returns:
        dict: The updated resource group.
    """
    return update_resource_group(
        client_factory,
        blueprint_id,
        resource_type,
        group_name,
        {"pool_ids": pool_ids},
    )


def unassign_resource_pools(client_factory, blueprint_id, resource_type, group_name):
    """Unassign all resource pools from a resource group.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        resource_type: The resource type.
        group_name: The resource group name.

    Returns:
        dict: The updated resource group.
    """
    return assign_resource_pools(
        client_factory, blueprint_id, resource_type, group_name, []
    )
