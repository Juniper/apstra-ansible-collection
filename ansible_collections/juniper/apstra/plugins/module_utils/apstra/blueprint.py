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


# ── Low-level Blueprint API Helpers ─────────────────────────────────────


def api_get(client_factory, path):
    """Issue a GET request via the base client and return parsed JSON or None.

    :param client_factory: An ApstraClientFactory instance.
    :param path: The API path (e.g., '/blueprints/{id}/nodes/{node_id}').
    :return: Parsed JSON dict, or None if not found.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(path)
    if resp.status_code == 200:
        return resp.json()
    return None


def api_post(client_factory, path, data, ok_codes=(200, 201, 202)):
    """Issue a POST request via the base client.

    :param client_factory: An ApstraClientFactory instance.
    :param path: The API path.
    :param data: The request body (dict).
    :param ok_codes: Tuple of acceptable HTTP status codes.
    :return: Parsed JSON response.
    :raises Exception: If the response status is not in ok_codes.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(path, "POST", data=data)
    if resp.status_code in ok_codes:
        try:
            return resp.json()
        except Exception:
            return {}
    raise Exception(f"POST {path} failed: {resp.status_code} {resp.text}")


def api_patch(client_factory, path, data, ok_codes=(200, 202, 204)):
    """Issue a PATCH request via the base client.

    :param client_factory: An ApstraClientFactory instance.
    :param path: The API path.
    :param data: The request body (dict).
    :param ok_codes: Tuple of acceptable HTTP status codes.
    :return: Parsed JSON response.
    :raises Exception: If the response status is not in ok_codes.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(path, "PATCH", data=data)
    if resp.status_code in ok_codes:
        try:
            return resp.json()
        except Exception:
            return {}
    raise Exception(f"PATCH {path} failed: {resp.status_code} {resp.text}")


def api_put(client_factory, path, data, ok_codes=(200, 202, 204)):
    """Issue a PUT request via the base client.

    :param client_factory: An ApstraClientFactory instance.
    :param path: The API path.
    :param data: The request body (dict).
    :param ok_codes: Tuple of acceptable HTTP status codes.
    :return: Parsed JSON response.
    :raises Exception: If the response status is not in ok_codes.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(path, "PUT", data=data)
    if resp.status_code in ok_codes:
        try:
            return resp.json()
        except Exception:
            return {}
    raise Exception(f"PUT {path} failed: {resp.status_code} {resp.text}")


def api_delete(client_factory, path, ok_codes=(200, 202, 204)):
    """Issue a DELETE request via the base client.

    :param client_factory: An ApstraClientFactory instance.
    :param path: The API path.
    :param ok_codes: Tuple of acceptable HTTP status codes.
    :raises Exception: If the response status is not in ok_codes.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(path, "DELETE")
    if resp.status_code not in ok_codes:
        raise Exception(f"DELETE {path} failed: {resp.status_code} {resp.text}")


# ── Blueprint Node Utilities ───────────────────────────────────────────


def get_blueprint_node(client_factory, blueprint_id, node_id):
    """GET /api/blueprints/{bp}/nodes/{node} — returns dict or None.

    :param client_factory: An ApstraClientFactory instance.
    :param blueprint_id: The blueprint ID.
    :param node_id: The node ID.
    :return: The node dict, or None if not found.
    """
    return api_get(client_factory, f"/blueprints/{blueprint_id}/nodes/{node_id}")


def patch_blueprint_node(client_factory, blueprint_id, node_id, patch_body):
    """PATCH /api/blueprints/{bp}/nodes/{node} — standard safe PATCH.

    :param client_factory: An ApstraClientFactory instance.
    :param blueprint_id: The blueprint ID.
    :param node_id: The node ID.
    :param patch_body: Dict of fields to patch.
    :return: Parsed JSON response.
    """
    return api_patch(
        client_factory, f"/blueprints/{blueprint_id}/nodes/{node_id}", patch_body
    )


def patch_blueprint_node_unsafe(client_factory, blueprint_id, node_id, patch_body):
    """PATCH /api/blueprints/{bp}/nodes/{node}?allow_unsafe=true.

    Required for node properties outside the safe set (tags, domain_id,
    loopback_ipv4/ipv6, port_channel_id_*, etc.).

    :param client_factory: An ApstraClientFactory instance.
    :param blueprint_id: The blueprint ID.
    :param node_id: The node ID.
    :param patch_body: Dict of fields to patch.
    :return: Parsed JSON response.
    :raises Exception: If the PATCH fails.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(
        f"/blueprints/{blueprint_id}/nodes/{node_id}?allow_unsafe=true",
        "PATCH",
        data=patch_body,
    )
    if resp.status_code not in (200, 202, 204):
        raise Exception(
            f"PATCH (unsafe) /blueprints/{blueprint_id}/nodes/{node_id} failed: "
            f"{resp.status_code} {resp.text}"
        )
    try:
        return resp.json()
    except Exception:
        return {}


