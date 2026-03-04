# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

"""Blueprint generic-system API utilities.

Provides helpers for generic-system operations that require
``raw_request`` — the SDK does not expose these endpoints.

API endpoints used::

    POST   /api/blueprints/{bp}/switch-system-links          -> create / add links
    POST   /api/blueprints/{bp}/delete-switch-system-links    -> delete links
    POST   /api/blueprints/{bp}/external-generic-systems      -> create external GS
    DELETE /api/blueprints/{bp}/external-generic-systems/{id} -> delete external GS
    POST   /api/blueprints/{bp}/qe                            -> graph queries
    PATCH  /api/blueprints/{bp}                               -> graph mutations

Usage inside a module::

    from ansible_collections.juniper.apstra.plugins.module_utils.apstra.bp_generic_systems import (
        create_switch_system_links,
        add_links_to_system,
        delete_switch_system_links,
        create_external_generic_system,
        delete_external_generic_system,
        get_system_asn,
        set_system_asn,
        get_system_loopback,
        create_or_update_loopback,
    )
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type


# ──────────────────────────────────────────────────────────────────
#  Internal raw-request helpers
# ──────────────────────────────────────────────────────────────────


def _raw_post(client_factory, path, data, ok_codes=(200, 201, 202)):
    """Issue a POST via raw_request.  Internal helper."""
    base = client_factory.get_base_client()
    resp = base.raw_request(path, "POST", data=data)
    if resp.status_code in ok_codes:
        try:
            return resp.json()
        except Exception:
            return {}
    raise Exception(f"POST {path} failed: {resp.status_code} {resp.text}")


def _raw_delete(client_factory, path, ok_codes=(200, 202, 204)):
    """Issue a DELETE via raw_request.  Internal helper."""
    base = client_factory.get_base_client()
    resp = base.raw_request(path, "DELETE")
    if resp.status_code not in ok_codes:
        raise Exception(f"DELETE {path} failed: {resp.status_code} {resp.text}")


def _raw_patch(client_factory, path, data, ok_codes=(200, 202, 204)):
    """Issue a PATCH via raw_request.  Internal helper."""
    base = client_factory.get_base_client()
    resp = base.raw_request(path, "PATCH", data=data)
    if resp.status_code in ok_codes:
        try:
            return resp.json()
        except Exception:
            return {}
    raise Exception(f"PATCH {path} failed: {resp.status_code} {resp.text}")


# ──────────────────────────────────────────────────────────────────
#  Switch-system-links operations
# ──────────────────────────────────────────────────────────────────


def create_switch_system_links(client_factory, blueprint_id, links, name, hostname):
    """Create a new generic system via switch-system-links API.

    Builds the payload from the flat link list, creating one new system.

    Calls ``POST /api/blueprints/{bp}/switch-system-links`` via
    ``raw_request`` — no SDK support.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        links: List of link definition dicts.
        name: The system name/label.
        hostname: The system hostname.

    Returns:
        dict: The API response (with ``ids`` list of created link IDs).
    """
    link_count = len(links)
    speed_value = 10
    speed_unit = "G"

    api_links = []
    for link in links:
        api_link = {
            "switch": {
                "system_id": link["target_switch_id"],
                "transformation_id": link.get("target_switch_if_transform_id", 1),
                "if_name": link["target_switch_if_name"],
            },
            "system": {
                "system_id": None,
            },
            "new_system_index": 0,
        }
        if link.get("lag_mode"):
            api_link["lag_mode"] = link["lag_mode"]
        else:
            api_link["lag_mode"] = None
        if link.get("group_label"):
            api_link["link_group_label"] = link["group_label"]
        api_links.append(api_link)

    ld_id = f"AOS-{link_count}x{speed_value}-1"
    ld_display = ld_id

    body = {
        "links": api_links,
        "new_systems": [
            {
                "system_type": "server",
                "label": name or hostname or "generic-system",
                "hostname": hostname or name or "generic-system",
                "deploy_mode": "deploy",
                "logical_device": {
                    "id": ld_id,
                    "display_name": ld_display,
                    "panels": [
                        {
                            "port_groups": [
                                {
                                    "roles": ["leaf", "access"],
                                    "count": link_count,
                                    "speed": {
                                        "value": speed_value,
                                        "unit": speed_unit,
                                    },
                                }
                            ],
                            "port_indexing": {
                                "schema": "absolute",
                                "order": "T-B, L-R",
                                "start_index": 1,
                            },
                            "panel_layout": {
                                "row_count": 1,
                                "column_count": link_count,
                            },
                        }
                    ],
                },
                "port_channel_id_min": 0,
                "port_channel_id_max": 0,
            }
        ],
    }
    return _raw_post(
        client_factory, f"/blueprints/{blueprint_id}/switch-system-links", body
    )


def add_links_to_system(client_factory, blueprint_id, sys_id, links):
    """Add links to an existing generic system.

    Calls ``POST /api/blueprints/{bp}/switch-system-links`` with
    ``system_id`` set via ``raw_request`` — no SDK support.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        sys_id: The existing system node ID.
        links: List of link definition dicts.

    Returns:
        dict: The API response.
    """
    api_links = []
    for link in links:
        api_link = {
            "switch": {
                "system_id": link["target_switch_id"],
                "transformation_id": link.get("target_switch_if_transform_id", 1),
                "if_name": link["target_switch_if_name"],
            },
            "system": {
                "system_id": sys_id,
            },
        }
        if link.get("lag_mode"):
            api_link["lag_mode"] = link["lag_mode"]
        else:
            api_link["lag_mode"] = None
        if link.get("group_label"):
            api_link["link_group_label"] = link["group_label"]
        api_links.append(api_link)

    body = {"links": api_links}
    return _raw_post(
        client_factory, f"/blueprints/{blueprint_id}/switch-system-links", body
    )


def delete_switch_system_links(client_factory, blueprint_id, link_ids):
    """Delete switch-system links by ID list.

    Calls ``POST /api/blueprints/{bp}/delete-switch-system-links``
    via ``raw_request`` — no SDK support.

    Removing the last link removes the generic system itself.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        link_ids: List of link ID strings to delete.

    Raises:
        Exception: If the deletion fails.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(
        f"/blueprints/{blueprint_id}/delete-switch-system-links",
        "POST",
        data={"link_ids": link_ids},
    )
    if resp.status_code not in (200, 201, 202, 204):
        raise Exception(
            f"Failed to delete switch-system-links: {resp.status_code} {resp.text}"
        )


