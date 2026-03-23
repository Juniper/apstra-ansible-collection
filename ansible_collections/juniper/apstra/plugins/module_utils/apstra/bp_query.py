# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

"""Blueprint query engine (QE) utilities.

Provides reusable helpers that run graph queries against an Apstra
blueprint via the REST QE endpoint (POST /api/blueprints/{id}/qe).

These helpers are consumed by:
  - modules/blueprint.py         (blueprint facts gathering)
  - modules/generic_systems.py   (internal node discovery)
  - module_utils/apstra/name_resolution.py  (ESI group / system resolution)
  - Any other module that needs to discover blueprint topology

Usage inside a module::

    from ansible_collections.juniper.apstra.plugins.module_utils.apstra.bp_query import (
        run_qe_query,
        find_nodes_by_role,
        find_interfaces_by_neighbor,
    )

    items = run_qe_query(client_factory, bp_id,
        "node('system', role='spine', name='system')")

    nodes = find_nodes_by_role(client_factory, bp_id, ['spine', 'leaf'])
    # => {'spine1': {'id': '...', 'role': 'spine', ...}, ...}
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type


# ──────────────────────────────────────────────────────────────────
#  Low-level API helpers
# ──────────────────────────────────────────────────────────────────


def _get_blueprint(client_factory, blueprint_id):
    """Return the SDK blueprint accessor ``client.blueprints[bp_id]``."""
    client = client_factory.get_base_client()
    return client.blueprints[blueprint_id]


def _node_to_dict(node):
    """Convert an SDK graph Node object to a plain dict.

    The SDK returns ``aos.sdk.graph.graph.Node`` objects from QE queries.
    Downstream consumers (modules, Jinja2 templates) expect plain dicts
    with ``id`` and all properties at the top level.
    """
    if isinstance(node, dict):
        return node
    result = {}
    if hasattr(node, "id"):
        result["id"] = node.id
    if hasattr(node, "type"):
        result["type"] = node.type
    if hasattr(node, "properties") and isinstance(node.properties, dict):
        result.update(node.properties)
    return result


# ──────────────────────────────────────────────────────────────────
#  Core QE query
# ──────────────────────────────────────────────────────────────────


def run_qe_query(client_factory, blueprint_id, query_string):
    """Run a QE graph query and return the items list.

    Uses the native SDK ``blueprints[bp_id].query()`` method which
    calls ``POST /api/blueprints/{bp_id}/qe`` internally.

    The SDK returns rich ``Node`` objects.  This function converts
    them to plain dicts (with ``id`` + properties at the top level)
    to maintain compatibility with all consumers.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        query_string: A Python-style graph query string, e.g.
            ``"node('system', role='spine', name='s')"``

    Returns:
        list[dict]: Each item is a dict whose keys are the ``name=``
        aliases from the query, and whose values are plain dicts with
        ``id`` and all node properties.
    """
    bp = _get_blueprint(client_factory, blueprint_id)
    raw_items = bp.query(query_string)
    if not raw_items:
        return []

    # Convert SDK Node objects to plain dicts
    items = []
    for raw_item in raw_items:
        item = {}
        for alias, node in raw_item.items():
            item[alias] = _node_to_dict(node)
        items.append(item)
    return items


# ──────────────────────────────────────────────────────────────────
#  Higher-level convenience helpers
# ──────────────────────────────────────────────────────────────────


def find_nodes_by_role(client_factory, blueprint_id, roles=None):
    """Discover system nodes in a blueprint, optionally filtered by role.

    Args:
        client_factory: ``ApstraClientFactory``.
        blueprint_id: Blueprint UUID.
        roles: Optional list of roles to filter, e.g.
            ``['spine', 'leaf']``.  When *None*, all system nodes are
            returned.

    Returns:
        dict: ``{label: {id, role, hostname, system_id, ...}}``
    """
    if roles:
        roles_str = ", ".join(f"'{r}'" for r in roles)
        qe = f"node('system', role=is_in([{roles_str}]), name='system')"
    else:
        qe = "node('system', name='system')"

    items = run_qe_query(client_factory, blueprint_id, qe)

    result = {}
    for item in items:
        node = item.get("system", {})
        label = node.get("label")
        if label:
            result[label] = node
    return result


def find_nodes_by_type(client_factory, blueprint_id, system_type):
    """Discover system nodes by system_type (e.g. 'server', 'switch').

    Returns:
        dict: ``{label: {id, role, hostname, system_type, ...}}``
    """
    qe = f"node('system', system_type='{system_type}', name='system')"
    items = run_qe_query(client_factory, blueprint_id, qe)

    result = {}
    for item in items:
        node = item.get("system", {})
        label = node.get("label")
        if label:
            result[label] = node
    return result


def find_interfaces_by_neighbor(
    client_factory,
    blueprint_id,
    neighbor_labels,
    neighbor_system_type="server",
    if_type="ethernet",
    local_role="leaf",
):
    """Find switch interfaces linked to specific neighbors.

    Used to discover SRX-facing or host-facing interfaces for CT
    assignment or endpoint policy.

    Args:
        client_factory: ``ApstraClientFactory``.
        blueprint_id: Blueprint UUID.
        neighbor_labels: List of neighbor system labels to match.
        neighbor_system_type: The ``system_type`` of the neighbor
            (default ``'server'``).
        if_type: Interface type filter (default ``'ethernet'``).
        local_role: Role of the local (switch) system
            (default ``'leaf'``).

    Returns:
        list[dict]: Each dict has ``intf_id``, ``intf_label``,
        ``switch_label``, ``neighbor_label``.
    """
    qe = (
        f"node('system', role='{local_role}', name='leaf')"
        ".out('hosted_interfaces')"
        f".node('interface', if_type='{if_type}', name='intf')"
        ".out('link')"
        ".node('link')"
        ".in_('link')"
        ".node('interface')"
        ".in_('hosted_interfaces')"
        f".node('system', system_type='{neighbor_system_type}', name='server')"
    )
    items = run_qe_query(client_factory, blueprint_id, qe)

    neighbor_set = set(neighbor_labels) if neighbor_labels else None
    results = []
    for item in items:
        server = item.get("server", {})
        if neighbor_set and server.get("label") not in neighbor_set:
            continue
        intf = item.get("intf", {})
        leaf = item.get("leaf", {})
        results.append(
            {
                "intf_id": intf.get("id"),
                "intf_label": intf.get("if_name", intf.get("label", "")),
                "switch_id": leaf.get("id"),
                "switch_label": leaf.get("label"),
                "neighbor_id": server.get("id"),
                "neighbor_label": server.get("label"),
            }
        )
    return results


def find_host_bond_interfaces(client_factory, blueprint_id, host_labels=None):
    """Find port-channel (bond) interfaces on host generic systems.

    Args:
        client_factory: ``ApstraClientFactory``.
        blueprint_id: Blueprint UUID.
        host_labels: Optional list of host labels to filter.

    Returns:
        dict: ``{host_label: interface_id}``
    """
    qe = (
        "node('system', system_type='server', name='server')"
        ".out('hosted_interfaces')"
        ".node('interface', if_type='port_channel', name='intf')"
    )
    items = run_qe_query(client_factory, blueprint_id, qe)

    host_set = set(host_labels) if host_labels else None
    result = {}
    for item in items:
        server = item.get("server", {})
        label = server.get("label")
        if host_set and label not in host_set:
            continue
        intf = item.get("intf", {})
        if label and intf.get("id"):
            result[label] = intf["id"]
    return result


def find_host_evpn_interfaces(client_factory, blueprint_id, host_labels=None):
    """Find ESI-LAG group interfaces (EVPN port-channels) for host systems.

    In dual-homed ESI-LAG topologies Apstra creates a virtual port-channel
    that spans the leaf pair.  These interfaces have
    ``po_control_protocol == "evpn"`` and their ``description`` follows the
    pattern ``to.<host_label>``.  They are the correct *application points*
    for VN endpoint-policy assignment.

    Args:
        client_factory: ``ApstraClientFactory``.
        blueprint_id: Blueprint UUID.
        host_labels: Optional list of host labels to filter.

    Returns:
        dict: ``{host_label: evpn_interface_id}``
    """
    qe = (
        "node('interface', if_type='port_channel',"
        " po_control_protocol='evpn', name='intf')"
    )
    items = run_qe_query(client_factory, blueprint_id, qe)

    host_set = set(host_labels) if host_labels else None
    result = {}
    for item in items:
        intf = item.get("intf", {})
        desc = intf.get("description", "") or ""
        intf_id = intf.get("id")
        if not desc.startswith("to.") or not intf_id:
            continue
        label = desc[3:]  # strip leading "to."
        if host_set and label not in host_set:
            continue
        result[label] = intf_id
    return result


def find_redundancy_groups(client_factory, blueprint_id):
    """Discover all ESI / MLAG redundancy groups and their member systems.

    Queries the blueprint graph for ``redundancy_group`` nodes and traverses
    the outgoing ``composed_of`` edges to their member ``system`` nodes.

    Args:
        client_factory: ``ApstraClientFactory``.
        blueprint_id: Blueprint UUID.

    Returns:
        dict: ``{rg_id: {"label": str, "members": [member_system_id, ...]}}`
        where *members* is a **sorted** list of member system node IDs.
        Returns an empty dict when the blueprint has no redundancy groups.
    """
    items = run_qe_query(
        client_factory,
        blueprint_id,
        "node('redundancy_group', name='rg').out().node('system', name='mbr')",
    )

    rg_map = {}
    for item in items:
        rg = item.get("rg", {})
        rg_id = rg.get("id")
        mbr_id = item.get("mbr", {}).get("id")
        if not rg_id or not mbr_id:
            continue
        if rg_id not in rg_map:
            rg_map[rg_id] = {"label": rg.get("label", ""), "members": []}
        rg_map[rg_id]["members"].append(mbr_id)

    # Sort members for deterministic ordering
    for info in rg_map.values():
        info["members"] = sorted(info["members"])

    return rg_map


# ──────────────────────────────────────────────────────────────────
#  Endpoint-policy / CT application-point query
# ──────────────────────────────────────────────────────────────────


def get_ct_application_point_ids(client_factory, blueprint_id, ct_id):
    """Return all valid interface application-point node IDs for a CT.

    Fetches the CT application-points tree via the endpoint-policy client
    (``GET /api/blueprints/{bp_id}/endpoint-policies/{ct_id}/application-points``)
    and returns a flat list of every ``type="interface"`` node ID found
    anywhere in the tree.

    Args:
        client_factory: ``ApstraClientFactory``.
        blueprint_id: Blueprint UUID.
        ct_id: The CT (batch endpoint-policy) UUID.

    Returns:
        list[str]: Interface node IDs that are valid application points.
    """
    ep_client = client_factory.get_endpointpolicy_client()
    ap_tree = (
        ep_client.blueprints[blueprint_id]
        .endpoint_policies[ct_id]
        .application_points.get()
    )

    results = []

    def _walk(node):
        if not isinstance(node, dict):
            return
        if node.get("type") == "interface" and node.get("id"):
            results.append(node["id"])
        for child in node.get("children", []):
            _walk(child)
        ap = node.get("application_points")
        if isinstance(ap, dict):
            for child in ap.get("children", []):
                _walk(child)

    _walk(ap_tree)
    return results
