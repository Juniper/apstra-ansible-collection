# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

"""Blueprint query engine (QE) utilities.

Provides reusable helpers that run graph queries against an Apstra
blueprint via the REST QE endpoint (POST /api/blueprints/{id}/qe).

These helpers are consumed by:
  - modules/blueprint_query.py  (playbook-facing module)
  - modules/generic_systems.py  (internal node discovery)
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