# ──────────────────────────────────────────────────────────────────
#  External generic-system operations
# ──────────────────────────────────────────────────────────────────


def create_external_generic_system(client_factory, blueprint_id, name, hostname):
    """Create an external generic system.

    Calls ``POST /api/blueprints/{bp}/external-generic-systems`` via
    ``raw_request`` — no SDK support.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        name: The system name/label.
        hostname: The system hostname.

    Returns:
        dict: The API response.
    """
    body = {
        "label": name or hostname or "external-generic-system",
        "hostname": hostname or name or "external-generic-system",
    }
    return _raw_post(
        client_factory, f"/blueprints/{blueprint_id}/external-generic-systems", body
    )


def delete_external_generic_system(client_factory, blueprint_id, sys_id):
    """Delete an external generic system.

    Calls ``DELETE /api/blueprints/{bp}/external-generic-systems/{id}``
    via ``raw_request`` — no SDK support.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        sys_id: The system node ID.

    Raises:
        Exception: If the deletion fails.
    """
    _raw_delete(
        client_factory,
        f"/blueprints/{blueprint_id}/external-generic-systems/{sys_id}",
    )


# ──────────────────────────────────────────────────────────────────
#  Graph-mutation helpers (ASN + loopback)
# ──────────────────────────────────────────────────────────────────

# Import bp_nodes lazily to avoid circular imports.  The functions
# below are the only callers.
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.bp_nodes import (  # noqa: E402
    get_node as _get_node,
    patch_node as _patch_node,
)


def get_system_asn(client_factory, blueprint_id, sys_id):
    """Read ASN (domain_id) for a generic system from its domain node.

    Apstra stores the ASN on a separate ``domain`` node (type
    ``autonomous_system``) connected to the system node, **not** as a
    property of the system node itself.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        sys_id: The system node UUID.

    Returns:
        str or None: The domain_id string, or ``None`` if not set.
    """
    qe = {
        "query": (
            f"node('domain', domain_type='autonomous_system', name='d')"
            f".out().node('system', id='{sys_id}')"
        )
    }
    resp = _raw_post(client_factory, f"/blueprints/{blueprint_id}/qe", qe)
    items = resp.get("items", []) if resp else []
    if items:
        domain = items[0].get("d", {})
        return domain.get("domain_id")
    return None