def update_blueprint_node(
    client_factory, blueprint_id, node_id, patch_body, safe_fields=None
):
    """PATCH a blueprint node, routing fields through safe or unsafe endpoints.

    Fields in *safe_fields* go through the normal PATCH endpoint; all
    others go through PATCH with allow_unsafe=true.

    :param client_factory: An ApstraClientFactory instance.
    :param blueprint_id: The blueprint ID.
    :param node_id: The node ID.
    :param patch_body: Dict of fields to patch.
    :param safe_fields: Frozenset of field names safe for normal PATCH.
    :return: Parsed JSON response.
    """
    if safe_fields is None:
        safe_fields = frozenset()
    safe = {k: v for k, v in patch_body.items() if k in safe_fields}
    unsafe = {k: v for k, v in patch_body.items() if k not in safe_fields}
    result = {}
    if safe:
        result = patch_blueprint_node(client_factory, blueprint_id, node_id, safe)
    if unsafe:
        result = patch_blueprint_node_unsafe(
            client_factory, blueprint_id, node_id, unsafe
        )
    return result


def set_blueprint_node_tags(client_factory, blueprint_id, node_id, tags):
    """Set tags on a blueprint node.

    Tags are not in the safe-PATCH set, so allow_unsafe=true is required.

    :param client_factory: An ApstraClientFactory instance.
    :param blueprint_id: The blueprint ID.
    :param node_id: The node ID.
    :param tags: List of tag strings.
    :return: Parsed JSON response.
    """
    return patch_blueprint_node_unsafe(
        client_factory, blueprint_id, node_id, {"tags": tags}
    )


def set_blueprint_node_property(
    client_factory, blueprint_id, node_id, prop, value, safe_fields=None
):
    """Set a single property on a blueprint node.

    Routes through safe or unsafe PATCH as appropriate.

    :param client_factory: An ApstraClientFactory instance.
    :param blueprint_id: The blueprint ID.
    :param node_id: The node ID.
    :param prop: The property name.
    :param value: The property value.
    :param safe_fields: Frozenset of field names safe for normal PATCH.
    :return: Parsed JSON response.
    """
    if safe_fields is None:
        safe_fields = frozenset()
    if prop in safe_fields:
        return patch_blueprint_node(
            client_factory, blueprint_id, node_id, {prop: value}
        )
    return patch_blueprint_node_unsafe(
        client_factory, blueprint_id, node_id, {prop: value}
    )


def blueprint_qe_query(client_factory, blueprint_id, query):
    """Execute a QE (Query Engine) query against a blueprint.

    :param client_factory: An ApstraClientFactory instance.
    :param blueprint_id: The blueprint ID.
    :param query: The QE query string.
    :return: List of result items.
    """
    resp = api_post(client_factory, f"/blueprints/{blueprint_id}/qe", {"query": query})
    return resp.get("items", []) if resp else []


# ── Blueprint Generic System Utilities ─────────────────────────────────


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


def create_switch_system_links(client_factory, blueprint_id, links, name, hostname):
    """Create a new generic system via switch-system-links API.

    Builds the payload from the flat link list, creating one new system.

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
    return api_post(
        client_factory, f"/blueprints/{blueprint_id}/switch-system-links", body
    )


def add_links_to_system(client_factory, blueprint_id, sys_id, links):
    """Add links to an existing generic system.

    POST /api/blueprints/{bp}/switch-system-links with system_id set.

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
    return api_post(
        client_factory, f"/blueprints/{blueprint_id}/switch-system-links", body
    )


def delete_switch_system_links(client_factory, blueprint_id, link_ids):
    """Delete switch-system links by ID list.

    POST /api/blueprints/{bp}/delete-switch-system-links.
    Removing the last link removes the generic system itself.

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
    return api_post(
        client_factory, f"/blueprints/{blueprint_id}/external-generic-systems", body
    )


def delete_external_generic_system(client_factory, blueprint_id, sys_id):
    """DELETE /api/blueprints/{bp}/external-generic-systems/{sys}.

    :param client_factory: An ApstraClientFactory instance.
    :param blueprint_id: The blueprint ID.
    :param sys_id: The system node ID.
    :raises Exception: If the deletion fails.
    """
    api_delete(
        client_factory,
        f"/blueprints/{blueprint_id}/external-generic-systems/{sys_id}",
    )


def clear_cts_from_links(client_factory, blueprint_id, sys_id):
    """Clear all connectivity templates from a system's link interfaces.

    Queries interfaces, then removes CT assignments from each.

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
