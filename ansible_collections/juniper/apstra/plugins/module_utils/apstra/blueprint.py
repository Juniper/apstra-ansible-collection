# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

"""
Blueprint utility functions for Apstra Ansible modules.

Delegates to focused utility modules:

  - **bp_nodes**          – node read / patch via SDK
  - **bp_query**          – QE graph queries via SDK
  - **bp_configlets**     – blueprint configlet CRUD via raw API
  - **bp_resource_pools** – resource-group operations via raw API

This module retains helpers that require ``raw_request`` because the
SDK does not expose a dedicated endpoint (switch-system-links,
external-generic-systems, obj-policy-export).

Usage::

    from ansible_collections.juniper.apstra.plugins.module_utils.apstra.blueprint import (
        find_system_by_label,
        create_switch_system_links,
        ...
    )
"""

# ── Delegates ────────────────────────────────────────────────────────────
# Import from focused modules and re-export so that existing consumer
# imports continue to work without changes.

# SDK-based
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.bp_nodes import (  # noqa: F401
    get_node as get_blueprint_node,
    patch_node as patch_blueprint_node,
)

# SDK-based
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.bp_query import (  # noqa: F401
    run_qe_query as blueprint_qe_query,
)

# API-based (raw_request)
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.bp_configlets import (  # noqa: F401
    list_blueprint_configlets,
    get_blueprint_configlet,
    create_blueprint_configlet,
    update_blueprint_configlet,
    delete_blueprint_configlet,
    find_blueprint_configlet_by_label,
)

# API-based (raw_request)
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.bp_resource_pools import (  # noqa: F401
    list_resource_groups,
    get_resource_groups_by_type,
    get_resource_group,
    update_resource_group,
    assign_resource_pools,
    unassign_resource_pools,
)


# ── Blueprint Node Convenience Wrappers ─────────────────────────────────
# These thin wrappers keep the same signatures as before, but delegate to
# the SDK-based ``bp_nodes`` module internally.


def patch_blueprint_node_unsafe(client_factory, blueprint_id, node_id, patch_body):
    """PATCH a blueprint node with allow_unsafe=true.

    Delegates to ``bp_nodes.patch_node`` which auto-detects the need for
    ``allow_unsafe`` based on field names.  Passing only unsafe fields
    guarantees the ``allow_unsafe=True`` code-path is taken.

    :param client_factory: An ApstraClientFactory instance.
    :param blueprint_id: The blueprint ID.
    :param node_id: The node ID.
    :param patch_body: Dict of fields to patch.
    :return: Parsed JSON response.
    """
    return patch_blueprint_node(client_factory, blueprint_id, node_id, patch_body)


def update_blueprint_node(
    client_factory, blueprint_id, node_id, patch_body, safe_fields=None
):
    """PATCH a blueprint node, routing through safe or unsafe as needed.

    Delegates to ``bp_nodes.patch_node`` which handles ``allow_unsafe``
    automatically.

    :param client_factory: An ApstraClientFactory instance.
    :param blueprint_id: The blueprint ID.
    :param node_id: The node ID.
    :param patch_body: Dict of fields to patch.
    :param safe_fields: Accepted for backward compatibility but ignored;
        ``bp_nodes.patch_node`` auto-detects safe vs unsafe fields.
    :return: Parsed JSON response.
    """
    return patch_blueprint_node(client_factory, blueprint_id, node_id, patch_body)


def set_blueprint_node_tags(client_factory, blueprint_id, node_id, tags):
    """Set tags on a blueprint node (requires allow_unsafe).

    :param client_factory: An ApstraClientFactory instance.
    :param blueprint_id: The blueprint ID.
    :param node_id: The node ID.
    :param tags: List of tag strings.
    :return: Parsed JSON response.
    """
    return patch_blueprint_node(client_factory, blueprint_id, node_id, {"tags": tags})


def set_blueprint_node_property(
    client_factory, blueprint_id, node_id, prop, value, safe_fields=None
):
    """Set a single property on a blueprint node.

    :param client_factory: An ApstraClientFactory instance.
    :param blueprint_id: The blueprint ID.
    :param node_id: The node ID.
    :param prop: The property name.
    :param value: The property value.
    :param safe_fields: Accepted for backward compatibility but ignored.
    :return: Parsed JSON response.
    """
    return patch_blueprint_node(client_factory, blueprint_id, node_id, {prop: value})


