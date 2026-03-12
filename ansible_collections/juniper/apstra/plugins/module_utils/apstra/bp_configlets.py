# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

"""Blueprint configlet utilities.

Provides reusable helpers for managing configlets within an Apstra
blueprint via ``raw_request``.  The SDK does not expose a dedicated
configlet endpoint on the base or l3clos clients, so this module
uses the REST API directly — following the same pattern as
``bp_property_set.py``.

API endpoints::

    GET    /api/blueprints/{bp_id}/configlets              → list
    POST   /api/blueprints/{bp_id}/configlets              → create
    GET    /api/blueprints/{bp_id}/configlets/{cfg_id}     → get
    PUT    /api/blueprints/{bp_id}/configlets/{cfg_id}     → update
    DELETE /api/blueprints/{bp_id}/configlets/{cfg_id}     → delete

Usage inside a module::

    from ansible_collections.juniper.apstra.plugins.module_utils.apstra.bp_configlets import (
        list_blueprint_configlets,
        get_blueprint_configlet,
        create_blueprint_configlet,
        update_blueprint_configlet,
        delete_blueprint_configlet,
        find_blueprint_configlet_by_label,
    )
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type


# ──────────────────────────────────────────────────────────────────
#  Collection operations
# ──────────────────────────────────────────────────────────────────


def list_blueprint_configlets(client_factory, blueprint_id):
    """List all configlets in a blueprint.

    Calls ``GET /api/blueprints/{bp_id}/configlets`` via
    ``raw_request``.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.

    Returns:
        list[dict]: List of configlet dicts.  Returns empty list on
        error or when no configlets exist.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(f"/blueprints/{blueprint_id}/configlets")
    if resp.status_code == 200:
        data = resp.json()
        return data.get("items", [])
    return []


# ──────────────────────────────────────────────────────────────────
#  Single resource operations
# ──────────────────────────────────────────────────────────────────


def get_blueprint_configlet(client_factory, blueprint_id, configlet_id):
    """Get a single blueprint configlet by ID.

    Calls ``GET /api/blueprints/{bp_id}/configlets/{cfg_id}`` via
    ``raw_request``.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        configlet_id: The configlet ID within the blueprint.

    Returns:
        dict or None: The configlet dict, or *None* if not found.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(f"/blueprints/{blueprint_id}/configlets/{configlet_id}")
    if resp.status_code == 200:
        return resp.json()
    return None


def create_blueprint_configlet(client_factory, blueprint_id, body):
    """Create a configlet in a blueprint.

    Calls ``POST /api/blueprints/{bp_id}/configlets`` via
    ``raw_request``.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        body: The configlet body dict (label, condition, configlet, etc.).

    Returns:
        dict: The created configlet response (typically contains ``id``).

    Raises:
        Exception: If creation fails.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(f"/blueprints/{blueprint_id}/configlets", "POST", data=body)
    if resp.status_code in (200, 201):
        return resp.json()
    raise Exception(
        f"Failed to create blueprint configlet: {resp.status_code} {resp.text}"
    )


def update_blueprint_configlet(client_factory, blueprint_id, configlet_id, body):
    """Update (PUT) a blueprint configlet.

    Calls ``PUT /api/blueprints/{bp_id}/configlets/{cfg_id}`` via
    ``raw_request``.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        configlet_id: The configlet ID within the blueprint.
        body: The full update body.

    Raises:
        Exception: If the update fails.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(
        f"/blueprints/{blueprint_id}/configlets/{configlet_id}", "PUT", data=body
    )
    if resp.status_code not in (200, 202, 204):
        raise Exception(
            f"Failed to update blueprint configlet: {resp.status_code} {resp.text}"
        )
    return None


def delete_blueprint_configlet(client_factory, blueprint_id, configlet_id):
    """Delete a blueprint configlet.

    Calls ``DELETE /api/blueprints/{bp_id}/configlets/{cfg_id}`` via
    ``raw_request``.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        configlet_id: The configlet ID within the blueprint.

    Raises:
        Exception: If deletion fails.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(
        f"/blueprints/{blueprint_id}/configlets/{configlet_id}", "DELETE"
    )
    if resp.status_code not in (200, 202, 204):
        raise Exception(
            f"Failed to delete blueprint configlet: {resp.status_code} {resp.text}"
        )


# ──────────────────────────────────────────────────────────────────
#  Convenience helpers
# ──────────────────────────────────────────────────────────────────


def find_blueprint_configlet_by_label(client_factory, blueprint_id, label):
    """Find a blueprint configlet by its label.

    Iterates the configlet list and returns the first match.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        label: The configlet label to search for.

    Returns:
        dict or None: The matching configlet dict, or *None*.
    """
    items = list_blueprint_configlets(client_factory, blueprint_id)
    for item in items:
        if isinstance(item, dict) and item.get("label") == label:
            return item
    return None