def set_system_asn(client_factory, blueprint_id, sys_id, asn):
    """Set ASN (domain_id) on the system's domain node.

    If the domain node already exists, patches its ``domain_id``.
    Otherwise creates a new ``domain`` node (type ``autonomous_system``)
    and a ``composed_of_systems`` relationship via the blueprint
    graph-mutation PATCH API.

    The value is coerced to a string (the API rejects integers).

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        sys_id: The system node UUID.
        asn: The ASN value (int or str).
    """
    asn_str = str(asn)

    # Find the domain node via QE
    qe = {
        "query": (
            f"node('domain', domain_type='autonomous_system', name='d')"
            f".out().node('system', id='{sys_id}')"
        )
    }
    resp = _raw_post(client_factory, f"/blueprints/{blueprint_id}/qe", qe)
    items = resp.get("items", []) if resp else []

    if items:
        domain_node_id = items[0].get("d", {}).get("id")
        if domain_node_id:
            _patch_node(
                client_factory, blueprint_id, domain_node_id, {"domain_id": asn_str}
            )
            return

    # Domain node doesn't exist — create via graph-mutation PATCH
    sys_node = _get_node(client_factory, blueprint_id, sys_id)
    label = sys_node.get("label", sys_id) if sys_node else sys_id
    domain_node_id = f"{label}_as"
    rel_id = f"{label}_as_composed"

    body = {
        "nodes": {
            domain_node_id: {
                "type": "domain",
                "domain_type": "autonomous_system",
                "domain_id": asn_str,
            },
        },
        "relationships": {
            rel_id: {
                "type": "composed_of_systems",
                "source_id": domain_node_id,
                "target_id": sys_id,
            }
        },
    }
    _raw_patch(client_factory, f"/blueprints/{blueprint_id}", body)


def get_system_loopback(client_factory, blueprint_id, sys_id):
    """Query the loopback interface node for a generic system.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        sys_id: The system node UUID.

    Returns:
        dict or None: Dict with ``node_id``, ``ipv4_addr``, ``ipv6_addr``
        keys, or ``None`` if no loopback exists.
    """
    qe = {
        "query": (
            f"node('system', id='{sys_id}', name='sys')"
            f".out('hosted_interfaces')"
            f".node('interface', if_type='loopback', name='lo')"
        )
    }
    resp = _raw_post(client_factory, f"/blueprints/{blueprint_id}/qe", qe)
    items = resp.get("items", []) if resp else []
    if items:
        lo = items[0].get("lo", {})
        return {
            "node_id": lo.get("id"),
            "ipv4_addr": lo.get("ipv4_addr"),
            "ipv6_addr": lo.get("ipv6_addr"),
        }
    return None


def create_or_update_loopback(
    client_factory, blueprint_id, sys_id, ipv4=None, ipv6=None
):
    """Create or update a loopback interface on a generic system.

    Uses the blueprint graph-mutation PATCH API to create an interface
    node (``type=interface``, ``if_type=loopback``) and a
    ``hosted_interfaces`` relationship.  If a loopback already exists,
    updates the IP addresses on the existing node.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        sys_id: The system node UUID.
        ipv4: Optional IPv4 CIDR address for the loopback.
        ipv6: Optional IPv6 CIDR address for the loopback.

    Returns:
        str: The loopback node ID.
    """
    existing = get_system_loopback(client_factory, blueprint_id, sys_id)

    if existing and existing.get("node_id"):
        # Update existing loopback interface node
        lo_patch = {}
        if ipv4 is not None and existing.get("ipv4_addr") != ipv4:
            lo_patch["ipv4_addr"] = ipv4
            lo_patch["ipv4_enabled"] = True
        if ipv6 is not None and existing.get("ipv6_addr") != ipv6:
            lo_patch["ipv6_addr"] = ipv6
            lo_patch["ipv6_enabled"] = True
        if lo_patch:
            _patch_node(client_factory, blueprint_id, existing["node_id"], lo_patch)
        return existing["node_id"]
    else:
        # Create new loopback via graph-mutation PATCH
        sys_node = _get_node(client_factory, blueprint_id, sys_id)
        label = sys_node.get("label", sys_id) if sys_node else sys_id
        lo_node_id = f"{label}_loopback"
        rel_id = f"{label}_loopback_hosted"

        node_props = {
            "type": "interface",
            "if_type": "loopback",
            "loopback_id": 0,
            "ipv4_enabled": False,
            "ipv6_enabled": False,
            "operation_state": "up",
        }
        if ipv4:
            node_props["ipv4_addr"] = ipv4
            node_props["ipv4_enabled"] = True
        if ipv6:
            node_props["ipv6_addr"] = ipv6
            node_props["ipv6_enabled"] = True

        body = {
            "nodes": {
                lo_node_id: node_props,
            },
            "relationships": {
                rel_id: {
                    "type": "hosted_interfaces",
                    "source_id": sys_id,
                    "target_id": lo_node_id,
                }
            },
        }
        _raw_patch(client_factory, f"/blueprints/{blueprint_id}", body)
        return lo_node_id
