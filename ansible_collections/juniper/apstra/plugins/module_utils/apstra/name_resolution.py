# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

"""
Name-to-ID Resolution Helpers
=================================

Centralised functions that resolve human-readable names (display_name,
label) to their corresponding UUIDs / IDs for various Apstra object
types.  Every resolver follows the same contract:

1. **Fast path** — if the value already looks like a UUID, return it
   unchanged.
2. **Slow path** — list the relevant objects and find the one whose
   name/label matches.
3. **Error** — raise ``ValueError`` with a helpful message listing
   available names when no match is found.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import re

# Regex for Apstra UUIDs (32 hex chars with hyphens: 8-4-4-4-12)
_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

# Map of group_type → SDK pool attribute name on the base client
_POOL_TYPE_MAP = {
    "asn": "asn_pools",
    "ip": "ip_pools",
    "ipv6": "ipv6_pools",
    "vni": "vni_pools",
    "vlan": "vlan_pools",
}


def _is_uuid(value):
    """Return True if *value* looks like a standard UUID."""
    return bool(value and _UUID_RE.match(str(value)))


# ──────────────────────────────────────────────────────────────────
#  Blueprint resolution
# ──────────────────────────────────────────────────────────────────


def resolve_blueprint_id(client_factory, blueprint_ref):
    """Resolve a blueprint reference (UUID or label) to its UUID.

    :param client_factory: An ``ApstraClientFactory`` instance.
    :param blueprint_ref: The blueprint UUID or label.
    :return: The resolved blueprint UUID string.
    :raises Exception: If a label is given but no matching blueprint is found.
    """
    if not blueprint_ref:
        return blueprint_ref

    # Fast path: already a UUID
    if _is_uuid(blueprint_ref):
        return blueprint_ref

    # Slow path: treat as a label and resolve
    base_client = client_factory.get_base_client()
    blueprints = base_client.blueprints.list()
    if blueprints is None:
        blueprints = []

    # Exact ID match (non-UUID IDs)
    for bp in blueprints:
        if bp.get("id") == blueprint_ref:
            return blueprint_ref

    # Exact label match
    for bp in blueprints:
        if bp.get("label") == blueprint_ref:
            return bp["id"]

    # Case-insensitive label fallback
    ref_lower = blueprint_ref.lower()
    for bp in blueprints:
        if (bp.get("label") or "").lower() == ref_lower:
            return bp["id"]

    available = [bp.get("label", "") for bp in blueprints]
    raise Exception(
        f"Blueprint with label '{blueprint_ref}' not found. " f"Available: {available}"
    )


# ──────────────────────────────────────────────────────────────────
#  Design template resolution
# ──────────────────────────────────────────────────────────────────


def resolve_template_id(client_factory, template_ref):
    """Resolve a design template reference (ID or display_name) to its ID.

    Users may supply either the exact template ID (e.g. ``L2_Virtual_EVPN``)
    or the human-readable display name (e.g. ``L2 Virtual EVPN``).

    :param client_factory: An ``ApstraClientFactory`` instance.
    :param template_ref: The template ID or display name.
    :return: The resolved template ID string.
    :raises ValueError: If no matching template is found.
    """
    if not template_ref:
        return template_ref

    base = client_factory.get_base_client()
    resp = base.raw_request("/design/templates")
    if resp.status_code != 200:
        raise Exception(
            f"Failed to list design templates: {resp.status_code} {resp.text}"
        )
    try:
        data = resp.json()
    except Exception:
        data = {}
    templates = data.get("items", [])

    # 1. Exact ID match
    for tmpl in templates:
        if tmpl.get("id") == template_ref:
            return template_ref

    # 2. Case-insensitive display_name match
    ref_lower = template_ref.lower()
    matches = [
        tmpl
        for tmpl in templates
        if (tmpl.get("display_name") or "").lower() == ref_lower
    ]
    if len(matches) == 1:
        return matches[0]["id"]
    if len(matches) > 1:
        ids = [m["id"] for m in matches]
        raise ValueError(
            f"Multiple templates match display_name '{template_ref}': {ids}. "
            "Please use the exact template ID instead."
        )

    # 3. No match found — build a helpful error message
    available = [
        f"  - {t.get('id')!r} ({t.get('display_name', '')})" for t in templates
    ]
    raise ValueError(
        f"Template '{template_ref}' not found. "
        f"Available templates:\n" + "\n".join(available)
    )


def resolve_system_node_ids(client_factory, blueprint_id, node_refs):
    """Resolve a list of system node references to their graph node IDs.

    :param client_factory: An ``ApstraClientFactory`` instance.
    :param blueprint_id: The blueprint UUID.
    :param node_refs: List of system node UUIDs or labels.
    :return: List of resolved system node ID strings.
    """
    if not node_refs:
        return node_refs
    return [
        resolve_system_node_id(client_factory, blueprint_id, ref) for ref in node_refs
    ]


# ──────────────────────────────────────────────────────────────────
#  Resource Pool resolution  (Phase 1)
# ──────────────────────────────────────────────────────────────────


def _list_pools(client_factory, pool_type):
    """List all pools of the given type.

    Returns a list of dicts, each with at least 'id' and 'display_name'.
    """
    sdk_attr = _POOL_TYPE_MAP.get(pool_type)
    if sdk_attr is None:
        raise ValueError(
            f"Unknown pool type '{pool_type}'. "
            f"Valid types: {sorted(_POOL_TYPE_MAP.keys())}"
        )
    base = client_factory.get_base_client()
    pool_resource = getattr(base, sdk_attr, None)
    if pool_resource is None:
        raise ValueError(f"SDK client has no attribute '{sdk_attr}'")
    result = pool_resource.list()
    if result is None:
        return []
    if isinstance(result, dict) and "items" in result:
        return result["items"]
    return result if isinstance(result, list) else []


def _resolve_pool_ref(pool_ref, pool_type, pools):
    """Resolve a single pool reference against a pre-fetched pool list.

    :param pool_ref: The pool UUID or display_name.
    :param pool_type: The pool type ('asn', 'ip', 'ipv6', 'vni', 'vlan').
    :param pools: Pre-fetched list of pool dicts with 'id' and 'display_name'.
    :return: The resolved pool ID string.
    :raises ValueError: If the pool reference does not match any existing pool.
    """
    if not pool_ref:
        return pool_ref

    # Check by exact ID match (covers both UUIDs and human-readable IDs)
    for pool in pools:
        if pool.get("id") == pool_ref:
            return pool_ref

    # If it looks like a UUID but didn't match any pool ID, it doesn't exist
    if _is_uuid(pool_ref):
        available = [
            f"  - {p.get('display_name', '')} (id={p.get('id', '')})" for p in pools
        ]
        raise ValueError(
            f"{pool_type.upper()} pool with ID '{pool_ref}' does not exist. "
            f"Available {pool_type} pools:\n" + "\n".join(available)
        )

    # Case-insensitive display_name match
    ref_lower = str(pool_ref).lower()
    matches = [p for p in pools if (p.get("display_name") or "").lower() == ref_lower]
    if len(matches) == 1:
        return matches[0]["id"]
    if len(matches) > 1:
        ids = [m["id"] for m in matches]
        raise ValueError(
            f"Multiple {pool_type} pools match display_name '{pool_ref}': {ids}. "
            "Please use the exact pool ID instead."
        )

    # No match
    available = [
        f"  - {p.get('display_name', '')} (id={p.get('id', '')})" for p in pools
    ]
    raise ValueError(
        f"{pool_type.upper()} pool '{pool_ref}' not found. "
        f"Available {pool_type} pools:\n" + "\n".join(available)
    )


def resolve_pool_id(client_factory, pool_ref, pool_type):
    """Resolve a single pool reference (UUID or display_name) to its ID.

    :param client_factory: An ``ApstraClientFactory`` instance.
    :param pool_ref: The pool UUID or display_name.
    :param pool_type: The pool type ('asn', 'ip', 'ipv6', 'vni', 'vlan').
    :return: The resolved pool ID string.
    :raises ValueError: If the pool reference does not match any existing pool.
    """
    if not pool_ref:
        return pool_ref

    pools = _list_pools(client_factory, pool_type)
    return _resolve_pool_ref(pool_ref, pool_type, pools)


def resolve_pool_ids(client_factory, pool_refs, pool_type):
    """Resolve a list of pool references to their IDs.

    Fetches the pool list once and validates that every reference
    (UUID or display_name) corresponds to an existing pool.

    :param client_factory: An ``ApstraClientFactory`` instance.
    :param pool_refs: List of pool UUIDs or display_names.
    :param pool_type: The pool type ('asn', 'ip', 'ipv6', 'vni', 'vlan').
    :return: List of resolved pool ID strings.
    :raises ValueError: If any pool reference does not match an existing pool.
    """
    if not pool_refs:
        return pool_refs
    pools = _list_pools(client_factory, pool_type)
    return [_resolve_pool_ref(ref, pool_type, pools) for ref in pool_refs]


# ──────────────────────────────────────────────────────────────────
#  Blueprint graph node resolution  (Phase 2 & 3)
# ──────────────────────────────────────────────────────────────────


def _run_qe(client_factory, blueprint_id, query_str):
    """Run a QE query and return the results list."""
    from ansible_collections.juniper.apstra.plugins.module_utils.apstra.bp_query import (
        run_qe_query,
    )

    return run_qe_query(client_factory, blueprint_id, query_str)


def resolve_security_zone_id(client_factory, blueprint_id, sz_ref):
    """Resolve a security-zone reference (UUID or label) to its node ID.

    :param client_factory: An ``ApstraClientFactory`` instance.
    :param blueprint_id: The blueprint UUID.
    :param sz_ref: The security-zone UUID or label.
    :return: The resolved security-zone node ID string.
    """
    if not sz_ref or _is_uuid(sz_ref):
        return sz_ref

    results = _run_qe(client_factory, blueprint_id, "node('security_zone', name='sz')")
    if not results:
        raise ValueError(
            f"Security zone '{sz_ref}' not found — no security zones exist in blueprint."
        )

    # Exact ID match (Apstra graph node IDs are short strings, not UUIDs)
    for r in results:
        sz = r.get("sz", {})
        if sz.get("id") == sz_ref:
            return sz_ref

    # Exact label match
    for r in results:
        sz = r.get("sz", {})
        if sz.get("label") == sz_ref:
            return sz["id"]

    # Case-insensitive label fallback
    ref_lower = sz_ref.lower()
    for r in results:
        sz = r.get("sz", {})
        if (sz.get("label") or "").lower() == ref_lower:
            return sz["id"]

    # VRF name match (e.g. "default" for the default routing zone)
    for r in results:
        sz = r.get("sz", {})
        if sz.get("vrf_name") == sz_ref:
            return sz["id"]

    # Case-insensitive vrf_name fallback
    for r in results:
        sz = r.get("sz", {})
        if (sz.get("vrf_name") or "").lower() == ref_lower:
            return sz["id"]

    available = [r.get("sz", {}).get("label", "") for r in results]
    raise ValueError(
        f"Security zone '{sz_ref}' not found in blueprint. " f"Available: {available}"
    )


def resolve_resource_group_name(client_factory, blueprint_id, group_name):
    """Resolve a resource-group name that may contain a security-zone reference.

    Resource-group names for VRF-scoped groups use the format
    ``sz:<security_zone_id>,<group_suffix>``.
    Users may specify a security-zone label or VRF name instead of the raw
    ID.  This function detects the ``sz:`` prefix, resolves the embedded
    reference via :func:`resolve_security_zone_id`, and returns the
    canonical group name with the resolved ID.

    If the group name does not start with ``sz:``, it is returned unchanged.

    :param client_factory: An ``ApstraClientFactory`` instance.
    :param blueprint_id: The blueprint UUID.
    :param group_name: The resource-group name (e.g.
        ``"sz:VRF1,leaf_loopback_ips"`` or ``"leaf_loopback_ips"``).
    :return: The group name with any security-zone reference resolved.
    """
    if not group_name or not group_name.startswith("sz:"):
        return group_name

    # Parse "sz:<sz_ref>,<suffix>"
    remainder = group_name[3:]  # strip "sz:" prefix
    comma_idx = remainder.find(",")
    if comma_idx < 0:
        # Malformed — no comma separator; return as-is and let the API
        # report the error.
        return group_name

    sz_ref = remainder[:comma_idx]
    suffix = remainder[comma_idx + 1 :]

    resolved_sz_id = resolve_security_zone_id(client_factory, blueprint_id, sz_ref)
    return f"sz:{resolved_sz_id},{suffix}"


def resolve_routing_policy_id(client_factory, blueprint_id, rp_ref):
    """Resolve a routing-policy reference (UUID or label) to its node ID.

    :param client_factory: An ``ApstraClientFactory`` instance.
    :param blueprint_id: The blueprint UUID.
    :param rp_ref: The routing-policy UUID or label.
    :return: The resolved routing-policy node ID string.
    """
    if not rp_ref or _is_uuid(rp_ref):
        return rp_ref

    results = _run_qe(client_factory, blueprint_id, "node('routing_policy', name='rp')")
    if not results:
        raise ValueError(
            f"Routing policy '{rp_ref}' not found — no routing policies exist in blueprint."
        )

    # Exact ID match (Apstra graph node IDs are short strings, not UUIDs)
    for r in results:
        rp = r.get("rp", {})
        if rp.get("id") == rp_ref:
            return rp_ref

    # Exact label match
    for r in results:
        rp = r.get("rp", {})
        if rp.get("label") == rp_ref:
            return rp["id"]

    # Case-insensitive fallback
    ref_lower = rp_ref.lower()
    for r in results:
        rp = r.get("rp", {})
        if (rp.get("label") or "").lower() == ref_lower:
            return rp["id"]

    available = [r.get("rp", {}).get("label", "") for r in results]
    raise ValueError(
        f"Routing policy '{rp_ref}' not found in blueprint. " f"Available: {available}"
    )


def resolve_system_node_id(client_factory, blueprint_id, node_ref):
    """Resolve a system node reference (UUID or label) to its graph node ID.

    Works for switches, spines, leafs, generic systems, etc.

    :param client_factory: An ``ApstraClientFactory`` instance.
    :param blueprint_id: The blueprint UUID.
    :param node_ref: The system node UUID or label.
    :return: The resolved system node ID string.
    """
    if not node_ref or _is_uuid(node_ref):
        return node_ref

    results = _run_qe(client_factory, blueprint_id, "node('system', name='sys')")
    if not results:
        raise ValueError(
            f"System node '{node_ref}' not found — no system nodes exist in blueprint."
        )

    # Exact ID match (Apstra graph node IDs are short strings, not UUIDs)
    for r in results:
        sys_node = r.get("sys", {})
        if sys_node.get("id") == node_ref:
            return node_ref

    # Exact label match
    for r in results:
        sys_node = r.get("sys", {})
        if sys_node.get("label") == node_ref:
            return sys_node["id"]

    # Case-insensitive fallback
    ref_lower = node_ref.lower()
    for r in results:
        sys_node = r.get("sys", {})
        if (sys_node.get("label") or "").lower() == ref_lower:
            return sys_node["id"]

    available = [r.get("sys", {}).get("label", "") for r in results]
    raise ValueError(
        f"System node '{node_ref}' not found in blueprint. " f"Available: {available}"
    )


def resolve_esi_member_ids(client_factory, blueprint_id, node_ref):
    """Check if *node_ref* is a redundancy-group (ESI/MLAG pair) and return
    the graph node IDs of its member systems.

    Used by the ``virtual_network`` module to transparently expand a
    redundancy-group label in ``bound_to.system_id`` into the individual
    member device IDs that the Apstra API expects.

    Delegates the QE query and parsing to
    :func:`~plugins.module_utils.apstra.bp_query.find_redundancy_groups`
    which is the canonical owner of that logic in this collection.

    :param client_factory: An ``ApstraClientFactory`` instance.
    :param blueprint_id: The blueprint UUID.
    :param node_ref: A system node label/ID or redundancy-group label/ID.
    :return: Sorted list of member system node IDs if *node_ref* identifies
             a redundancy group, or ``None`` if it does not (caller should
             fall back to regular :func:`resolve_system_node_id`).
    """
    if not node_ref:
        return None

    # Deferred import to avoid circular dependencies at module load time
    from ansible_collections.juniper.apstra.plugins.module_utils.apstra.bp_query import (
        find_redundancy_groups,
    )

    rg_map = find_redundancy_groups(client_factory, blueprint_id)
    if not rg_map:
        return None

    # Exact ID match
    if node_ref in rg_map:
        return rg_map[node_ref]["members"]

    # Exact label match
    for info in rg_map.values():
        if info["label"] == node_ref:
            return info["members"]

    # Case-insensitive label fallback
    ref_lower = node_ref.lower()
    for info in rg_map.values():
        if info["label"].lower() == ref_lower:
            return info["members"]

    return None


# ──────────────────────────────────────────────────────────────────
#  Interface / application-point resolution
# ──────────────────────────────────────────────────────────────────


def resolve_interface_node_id(client_factory, blueprint_id, ap_ref):
    """Resolve an application-point reference to a blueprint interface node ID.

    Accepts one of the following forms:

    * A raw string graph node ID (pass-through, no API call performed).
    * A dict ``{"system": "<system_label_or_id>", "if_name": "<if_name>"}``
      which is resolved via a QE graph query.

    :param client_factory: An ``ApstraClientFactory`` instance.
    :param blueprint_id: The blueprint UUID.
    :param ap_ref: A raw string node ID or a resolution dict.
    :return: The resolved interface graph node ID string.
    :raises ValueError: If the system or interface cannot be found.
    """
    if not ap_ref:
        return ap_ref

    if isinstance(ap_ref, str):
        return ap_ref  # already a raw node ID — pass through unchanged

    system_ref = ap_ref.get("system")
    if_name = ap_ref.get("if_name")
    if not system_ref or not if_name:
        raise ValueError(
            "Interface reference dict must have 'system' and 'if_name' keys, "
            f"got: {ap_ref}"
        )

    qry = (
        'node(type="system", name="sys")'
        '.out(type="hosted_interfaces")'
        f'.node(type="interface", if_name="{if_name}", name="intf")'
    )
    results = _run_qe(client_factory, blueprint_id, qry)

    if results:
        # Exact label or ID match
        for r in results:
            sys_node = r.get("sys", {})
            if sys_node.get("label") == system_ref or sys_node.get("id") == system_ref:
                return r["intf"]["id"]

        # Case-insensitive label fallback
        ref_lower = str(system_ref).lower()
        for r in results:
            sys_node = r.get("sys", {})
            if (sys_node.get("label") or "").lower() == ref_lower:
                return r["intf"]["id"]

    available_systems = sorted(
        {r.get("sys", {}).get("label", "") for r in (results or [])} - {""}
    )
    raise ValueError(
        f"Interface '{if_name}' on system '{system_ref}' not found in blueprint "
        f"'{blueprint_id}'. "
        + (
            f"Systems with that interface: {available_systems}"
            if available_systems
            else "No systems have an interface with that name."
        )
    )


def resolve_application_point_ids(client_factory, blueprint_id, ap_refs):
    """Resolve a list of application-point references to interface node IDs.

    Each entry may be a raw string graph node ID or a resolution dict
    ``{"system": "<label_or_id>", "if_name": "<if_name>"}``.

    :param client_factory: An ``ApstraClientFactory`` instance.
    :param blueprint_id: The blueprint UUID.
    :param ap_refs: List of raw string IDs or resolution dicts.
    :return: List of resolved interface graph node ID strings.
    """
    if not ap_refs:
        return ap_refs
    return [
        resolve_interface_node_id(client_factory, blueprint_id, ref) for ref in ap_refs
    ]


# ──────────────────────────────────────────────────────────────────
#  IBA Probe resolution
# ──────────────────────────────────────────────────────────────────


def resolve_probe_id(client_factory, blueprint_id, probe_ref):
    """Resolve an IBA probe reference (UUID or label) to its probe ID.

    :param client_factory: An ``ApstraClientFactory`` instance.
    :param blueprint_id: The blueprint UUID.
    :param probe_ref: The probe UUID or label.
    :return: The resolved probe ID string.
    :raises ValueError: If no matching probe is found.
    """
    if not probe_ref:
        return probe_ref

    # Fast path: already a UUID
    if _is_uuid(probe_ref):
        return probe_ref

    base = client_factory.get_base_client()
    resp = base.raw_request(f"/blueprints/{blueprint_id}/probes")
    if resp.status_code != 200:
        raise ValueError(
            f"Failed to list probes in blueprint '{blueprint_id}': "
            f"{resp.status_code} {resp.text}"
        )
    all_probes = resp.json().get("items", [])

    # Exact ID match (non-UUID IDs)
    for p in all_probes:
        if p.get("id") == probe_ref:
            return probe_ref

    # Exact label match
    for p in all_probes:
        if p.get("label") == probe_ref:
            return p["id"]

    # Case-insensitive label fallback
    ref_lower = probe_ref.lower()
    for p in all_probes:
        if (p.get("label") or "").lower() == ref_lower:
            return p["id"]

    available = [p.get("label", "") for p in all_probes]
    raise ValueError(
        f"Probe '{probe_ref}' not found in blueprint '{blueprint_id}'. "
        f"Available: {available}"
    )


def resolve_dashboard_id(client_factory, blueprint_id, dashboard_ref):
    """Resolve an IBA dashboard reference (UUID or label) to its dashboard ID.

    :param client_factory: An ``ApstraClientFactory`` instance.
    :param blueprint_id: The blueprint UUID.
    :param dashboard_ref: The dashboard UUID or label.
    :return: The resolved dashboard ID string.
    :raises ValueError: If no matching dashboard is found.
    """
    if not dashboard_ref:
        return dashboard_ref

    # Fast path: already a UUID
    if _is_uuid(dashboard_ref):
        return dashboard_ref

    base = client_factory.get_base_client()
    resp = base.raw_request(f"/blueprints/{blueprint_id}/iba/dashboards")
    if resp.status_code != 200:
        raise ValueError(
            f"Failed to list dashboards in blueprint '{blueprint_id}': "
            f"{resp.status_code} {resp.text}"
        )
    all_dashboards = resp.json().get("items", [])

    # Exact ID match (non-UUID IDs)
    for d in all_dashboards:
        if d.get("id") == dashboard_ref:
            return dashboard_ref

    # Exact label match
    for d in all_dashboards:
        if d.get("label") == dashboard_ref:
            return d["id"]

    # Case-insensitive label fallback
    ref_lower = dashboard_ref.lower()
    for d in all_dashboards:
        if (d.get("label") or "").lower() == ref_lower:
            return d["id"]

    available = [d.get("label", "") for d in all_dashboards]
    raise ValueError(
        f"Dashboard '{dashboard_ref}' not found in blueprint '{blueprint_id}'. "
        f"Available: {available}"
    )


# ──────────────────────────────────────────────────────────────────
#  Virtual Network resolution  (Phase 4)
# ──────────────────────────────────────────────────────────────────


def resolve_virtual_network_id(client_factory, blueprint_id, vn_ref):
    """Resolve a virtual-network reference (UUID or label) to its node ID.

    :param client_factory: An ``ApstraClientFactory`` instance.
    :param blueprint_id: The blueprint UUID.
    :param vn_ref: The virtual-network UUID or label.
    :return: The resolved virtual-network node ID string.
    """
    if not vn_ref or _is_uuid(vn_ref):
        return vn_ref

    results = _run_qe(
        client_factory, blueprint_id, "node('virtual_network', name='vn')"
    )
    if not results:
        raise ValueError(
            f"Virtual network '{vn_ref}' not found — no virtual networks exist in blueprint."
        )

    # Exact ID match (Apstra graph node IDs are short strings, not UUIDs)
    for r in results:
        vn = r.get("vn", {})
        if vn.get("id") == vn_ref:
            return vn_ref

    # Exact label match
    for r in results:
        vn = r.get("vn", {})
        if vn.get("label") == vn_ref:
            return vn["id"]

    # Case-insensitive fallback
    ref_lower = vn_ref.lower()
    for r in results:
        vn = r.get("vn", {})
        if (vn.get("label") or "").lower() == ref_lower:
            return vn["id"]

    available = [r.get("vn", {}).get("label", "") for r in results]
    raise ValueError(
        f"Virtual network '{vn_ref}' not found in blueprint. " f"Available: {available}"
    )


# ──────────────────────────────────────────────────────────────────
#  Global property set resolution  (Phase 5)
# ──────────────────────────────────────────────────────────────────


def resolve_property_set_id(client_factory, ps_ref):
    """Resolve a global property-set reference (UUID or label) to its ID.

    :param client_factory: An ``ApstraClientFactory`` instance.
    :param ps_ref: The property-set UUID or label.
    :return: The resolved property-set ID string.
    """
    if not ps_ref or _is_uuid(ps_ref):
        return ps_ref

    base = client_factory.get_base_client()
    result = base.property_sets.list()
    if result is None:
        all_ps = []
    elif isinstance(result, list):
        all_ps = result
    elif isinstance(result, dict) and "items" in result:
        all_ps = result["items"]
    else:
        all_ps = []

    # Exact ID match (IDs may not be UUIDs)
    for ps in all_ps:
        if ps.get("id") == ps_ref:
            return ps_ref

    # Exact label match
    for ps in all_ps:
        if ps.get("label") == ps_ref:
            return ps["id"]

    # Case-insensitive fallback
    ref_lower = ps_ref.lower()
    for ps in all_ps:
        if (ps.get("label") or "").lower() == ref_lower:
            return ps["id"]

    available = [ps.get("label", "") for ps in all_ps]
    raise ValueError(f"Property set '{ps_ref}' not found. " f"Available: {available}")


def resolve_configlet_id(client_factory, configlet_ref):
    """Resolve a catalog configlet reference (UUID or display_name) to its ID.

    :param client_factory: An ``ApstraClientFactory`` instance.
    :param configlet_ref: The configlet UUID or display_name.
    :return: The resolved configlet ID string.
    """
    if not configlet_ref or _is_uuid(configlet_ref):
        return configlet_ref

    base = client_factory.get_base_client()
    result = base.configlets.list()
    if result is None:
        all_cfg = []
    elif isinstance(result, list):
        all_cfg = result
    elif isinstance(result, dict) and "items" in result:
        all_cfg = result["items"]
    else:
        all_cfg = []

    # Exact ID match (IDs may not be UUIDs)
    for cfg in all_cfg:
        if cfg.get("id") == configlet_ref:
            return configlet_ref

    # Exact display_name match
    for cfg in all_cfg:
        if cfg.get("display_name") == configlet_ref:
            return cfg["id"]

    # Case-insensitive fallback
    ref_lower = configlet_ref.lower()
    for cfg in all_cfg:
        if (cfg.get("display_name") or "").lower() == ref_lower:
            return cfg["id"]

    available = [cfg.get("display_name", "") for cfg in all_cfg]
    raise ValueError(
        f"Configlet '{configlet_ref}' not found. " f"Available: {available}"
    )


# ──────────────────────────────────────────────────────────────────
#  CT primitives deep resolution  (Phase 2 + 4 combined)
# ──────────────────────────────────────────────────────────────────

# Fields within CT primitive attributes that contain resolvable IDs
_CT_RESOLVE_FIELDS = {
    "security_zone": "security_zone",
    "routing_zone_id": "security_zone",
    "rp_to_attach": "routing_policy",
    "vn_node_id": "virtual_network",
    "untagged_vn_node_id": "virtual_network",
}

# List fields within CT primitive attributes
_CT_RESOLVE_LIST_FIELDS = {
    "tagged_vn_node_ids": "virtual_network",
    "constraints": "security_zone",
}

# Known plural primitive type names (child groups to recurse into)
_PLURAL_PRIMITIVE_KEYS = {
    "ip_links",
    "virtual_network_singles",
    "virtual_network_multiples",
    "bgp_peering_generic_systems",
    "bgp_peering_ip_endpoints",
    "routing_policies",
    "static_routes",
    "custom_static_routes",
    "dynamic_bgp_peerings",
    "routing_zone_constraints",
}

_RESOLVERS = {
    "security_zone": resolve_security_zone_id,
    "routing_policy": resolve_routing_policy_id,
    "virtual_network": resolve_virtual_network_id,
}


def resolve_ct_primitives(client_factory, blueprint_id, primitives):
    """Walk the CT primitives tree and resolve all name references in-place.

    Modifies *primitives* dict in-place.  Handles arbitrary nesting of
    child primitives.

    :param client_factory: An ``ApstraClientFactory`` instance.
    :param blueprint_id: The blueprint UUID.
    :param primitives: The dict-of-named-dicts primitives structure.
    """
    if not primitives or not isinstance(primitives, dict):
        return

    for plural_key, instances in primitives.items():
        if not isinstance(instances, dict):
            continue
        for _inst_name, inst_config in instances.items():
            if not isinstance(inst_config, dict):
                continue
            _resolve_primitive_attrs(client_factory, blueprint_id, inst_config)


def _resolve_primitive_attrs(client_factory, blueprint_id, config):
    """Resolve ID fields in a single primitive's config dict.

    Recurses into child primitive groups.
    """
    for key, value in list(config.items()):
        # Resolve scalar ID fields
        if key in _CT_RESOLVE_FIELDS and value:
            obj_type = _CT_RESOLVE_FIELDS[key]
            resolver = _RESOLVERS[obj_type]
            config[key] = resolver(client_factory, blueprint_id, value)

        # Resolve list ID fields
        elif key in _CT_RESOLVE_LIST_FIELDS and isinstance(value, list):
            obj_type = _CT_RESOLVE_LIST_FIELDS[key]
            resolver = _RESOLVERS[obj_type]
            config[key] = [resolver(client_factory, blueprint_id, v) for v in value]

        # Recurse into child primitive groups
        elif key in _PLURAL_PRIMITIVE_KEYS and isinstance(value, dict):
            for _child_name, child_config in value.items():
                if isinstance(child_config, dict):
                    _resolve_primitive_attrs(client_factory, blueprint_id, child_config)


# ──────────────────────────────────────────────────────────────────
#  EVPN Interconnect Domain resolution
# ──────────────────────────────────────────────────────────────────


def resolve_interconnect_domain_id(client_factory, blueprint_id, domain_ref):
    """Resolve an EVPN interconnect domain reference (ID or label) to its ID.

    :param client_factory: An ``ApstraClientFactory`` instance.
    :param blueprint_id: The blueprint UUID.
    :param domain_ref: The domain ID or label.
    :return: The resolved domain ID string.
    :raises ValueError: If no matching domain is found.
    """
    if not domain_ref:
        return domain_ref

    # Deferred import to avoid circular dependencies at module load time
    from ansible_collections.juniper.apstra.plugins.module_utils.apstra.bp_interconnect_domain import (
        list_interconnect_domains,
    )

    domains = list_interconnect_domains(client_factory, blueprint_id)

    # Exact ID match (domain IDs are UUIDs or short strings)
    for domain in domains:
        if domain.get("id") == domain_ref:
            return domain_ref

    # If it already looks like a UUID and didn't match, fast-fail with helpful error
    if _is_uuid(domain_ref):
        available = [d.get("label", "") for d in domains]
        raise ValueError(
            f"Interconnect domain with ID '{domain_ref}' not found in blueprint. "
            f"Available: {available}"
        )

    # Exact label match
    for domain in domains:
        if domain.get("label") == domain_ref:
            return domain["id"]

    # Case-insensitive label fallback
    ref_lower = domain_ref.lower()
    for domain in domains:
        if (domain.get("label") or "").lower() == ref_lower:
            return domain["id"]

    available = [d.get("label", "") for d in domains]
    raise ValueError(
        f"Interconnect domain '{domain_ref}' not found in blueprint. "
        f"Available: {available}"
    )
