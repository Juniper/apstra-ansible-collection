# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

"""IBA (Intent-Based Analytics) probe utilities.

Provides reusable helpers for managing IBA probes within an Apstra
blueprint via ``raw_request``.  The SDK does not expose a dedicated
IBA probe endpoint, so this module uses the REST API directly —
following the same pattern as ``bp_configlets.py``.

API endpoints::

    GET    /api/blueprints/{bp_id}/probes                                  → list probes
    POST   /api/blueprints/{bp_id}/probes                                  → create custom probe
    GET    /api/blueprints/{bp_id}/probes/{probe_id}                       → get probe
    PUT    /api/blueprints/{bp_id}/probes/{probe_id}                       → update probe
    DELETE /api/blueprints/{bp_id}/probes/{probe_id}                       → delete probe

    GET    /api/blueprints/{bp_id}/iba/predefined-probes                   → list predefined probes
    POST   /api/blueprints/{bp_id}/iba/predefined-probes/{name}            → instantiate predefined probe

    GET    /api/blueprints/{bp_id}/iba/dashboards                          → list dashboards
    POST   /api/blueprints/{bp_id}/iba/dashboards                          → create dashboard
    GET    /api/blueprints/{bp_id}/iba/dashboards/{dashboard_id}           → get dashboard
    PUT    /api/blueprints/{bp_id}/iba/dashboards/{dashboard_id}           → update dashboard
    DELETE /api/blueprints/{bp_id}/iba/dashboards/{dashboard_id}           → delete dashboard

Usage inside a module::

    from ansible_collections.juniper.apstra.plugins.module_utils.apstra.iba_probes import (
        list_probes,
        get_probe,
        create_probe,
        create_predefined_probe,
        update_probe,
        delete_probe,
        find_probe_by_label,
        list_predefined_probes,
        get_predefined_probe,
        list_dashboards,
        get_dashboard,
        create_dashboard,
        update_dashboard,
        delete_dashboard,
        find_dashboard_by_label,
    )
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import time


# ──────────────────────────────────────────────────────────────────
#  Probe collection operations
# ──────────────────────────────────────────────────────────────────


def list_probes(client_factory, blueprint_id):
    """List all probes in a blueprint.

    Calls ``GET /api/blueprints/{bp_id}/probes``.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.

    Returns:
        list[dict]: List of probe dicts.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(f"/blueprints/{blueprint_id}/probes")
    if resp.status_code == 200:
        data = resp.json()
        return data.get("items", [])
    return []


# ──────────────────────────────────────────────────────────────────
#  Probe single-resource operations
# ──────────────────────────────────────────────────────────────────


def get_probe(client_factory, blueprint_id, probe_id):
    """Get a single probe by ID.

    Calls ``GET /api/blueprints/{bp_id}/probes/{probe_id}``.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        probe_id: The probe UUID.

    Returns:
        dict or None: The probe dict, or *None* if not found.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(f"/blueprints/{blueprint_id}/probes/{probe_id}")
    if resp.status_code == 200:
        return resp.json()
    return None


def create_probe(client_factory, blueprint_id, body):
    """Create a custom probe in a blueprint.

    Calls ``POST /api/blueprints/{bp_id}/probes``.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        body: The probe body dict (label, processors, etc.).

    Returns:
        dict: The created probe response (contains ``id``).

    Raises:
        Exception: If creation fails.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(f"/blueprints/{blueprint_id}/probes", "POST", data=body)
    if resp.status_code in (200, 201):
        return resp.json()
    raise Exception(f"Failed to create probe: {resp.status_code} {resp.text}")


def create_predefined_probe(
    client_factory, blueprint_id, predefined_probe_name, params
):
    """Instantiate a predefined probe in a blueprint.

    Calls ``POST /api/blueprints/{bp_id}/iba/predefined-probes/{name}``.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        predefined_probe_name: The predefined probe name (e.g. ``bgp_session``).
        params: Dict of parameters matching the predefined probe schema
                (e.g. ``{"label": "My Probe", "duration": 300}``).

    Returns:
        dict: Response containing the created probe ``id``.

    Raises:
        Exception: If instantiation fails.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(
        f"/blueprints/{blueprint_id}/iba/predefined-probes/{predefined_probe_name}",
        "POST",
        data=params,
    )
    if resp.status_code in (200, 201):
        return resp.json()
    raise Exception(
        f"Failed to instantiate predefined probe '{predefined_probe_name}': "
        f"{resp.status_code} {resp.text}"
    )


def update_probe(client_factory, blueprint_id, probe_id, body):
    """Update (PUT) a probe in a blueprint.

    Calls ``PUT /api/blueprints/{bp_id}/probes/{probe_id}``.

    The body should include ``label``, ``description``, ``disabled``,
    and ``processors``.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        probe_id: The probe UUID.
        body: The full update body.

    Raises:
        Exception: If the update fails.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(
        f"/blueprints/{blueprint_id}/probes/{probe_id}", "PUT", data=body
    )
    if resp.status_code not in (200, 202, 204):
        raise Exception(f"Failed to update probe: {resp.status_code} {resp.text}")


