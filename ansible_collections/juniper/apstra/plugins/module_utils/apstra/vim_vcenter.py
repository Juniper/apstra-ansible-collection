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

**Apstra VIM Architecture — vcenter vs NSX:**

``vcenter`` VIM type
    The VIM itself IS the direct connection to VMware vCenter.
    Create via ``POST /virtual-infra-managers`` with
    ``virtual_infra_type: "vcenter"`` and ``management_ip: "<vcenter-ip>"``.
    Apstra connects directly and populates ``connection_state`` and
    ``vcenter_info`` on the VIM object.
    The ``/vcenters`` sub-resource endpoint is **read-only** for
    vcenter-type VIMs — ``POST /vcenters`` returns HTTP 422
    ("Vcenters can be added to virtual infra manager of the type NSX
    only").  Use the global VIM create/update APIs instead.

``nsx`` VIM type
    The VIM IS a connection to VMware NSX Manager.  NSX in turn
    manages multiple vCenters.  After creating the NSX VIM you
    register individual vCenter instances as sub-resources via
    ``POST /virtual-infra-managers/{nsx-id}/vcenters``.
    This is the only context where ``create_vim_vcenter`` succeeds.

API endpoints::

    # Global VIM
    GET    /api/virtual-infra-managers                                   → list all VIMs
    POST   /api/virtual-infra-managers                                   → create VIM
    GET    /api/virtual-infra-managers/{mgr_id}                          → get VIM
    PATCH  /api/virtual-infra-managers/{mgr_id}                          → patch VIM
    PUT    /api/virtual-infra-managers/{mgr_id}                          → replace VIM
    DELETE /api/virtual-infra-managers/{mgr_id}                          → delete VIM

    # vCenter sub-resource (NSX VIMs only for CREATE)
    GET    /api/virtual-infra-managers/{mgr_id}/vcenters                 → list
    POST   /api/virtual-infra-managers/{mgr_id}/vcenters                 → create (NSX only)
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
        get_vim_connection_state,
        wait_for_vim_connection,
    )
"""

from __future__ import absolute_import, division, print_function

import time

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
    """Find a vCenter by management_ip within a VIM.

    Iterates the vCenter list and returns the first entry whose
    ``management_ip`` field matches the supplied value (case-sensitive).
    The parameter is still named ``hostname`` for API backward compatibility.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        manager_id: The VIM UUID.
        hostname: The vCenter management_ip value to search for.

    Returns:
        dict or None: The matching vCenter dict, or ``None`` if not found.
    """
    items = list_vim_vcenters(client_factory, manager_id)
    for item in items:
        if isinstance(item, dict) and item.get("management_ip") == hostname:
            return item
    return None


def get_vim_connection_state(client_factory, vim_id):
    """Return the current connection_state and full VIM dict for a VIM.

    Calls ``GET /api/virtual-infra-managers/{vim_id}`` and extracts
    ``connection_state`` from the (possibly items-wrapped) response.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        vim_id: The VIM UUID.

    Returns:
        tuple[str, dict]: ``(connection_state, vim_dict)`` where
        ``connection_state`` is one of ``"connected"``, ``"disconnected"``,
        ``"unknown"``, or ``"error"``, and ``vim_dict`` is the raw VIM
        object from the API (may be ``{}`` on error).
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(f"{_BASE}/{vim_id}")
    if resp.status_code != 200:
        return "unknown", {}
    data = resp.json()
    # API may return {"items": [...]} wrapper or a bare dict
    if isinstance(data, dict) and "items" in data:
        items = data.get("items", [])
        vim = items[0] if items else {}
    else:
        vim = data
    state = vim.get("connection_state", "unknown")
    return state, vim


def wait_for_vim_connection(client_factory, vim_id, timeout=60, interval=5):
    """Poll a VIM until ``connection_state`` is ``"connected"`` or timeout.

    Useful after creating a vcenter-type VIM with real credentials to
    confirm Apstra has successfully authenticated and collected vCenter
    inventory before proceeding with tests that depend on live data.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        vim_id: The VIM UUID.
        timeout: Maximum seconds to wait (default ``60``).
        interval: Polling interval in seconds (default ``5``).

    Returns:
        tuple[bool, dict]: ``(True, vim_dict)`` if connected within
        timeout, ``(False, vim_dict)`` otherwise.  ``vim_dict`` is the
        last-seen VIM object from the API.
    """
    elapsed = 0
    vim = {}
    while elapsed < timeout:
        state, vim = get_vim_connection_state(client_factory, vim_id)
        if state == "connected":
            return True, vim
        if state in ("error", "failed"):
            return False, vim
        time.sleep(interval)
        elapsed += interval
    # One final check
    state, vim = get_vim_connection_state(client_factory, vim_id)
    return state == "connected", vim
