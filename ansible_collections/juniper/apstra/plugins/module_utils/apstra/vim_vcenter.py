# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

"""Virtual Infra Manager — vCenter sub-resource utilities.

Provides reusable helpers for managing vCenter instances within an
Apstra Virtual Infra Manager (VIM) via ``raw_request``.  The SDK
exposes ``list()`` and ``create()`` on the ``vcenters`` collection
but does **not** define a ``/{vcenter_id}`` sub-resource, so the
individual GET / PUT / PATCH / DELETE operations must be performed
directly against the REST API — following the same pattern as
``bp_configlets.py`` and ``bp_property_set.py``.

API endpoints::

    GET    /api/virtual-infra-managers/{mgr_id}/vcenters                 → list
    POST   /api/virtual-infra-managers/{mgr_id}/vcenters                 → create
    GET    /api/virtual-infra-managers/{mgr_id}/vcenters/{vcenter_id}    → get
    PUT    /api/virtual-infra-managers/{mgr_id}/vcenters/{vcenter_id}    → update
    PATCH  /api/virtual-infra-managers/{mgr_id}/vcenters/{vcenter_id}    → patch
    DELETE /api/virtual-infra-managers/{mgr_id}/vcenters/{vcenter_id}    → delete

Usage inside a module::

    from ansible_collections.juniper.apstra.plugins.module_utils.apstra.vim_vcenter import (
        list_vim_vcenters,
        get_vim_vcenter,
        create_vim_vcenter,
        update_vim_vcenter,
        patch_vim_vcenter,
        delete_vim_vcenter,
        find_vim_vcenter_by_hostname,
    )
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

# Base path for all vCenter sub-resource calls.
_BASE = "/virtual-infra-managers"


# ──────────────────────────────────────────────────────────────────
#  Collection operations
# ──────────────────────────────────────────────────────────────────


def list_vim_vcenters(client_factory, manager_id):
    """List all vCenters registered under a Virtual Infra Manager.

    Calls ``GET /api/virtual-infra-managers/{mgr_id}/vcenters`` via
    ``raw_request``.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        manager_id: The VIM UUID.

    Returns:
        list[dict]: List of vCenter dicts.  Returns empty list if
        none exist or on error.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(f"{_BASE}/{manager_id}/vcenters")
    if resp.status_code == 200:
        data = resp.json()
        # API may return {"items": [...]} or a bare list
        if isinstance(data, list):
            return data
        return data.get("items", [])
    return []


def create_vim_vcenter(client_factory, manager_id, body):
    """Create a vCenter instance under a Virtual Infra Manager.

    Calls ``POST /api/virtual-infra-managers/{mgr_id}/vcenters`` via
    ``raw_request``.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        manager_id: The VIM UUID.
        body: The vCenter configuration dict.

    Returns:
        dict: The created vCenter response (typically contains ``id``).

    Raises:
        Exception: If creation fails.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(f"{_BASE}/{manager_id}/vcenters", "POST", data=body)
    if resp.status_code in (200, 201):
        return resp.json()
    raise Exception(
        f"Failed to create vCenter under VIM '{manager_id}': "
        f"{resp.status_code} {resp.text}"
    )


# ──────────────────────────────────────────────────────────────────
#  Single resource operations
# ──────────────────────────────────────────────────────────────────


def get_vim_vcenter(client_factory, manager_id, vcenter_id):
    """Get a single vCenter by ID from a Virtual Infra Manager.

    Calls ``GET /api/virtual-infra-managers/{mgr_id}/vcenters/{vcenter_id}``
    via ``raw_request``.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        manager_id: The VIM UUID.
        vcenter_id: The vCenter ID.

    Returns:
        dict or None: The vCenter dict, or ``None`` if not found.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(f"{_BASE}/{manager_id}/vcenters/{vcenter_id}")
    if resp.status_code == 200:
        return resp.json()
    return None


def update_vim_vcenter(client_factory, manager_id, vcenter_id, body):
    """Fully replace (PUT) a vCenter under a Virtual Infra Manager.

    Calls ``PUT /api/virtual-infra-managers/{mgr_id}/vcenters/{vcenter_id}``
    via ``raw_request``.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        manager_id: The VIM UUID.
        vcenter_id: The vCenter ID.
        body: Full replacement body.

    Returns:
        dict or None: The updated vCenter response, or ``None`` if
        the server returns 204.

    Raises:
        Exception: If the PUT request fails.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(
        f"{_BASE}/{manager_id}/vcenters/{vcenter_id}", "PUT", data=body
    )
    if resp.status_code not in (200, 201, 202, 204):
        raise Exception(
            f"Failed to replace vCenter '{vcenter_id}' under VIM '{manager_id}': "
            f"{resp.status_code} {resp.text}"
        )
    if resp.status_code == 204 or not resp.text:
        return None
    return resp.json()


def patch_vim_vcenter(client_factory, manager_id, vcenter_id, body):
    """Partially update (PATCH) a vCenter under a Virtual Infra Manager.

    Calls ``PATCH /api/virtual-infra-managers/{mgr_id}/vcenters/{vcenter_id}``
    via ``raw_request``.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        manager_id: The VIM UUID.
        vcenter_id: The vCenter ID.
        body: The partial update body (only fields to change).

    Returns:
        dict or None: The updated vCenter response, or ``None`` if
        the server returns 204.

    Raises:
        Exception: If the PATCH request fails.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(
        f"{_BASE}/{manager_id}/vcenters/{vcenter_id}", "PATCH", data=body
    )
    if resp.status_code not in (200, 201, 202, 204):
        raise Exception(
            f"Failed to patch vCenter '{vcenter_id}' under VIM '{manager_id}': "
            f"{resp.status_code} {resp.text}"
        )
    if resp.status_code == 204 or not resp.text:
        return None
    return resp.json()


def delete_vim_vcenter(client_factory, manager_id, vcenter_id):
    """Delete a vCenter from a Virtual Infra Manager.

    Calls ``DELETE /api/virtual-infra-managers/{mgr_id}/vcenters/{vcenter_id}``
    via ``raw_request``.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        manager_id: The VIM UUID.
        vcenter_id: The vCenter ID.

    Raises:
        Exception: If the DELETE request fails.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(f"{_BASE}/{manager_id}/vcenters/{vcenter_id}", "DELETE")
    if resp.status_code not in (200, 202, 204):
        raise Exception(
            f"Failed to delete vCenter '{vcenter_id}' under VIM '{manager_id}': "
            f"{resp.status_code} {resp.text}"
        )


# ──────────────────────────────────────────────────────────────────
#  Convenience helpers
# ──────────────────────────────────────────────────────────────────


def find_vim_vcenter_by_hostname(client_factory, manager_id, hostname):
    """Find a vCenter by hostname within a VIM.

    Iterates the vCenter list and returns the first entry whose
    ``hostname`` field matches the supplied value (case-sensitive).

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        manager_id: The VIM UUID.
        hostname: The vCenter hostname to search for.

    Returns:
        dict or None: The matching vCenter dict, or ``None`` if not found.
    """
    items = list_vim_vcenters(client_factory, manager_id)
    for item in items:
        if isinstance(item, dict) and item.get("hostname") == hostname:
            return item
    return None