def delete_probe(client_factory, blueprint_id, probe_id):
    """Delete a probe from a blueprint.

    Calls ``DELETE /api/blueprints/{bp_id}/probes/{probe_id}``.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        probe_id: The probe UUID.

    Raises:
        Exception: If deletion fails.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(f"/blueprints/{blueprint_id}/probes/{probe_id}", "DELETE")
    if resp.status_code not in (200, 202, 204):
        raise Exception(f"Failed to delete probe: {resp.status_code} {resp.text}")


# ──────────────────────────────────────────────────────────────────
#  Probe convenience helpers
# ──────────────────────────────────────────────────────────────────


def find_probe_by_label(client_factory, blueprint_id, label):
    """Find a probe by its label.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        label: The probe label to search for.

    Returns:
        dict or None: The matching probe dict, or *None*.
    """
    items = list_probes(client_factory, blueprint_id)
    for item in items:
        if isinstance(item, dict) and item.get("label") == label:
            return item
    return None


def wait_for_probe_state(
    client_factory,
    blueprint_id,
    probe_id,
    target_state="operational",
    timeout=120,
    interval=5,
):
    """Poll a probe until it reaches the target state or timeout.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        probe_id: The probe UUID.
        target_state: Desired ``state`` value (default ``operational``).
        timeout: Max seconds to wait.
        interval: Seconds between polls.

    Returns:
        dict: The probe dict once it reaches the target state.

    Raises:
        Exception: If the probe does not reach the target state within timeout.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        probe = get_probe(client_factory, blueprint_id, probe_id)
        if probe and probe.get("state") == target_state:
            return probe
        time.sleep(interval)
    raise Exception(
        f"Probe {probe_id} did not reach state '{target_state}' within {timeout}s"
    )


# ──────────────────────────────────────────────────────────────────
#  Predefined probe helpers
# ──────────────────────────────────────────────────────────────────


def list_predefined_probes(client_factory, blueprint_id):
    """List all predefined (built-in) probes available for a blueprint.

    Calls ``GET /api/blueprints/{bp_id}/iba/predefined-probes``.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.

    Returns:
        list[dict]: List of predefined probe dicts (each has ``name``,
        ``schema``, ``description``).
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(f"/blueprints/{blueprint_id}/iba/predefined-probes")
    if resp.status_code == 200:
        data = resp.json()
        return data.get("items", [])
    return []


def get_predefined_probe(client_factory, blueprint_id, name):
    """Find a predefined probe by name.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        name: The predefined probe name (e.g. ``bgp_session``).

    Returns:
        dict or None: The predefined probe dict, or *None*.
    """
    items = list_predefined_probes(client_factory, blueprint_id)
    for item in items:
        if isinstance(item, dict) and item.get("name") == name:
            return item
    return None


# ──────────────────────────────────────────────────────────────────
#  Dashboard operations
# ──────────────────────────────────────────────────────────────────


def list_dashboards(client_factory, blueprint_id):
    """List all IBA dashboards in a blueprint.

    Calls ``GET /api/blueprints/{bp_id}/iba/dashboards``.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.

    Returns:
        list[dict]: List of dashboard dicts.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(f"/blueprints/{blueprint_id}/iba/dashboards")
    if resp.status_code == 200:
        data = resp.json()
        return data.get("items", [])
    return []


def get_dashboard(client_factory, blueprint_id, dashboard_id):
    """Get a single IBA dashboard by ID.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        dashboard_id: The dashboard UUID.

    Returns:
        dict or None: The dashboard dict, or *None*.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(f"/blueprints/{blueprint_id}/iba/dashboards/{dashboard_id}")
    if resp.status_code == 200:
        return resp.json()
    return None


def create_dashboard(client_factory, blueprint_id, body):
    """Create an IBA dashboard in a blueprint.

    Calls ``POST /api/blueprints/{bp_id}/iba/dashboards``.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        body: The dashboard body dict.

    Returns:
        dict: The created dashboard response (contains ``id``).

    Raises:
        Exception: If creation fails.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(
        f"/blueprints/{blueprint_id}/iba/dashboards", "POST", data=body
    )
    if resp.status_code in (200, 201):
        return resp.json()
    raise Exception(f"Failed to create dashboard: {resp.status_code} {resp.text}")


def update_dashboard(client_factory, blueprint_id, dashboard_id, body):
    """Update (PUT) an IBA dashboard.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        dashboard_id: The dashboard UUID.
        body: The full update body.

    Raises:
        Exception: If the update fails.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(
        f"/blueprints/{blueprint_id}/iba/dashboards/{dashboard_id}",
        "PUT",
        data=body,
    )
    if resp.status_code not in (200, 202, 204):
        raise Exception(f"Failed to update dashboard: {resp.status_code} {resp.text}")


def delete_dashboard(client_factory, blueprint_id, dashboard_id):
    """Delete an IBA dashboard.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        dashboard_id: The dashboard UUID.

    Raises:
        Exception: If deletion fails.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(
        f"/blueprints/{blueprint_id}/iba/dashboards/{dashboard_id}", "DELETE"
    )
    if resp.status_code not in (200, 202, 204):
        raise Exception(f"Failed to delete dashboard: {resp.status_code} {resp.text}")


def find_dashboard_by_label(client_factory, blueprint_id, label):
    """Find an IBA dashboard by its label.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        label: The dashboard label to search for.

    Returns:
        dict or None: The matching dashboard dict, or *None*.
    """
    items = list_dashboards(client_factory, blueprint_id)
    for item in items:
        if isinstance(item, dict) and item.get("label") == label:
            return item
    return None