# ── Blueprint Generic System Utilities ─────────────────────────────────
# These use ``bp_query.run_qe_query`` (SDK) for graph queries, and
# ``raw_request`` only for endpoints the SDK does not cover.


def find_system_by_label(client_factory, blueprint_id, label):
    """Find a generic system by label using QE.

    :param client_factory: An ApstraClientFactory instance.
    :param blueprint_id: The blueprint ID.
    :param label: The system label to search for.
    :return: The system dict, or None.
    """
    items = blueprint_qe_query(
        client_factory,
        blueprint_id,
        f"node('system', system_type='server', label='{label}', name='gs')",
    )
    if items:
        return items[0].get("gs", items[0])
    return None


def find_system_by_hostname(client_factory, blueprint_id, hostname):
    """Find a generic system by hostname using QE.

    :param client_factory: An ApstraClientFactory instance.
    :param blueprint_id: The blueprint ID.
    :param hostname: The system hostname to search for.
    :return: The system dict, or None.
    """
    items = blueprint_qe_query(
        client_factory,
        blueprint_id,
        f"node('system', system_type='server', hostname='{hostname}', name='gs')",
    )
    if items:
        return items[0].get("gs", items[0])
    return None


def get_system_tags(client_factory, blueprint_id, sys_id):
    """Get tags for a system node.

    :param client_factory: An ApstraClientFactory instance.
    :param blueprint_id: The blueprint ID.
    :param sys_id: The system node ID.
    :return: List of tag strings.
    """
    node = get_blueprint_node(client_factory, blueprint_id, sys_id)
    if node:
        return node.get("tags", []) or []
    return []


def get_system_link_ids(client_factory, blueprint_id, sys_id):
    """Get all physical (ethernet) link IDs for a system via QE.

    :param client_factory: An ApstraClientFactory instance.
    :param blueprint_id: The blueprint ID.
    :param sys_id: The system node ID.
    :return: List of link ID strings.
    """
    items = blueprint_qe_query(
        client_factory,
        blueprint_id,
        (
            f"node('system', id='{sys_id}', name='gs')"
            f".out('hosted_interfaces').node('interface', name='intf')"
            f".out('link').node('link', name='link')"
        ),
    )
    link_ids = set()
    for item in items:
        if isinstance(item, dict):
            link_info = item.get("link", {})
            if isinstance(link_info, dict) and link_info.get("id"):
                if link_info.get("link_type") != "aggregate_link":
                    link_ids.add(link_info["id"])
    return list(link_ids)


def get_system_links_detail(client_factory, blueprint_id, sys_id):
    """Get detailed link+interface info for a system.

    :param client_factory: An ApstraClientFactory instance.
    :param blueprint_id: The blueprint ID.
    :param sys_id: The system node ID.
    :return: List of dicts with keys: link_id, target_switch_id,
             target_switch_if_name, lag_mode, group_label, tags.
    """
    items = blueprint_qe_query(
        client_factory,
        blueprint_id,
        (
            f"node('system', id='{sys_id}', name='gs')"
            f".out('hosted_interfaces').node('interface', name='gs_intf')"
            f".out('link').node('link', link_type='ethernet', name='link')"
            f".in_('link').node('interface', name='sw_intf')"
            f".in_('hosted_interfaces').node('system', name='switch')"
        ),
    )
    links = []
    seen_link_ids = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        link = item.get("link", {})
        sw = item.get("switch", {})
        sw_intf = item.get("sw_intf", {})

        # Skip the self-referential path where 'switch' is the GS itself
        if sw.get("id") == sys_id:
            continue

        # Deduplicate by link_id
        lid = link.get("id")
        if lid in seen_link_ids:
            continue
        seen_link_ids.add(lid)

        links.append(
            {
                "link_id": lid,
                "target_switch_id": sw.get("id"),
                "target_switch_if_name": sw_intf.get("if_name"),
                "lag_mode": link.get("lag_mode"),
                "group_label": link.get("group_label"),
                "tags": link.get("tags", []) or [],
            }
        )
    return links


# ── Raw API helpers (no SDK coverage) ───────────────────────────────────
# The following endpoints are not exposed by any SDK client, so we use
# ``raw_request`` directly.


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


