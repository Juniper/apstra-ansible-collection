# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

"""Blueprint tenant utilities.

Provides reusable helpers for managing tenants within an Apstra
blueprint via ``raw_request``.  The SDK does not expose a dedicated
tenant endpoint, so this module uses the REST API directly —
following the same pattern as ``bp_configlets.py``.

A **Tenant** in Apstra is a logical grouping of Routing Zones
(Security Zones / VRFs).  Each tenant has a label and a list of
security-zone IDs (``application_node_ids``) that belong to it.

API endpoints::

    GET    /api/blueprints/{bp_id}/tenants              → list
    POST   /api/blueprints/{bp_id}/tenants              → create
    GET    /api/blueprints/{bp_id}/tenants/{tenant_id}  → get
    PUT    /api/blueprints/{bp_id}/tenants/{tenant_id}  → update (SZ linkage)
    DELETE /api/blueprints/{bp_id}/tenants/{tenant_id}  → delete

Create / PUT body::

    {
        "label": "my-tenant",
        "application_node_ids": ["sz_id_1", "sz_id_2"]
    }

Note: The tenant *label* is immutable after creation.  PUT only
updates ``application_node_ids``.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type


# ──────────────────────────────────────────────────────────────────
#  Collection operations
# ──────────────────────────────────────────────────────────────────


def list_tenants(client_factory, blueprint_id):
    """List all tenants in a blueprint.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.

    Returns:
        list[dict]: List of tenant dicts.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(f"/blueprints/{blueprint_id}/tenants")
    if resp.status_code == 200:
        data = resp.json()
        return data.get("items", [])
    return []


# ──────────────────────────────────────────────────────────────────
#  Single resource operations
# ──────────────────────────────────────────────────────────────────


def get_tenant(client_factory, blueprint_id, tenant_id):
    """Get a single tenant by ID.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        tenant_id: The tenant ID.

    Returns:
        dict or None: The tenant dict, or *None* if not found.
    """
    base = client_factory.get_base_client()
    url = f"/blueprints/{blueprint_id}/tenants/{tenant_id}"
    resp = base.raw_request(url)
    if resp.status_code == 200:
        return resp.json()
    return None


def create_tenant(client_factory, blueprint_id, label, security_zone_ids=None):
    """Create a tenant in a blueprint.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        label: The tenant label.
        security_zone_ids: Optional list of security-zone IDs to assign.

    Returns:
        dict: ``{"id": "<tenant_id>"}``

    Raises:
        Exception: If creation fails.
    """
    body = {"label": label}
    if security_zone_ids:
        body["application_node_ids"] = list(security_zone_ids)
    base = client_factory.get_base_client()
    resp = base.raw_request(f"/blueprints/{blueprint_id}/tenants", "POST", data=body)
    if resp.status_code in (200, 201):
        return resp.json()
    raise Exception(f"Failed to create tenant: {resp.status_code} {resp.text}")


def update_tenant(client_factory, blueprint_id, tenant_id, security_zone_ids):
    """Update a tenant's security-zone assignments.

    The tenant label is immutable after creation; only
    ``application_node_ids`` can be changed via PUT.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        tenant_id: The tenant ID.
        security_zone_ids: List of security-zone IDs to assign.

    Raises:
        Exception: If the update fails.
    """
    body = {"application_node_ids": list(security_zone_ids)}
    base = client_factory.get_base_client()
    resp = base.raw_request(
        f"/blueprints/{blueprint_id}/tenants/{tenant_id}", "PUT", data=body
    )
    if resp.status_code not in (200, 202, 204):
        raise Exception(f"Failed to update tenant: {resp.status_code} {resp.text}")


def delete_tenant(client_factory, blueprint_id, tenant_id):
    """Delete a tenant from a blueprint.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        tenant_id: The tenant ID.

    Raises:
        Exception: If deletion fails.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(f"/blueprints/{blueprint_id}/tenants/{tenant_id}", "DELETE")
    if resp.status_code not in (200, 202, 204):
        raise Exception(f"Failed to delete tenant: {resp.status_code} {resp.text}")


# ──────────────────────────────────────────────────────────────────
#  Convenience helpers
# ──────────────────────────────────────────────────────────────────


def find_tenant_by_label(client_factory, blueprint_id, label):
    """Find a tenant by its label.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        label: The tenant label to search for.

    Returns:
        dict or None: The matching tenant dict, or *None*.
    """
    items = list_tenants(client_factory, blueprint_id)
    for item in items:
        if isinstance(item, dict) and item.get("label") == label:
            return item
    return None


def resolve_security_zone_ids(client_factory, blueprint_id, references):
    """Resolve a list of security-zone references to IDs.

    Each reference can be a security-zone ID or label.  Labels are
    resolved by listing all security zones and matching.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        references: List of security-zone IDs or labels.

    Returns:
        list[str]: List of resolved security-zone IDs.

    Raises:
        ValueError: If a reference cannot be resolved.
    """
    from ansible_collections.juniper.apstra.plugins.module_utils.apstra.name_resolution import (
        resolve_security_zone_id,
    )

    resolved = []
    for ref in references:
        sz_id = resolve_security_zone_id(
            client_factory, blueprint_id, ref, raise_on_missing=True
        )
        resolved.append(sz_id)
    return resolved
