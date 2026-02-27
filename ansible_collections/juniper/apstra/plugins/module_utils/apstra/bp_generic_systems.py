# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

"""Blueprint generic-system utilities (API-based).

Provides helpers for generic-system operations that the AOS SDK does
not expose natively.  Follows the same ``raw_request`` pattern as
``bp_property_set.py``.

API endpoints used::

    POST   /api/blueprints/{bp}/switch-system-links          → create / add links
    POST   /api/blueprints/{bp}/delete-switch-system-links    → delete links
    POST   /api/blueprints/{bp}/external-generic-systems      → create external GS
    DELETE /api/blueprints/{bp}/external-generic-systems/{id} → delete external GS
    POST   /api/blueprints/{bp}/obj-policy-export             → clear CTs

Usage inside a module::

    from ansible_collections.juniper.apstra.plugins.module_utils.apstra.bp_generic_systems import (
        create_switch_system_links,
        add_links_to_system,
        delete_switch_system_links,
        create_external_generic_system,
        delete_external_generic_system,
        clear_cts_from_links,
    )
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.juniper.apstra.plugins.module_utils.apstra.bp_query import (
    run_qe_query,
)


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
#  Connectivity-template clearing
# ──────────────────────────────────────────────────────────────────


def clear_cts_from_links(client_factory, blueprint_id, sys_id):
    """Clear all connectivity templates from a system's link interfaces.

    Uses ``bp_query.run_qe_query`` (SDK) to discover interfaces, then
    ``raw_request`` for the ``obj-policy-export`` endpoint which has
    no SDK support.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        sys_id: The system node ID.
    """
    items = run_qe_query(
        client_factory,
        blueprint_id,
        (
            f"node('system', id='{sys_id}', name='gs')"
            f".out('hosted_interfaces')"
            f".node('interface', if_type='ethernet', name='intf')"
        ),
    )
    intf_ids = []
    for item in items:
        if isinstance(item, dict):
            intf = item.get("intf", {})
            if isinstance(intf, dict) and intf.get("id"):
                intf_ids.append(intf["id"])

    if not intf_ids:
        return

    for intf_id in intf_ids:
        try:
            base = client_factory.get_base_client()
            base.raw_request(
                f"/blueprints/{blueprint_id}/obj-policy-export",
                "POST",
                data={"policy_type_name": "", "application_points": [intf_id]},
            )
        except Exception:
            pass  # Best-effort CT clearing