def create_switch_system_links(client_factory, blueprint_id, links, name, hostname):
    """Create a new generic system via switch-system-links API.

    Builds the payload from the flat link list, creating one new system.
    No SDK support — uses ``raw_request``.

    :param client_factory: An ApstraClientFactory instance.
    :param blueprint_id: The blueprint ID.
    :param links: List of link definition dicts.
    :param name: The system name/label.
    :param hostname: The system hostname.
    :return: The API response dict (with 'ids' list of created link IDs).
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

    POST /api/blueprints/{bp}/switch-system-links with system_id set.
    No SDK support — uses ``raw_request``.

    :param client_factory: An ApstraClientFactory instance.
    :param blueprint_id: The blueprint ID.
    :param sys_id: The existing system node ID.
    :param links: List of link definition dicts.
    :return: The API response dict.
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

    POST /api/blueprints/{bp}/delete-switch-system-links.
    Removing the last link removes the generic system itself.
    No SDK support — uses ``raw_request``.

    :param client_factory: An ApstraClientFactory instance.
    :param blueprint_id: The blueprint ID.
    :param link_ids: List of link ID strings to delete.
    :raises Exception: If the deletion fails.
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


def create_external_generic_system(client_factory, blueprint_id, name, hostname):
    """Create an external generic system.

    POST /api/blueprints/{bp}/external-generic-systems.
    No SDK support — uses ``raw_request``.

    :param client_factory: An ApstraClientFactory instance.
    :param blueprint_id: The blueprint ID.
    :param name: The system name/label.
    :param hostname: The system hostname.
    :return: The API response dict.
    """
    body = {
        "label": name or hostname or "external-generic-system",
        "hostname": hostname or name or "external-generic-system",
    }
    return _raw_post(
        client_factory, f"/blueprints/{blueprint_id}/external-generic-systems", body
    )


def delete_external_generic_system(client_factory, blueprint_id, sys_id):
    """DELETE /api/blueprints/{bp}/external-generic-systems/{sys}.

    No SDK support — uses ``raw_request``.

    :param client_factory: An ApstraClientFactory instance.
    :param blueprint_id: The blueprint ID.
    :param sys_id: The system node ID.
    :raises Exception: If the deletion fails.
    """
    _raw_delete(
        client_factory,
        f"/blueprints/{blueprint_id}/external-generic-systems/{sys_id}",
    )


def clear_cts_from_links(client_factory, blueprint_id, sys_id):
    """Clear all connectivity templates from a system's link interfaces.

    Uses ``bp_query`` (SDK) to discover interfaces, then ``raw_request``
    for the obj-policy-export endpoint which has no SDK support.

    :param client_factory: An ApstraClientFactory instance.
    :param blueprint_id: The blueprint ID.
    :param sys_id: The system node ID.
    """
    items = blueprint_qe_query(
        client_factory,
        blueprint_id,
        (
            f"node('system', id='{sys_id}', name='gs')"
            f".out('hosted_interfaces').node('interface', if_type='ethernet', name='intf')"
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


# ── Backward-compatible raw API helpers ──────────────────────────────────
# Some callers still use these for paths that don't map neatly to the SDK
# or to the dedicated utility modules.  New code should prefer bp_nodes,
# bp_query, bp_configlets, or bp_resource_pools where possible.


def api_get(client_factory, path):
    """GET via raw_request, returns parsed JSON or None."""
    base = client_factory.get_base_client()
    resp = base.raw_request(path)
    if resp.status_code == 200:
        return resp.json()
    return None


def api_post(client_factory, path, data, ok_codes=(200, 201, 202)):
    """POST via raw_request."""
    return _raw_post(client_factory, path, data, ok_codes)


def api_patch(client_factory, path, data, ok_codes=(200, 202, 204)):
    """PATCH via raw_request."""
    base = client_factory.get_base_client()
    resp = base.raw_request(path, "PATCH", data=data)
    if resp.status_code in ok_codes:
        try:
            return resp.json()
        except Exception:
            return {}
    raise Exception(f"PATCH {path} failed: {resp.status_code} {resp.text}")


def api_put(client_factory, path, data, ok_codes=(200, 202, 204)):
    """PUT via raw_request."""
    base = client_factory.get_base_client()
    resp = base.raw_request(path, "PUT", data=data)
    if resp.status_code in ok_codes:
        try:
            return resp.json()
        except Exception:
            return {}
    raise Exception(f"PUT {path} failed: {resp.status_code} {resp.text}")


def api_delete(client_factory, path, ok_codes=(200, 202, 204)):
    """DELETE via raw_request."""
    _raw_delete(client_factory, path, ok_codes)
