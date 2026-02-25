# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

"""
Reusable blueprint utility functions for Apstra Ansible modules.

This module provides helper functions for common blueprint operations
such as managing resource groups and configlets. These utilities are
designed to be imported by Ansible modules to avoid code duplication
and to ensure consistent blueprint API interactions across the collection.

Usage::

    from ansible_collections.juniper.apstra.plugins.module_utils.apstra.blueprint import (
        list_resource_groups,
        get_resource_group,
        assign_resource_pools,
        list_blueprint_configlets,
        get_blueprint_configlet,
    )
"""


# ── Blueprint Resource Group Utilities ──────────────────────────────────


def list_resource_groups(client_factory, blueprint_id):
    """
    List all resource groups in a blueprint.

    :param client_factory: An ApstraClientFactory instance.
    :param blueprint_id: The blueprint ID.
    :return: A list of resource group dicts.
    """
    base_client = client_factory.get_base_client()
    resp = base_client.raw_request(f"/blueprints/{blueprint_id}/resource_groups")
    if resp.status_code == 200:
        data = resp.json()
        return data.get("items", [])
    return []


def get_resource_groups_by_type(client_factory, blueprint_id, resource_type):
    """
    Get resource groups filtered by type.

    :param client_factory: An ApstraClientFactory instance.
    :param blueprint_id: The blueprint ID.
    :param resource_type: The resource type to filter by (e.g., 'asn', 'ip', 'vni').
    :return: A list of matching resource group dicts.
    """
    all_groups = list_resource_groups(client_factory, blueprint_id)
    return [g for g in all_groups if g.get("type") == resource_type]


def get_resource_group(client_factory, blueprint_id, resource_type, group_name):
    """
    Get a specific resource group.

    :param client_factory: An ApstraClientFactory instance.
    :param blueprint_id: The blueprint ID.
    :param resource_type: The resource type (e.g., 'asn', 'ip').
    :param group_name: The resource group name.
    :return: The resource group dict, or None.
    """
    ra_client = client_factory.get_resource_allocation_client()
    try:
        return (
            ra_client.blueprints[blueprint_id]
            .resource_groups[resource_type][group_name]
            .get()
        )
    except Exception:
        return None


def update_resource_group(
    client_factory, blueprint_id, resource_type, group_name, data
):
    """
    Update a resource group.

    :param client_factory: An ApstraClientFactory instance.
    :param blueprint_id: The blueprint ID.
    :param resource_type: The resource type.
    :param group_name: The resource group name.
    :param data: The update data (e.g., {'pool_ids': [...]}).
    :return: The updated resource group dict.
    """
    ra_client = client_factory.get_resource_allocation_client()
    return (
        ra_client.blueprints[blueprint_id]
        .resource_groups[resource_type][group_name]
        .update(data)
    )


def assign_resource_pools(
    client_factory, blueprint_id, resource_type, group_name, pool_ids
):
    """
    Assign resource pools to a resource group.

    :param client_factory: An ApstraClientFactory instance.
    :param blueprint_id: The blueprint ID.
    :param resource_type: The resource type.
    :param group_name: The resource group name.
    :param pool_ids: List of pool IDs to assign.
    :return: The updated resource group dict.
    """
    return update_resource_group(
        client_factory,
        blueprint_id,
        resource_type,
        group_name,
        {"pool_ids": pool_ids},
    )


def unassign_resource_pools(client_factory, blueprint_id, resource_type, group_name):
    """
    Unassign all resource pools from a resource group.

    :param client_factory: An ApstraClientFactory instance.
    :param blueprint_id: The blueprint ID.
    :param resource_type: The resource type.
    :param group_name: The resource group name.
    :return: The updated resource group dict.
    """
    return assign_resource_pools(
        client_factory, blueprint_id, resource_type, group_name, []
    )


# ── Blueprint Configlet Utilities ───────────────────────────────────────


def list_blueprint_configlets(client_factory, blueprint_id):
    """
    List all configlets for a blueprint.

    Uses raw_request because the SDK does not expose a dedicated endpoint.

    :param client_factory: An ApstraClientFactory instance.
    :param blueprint_id: The blueprint ID.
    :return: A list of configlet dicts.
    """
    base_client = client_factory.get_base_client()
    resp = base_client.raw_request(f"/blueprints/{blueprint_id}/configlets")
    if resp.status_code == 200:
        data = resp.json()
        return data.get("items", [])
    return []


def get_blueprint_configlet(client_factory, blueprint_id, configlet_id):
    """
    Get a single blueprint configlet by ID.

    :param client_factory: An ApstraClientFactory instance.
    :param blueprint_id: The blueprint ID.
    :param configlet_id: The configlet ID.
    :return: The configlet dict, or None.
    """
    base_client = client_factory.get_base_client()
    resp = base_client.raw_request(
        f"/blueprints/{blueprint_id}/configlets/{configlet_id}"
    )
    if resp.status_code == 200:
        return resp.json()
    return None


def create_blueprint_configlet(client_factory, blueprint_id, body):
    """
    Create a blueprint configlet.

    :param client_factory: An ApstraClientFactory instance.
    :param blueprint_id: The blueprint ID.
    :param body: The configlet body.
    :return: The created configlet dict.
    :raises Exception: If creation fails.
    """
    base_client = client_factory.get_base_client()
    resp = base_client.raw_request(
        f"/blueprints/{blueprint_id}/configlets", "POST", data=body
    )
    if resp.status_code in (200, 201):
        return resp.json()
    raise Exception(
        f"Failed to create blueprint configlet: {resp.status_code} {resp.text}"
    )


def update_blueprint_configlet(client_factory, blueprint_id, configlet_id, body):
    """
    Update a blueprint configlet (PUT).

    :param client_factory: An ApstraClientFactory instance.
    :param blueprint_id: The blueprint ID.
    :param configlet_id: The configlet ID.
    :param body: The update body.
    :raises Exception: If update fails.
    """
    base_client = client_factory.get_base_client()
    resp = base_client.raw_request(
        f"/blueprints/{blueprint_id}/configlets/{configlet_id}", "PUT", data=body
    )
    if resp.status_code not in (200, 202, 204):
        raise Exception(
            f"Failed to update blueprint configlet: {resp.status_code} {resp.text}"
        )
    return None


def delete_blueprint_configlet(client_factory, blueprint_id, configlet_id):
    """
    Delete a blueprint configlet.

    :param client_factory: An ApstraClientFactory instance.
    :param blueprint_id: The blueprint ID.
    :param configlet_id: The configlet ID.
    :raises Exception: If deletion fails.
    """
    base_client = client_factory.get_base_client()
    resp = base_client.raw_request(
        f"/blueprints/{blueprint_id}/configlets/{configlet_id}", "DELETE"
    )
    if resp.status_code not in (200, 202, 204):
        raise Exception(
            f"Failed to delete blueprint configlet: {resp.status_code} {resp.text}"
        )


def find_blueprint_configlet_by_label(client_factory, blueprint_id, label):
    """
    Find a blueprint configlet by label.

    :param client_factory: An ApstraClientFactory instance.
    :param blueprint_id: The blueprint ID.
    :param label: The configlet label.
    :return: The configlet dict, or None.
    """
    items = list_blueprint_configlets(client_factory, blueprint_id)
    for item in items:
        if isinstance(item, dict) and item.get("label") == label:
            return item
    return None
