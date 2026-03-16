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


def resolve_pool_id(client_factory, pool_ref, pool_type):
    """Resolve a single pool reference (UUID or display_name) to its ID.

    :param client_factory: An ``ApstraClientFactory`` instance.
    :param pool_ref: The pool UUID or display_name.
    :param pool_type: The pool type ('asn', 'ip', 'ipv6', 'vni', 'vlan').
    :return: The resolved pool ID string.
    """
    if not pool_ref:
        return pool_ref

    # Fast path: already a UUID
    if _is_uuid(pool_ref):
        return pool_ref

    pools = _list_pools(client_factory, pool_type)

    # Try exact ID match (some pool IDs are human-readable strings)
    for pool in pools:
        if pool.get("id") == pool_ref:
            return pool_ref

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


def resolve_pool_ids(client_factory, pool_refs, pool_type):
    """Resolve a list of pool references to their IDs.

    :param client_factory: An ``ApstraClientFactory`` instance.
    :param pool_refs: List of pool UUIDs or display_names.
    :param pool_type: The pool type ('asn', 'ip', 'ipv6', 'vni', 'vlan').
    :return: List of resolved pool ID strings.
    """
    if not pool_refs:
        return pool_refs
    return [resolve_pool_id(client_factory, ref, pool_type) for ref in pool_refs]


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

    available = [r.get("sz", {}).get("label", "") for r in results]
    raise ValueError(
        f"Security zone '{sz_ref}' not found in blueprint. " f"Available: {available}"
    )


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
