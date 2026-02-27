# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

"""Blueprint node utilities.

Provides reusable helpers for reading and patching blueprint nodes
via the Apstra REST API.

Primary use cases:
  - Assign a physical device serial (``system_id``) to a blueprint node
  - Set ``deploy_mode`` on one or more nodes
  - Read node details (hostname, role, system_id, etc.)

These helpers are consumed by:
  - modules/blueprint_node.py  (playbook-facing module)
  - modules/generic_systems.py (internal node patching)

Usage inside a module::

    from ansible_collections.juniper.apstra.plugins.module_utils.apstra.bp_nodes import (
        get_node,
        patch_node,
        list_nodes,
    )

    node = get_node(client_factory, bp_id, node_id)
    patch_node(client_factory, bp_id, node_id,
               {"system_id": "SERIAL123"})
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type


# ──────────────────────────────────────────────────────────────────
#  SDK client helpers
# ──────────────────────────────────────────────────────────────────

# Fields that the Apstra API allows patching without allow_unsafe=true
_SAFE_PATCH_FIELDS = frozenset({"label", "deploy_mode", "system_id", "hostname"})


def _get_blueprint(client_factory, blueprint_id):
    """Return the SDK blueprint accessor ``client.blueprints[bp_id]``."""
    client = client_factory.get_base_client()
    return client.blueprints[blueprint_id]


# ──────────────────────────────────────────────────────────────────
#  Node read operations
# ──────────────────────────────────────────────────────────────────


def get_node(client_factory, blueprint_id, node_id):
    """Read a single blueprint node via the SDK.

    Uses ``client.blueprints[bp_id].nodes[node_id].get()``.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        node_id: The node UUID within the blueprint.

    Returns:
        dict or None: The node properties dict, or *None* if not found.
    """
    bp = _get_blueprint(client_factory, blueprint_id)
    return bp.nodes[node_id].get()


def list_nodes(client_factory, blueprint_id):
    """List all blueprint nodes via the SDK.

    Uses ``client.blueprints[bp_id].nodes.list()``  which returns
    the ``nodes`` dict directly (keyed by node ID).

    Returns:
        dict: Mapping of ``{node_id: node_dict}``.  Returns empty dict
        on error.
    """
    bp = _get_blueprint(client_factory, blueprint_id)
    result = bp.nodes.list()
    return result or {}


# ──────────────────────────────────────────────────────────────────
#  Node write operations
# ──────────────────────────────────────────────────────────────────


def patch_node(client_factory, blueprint_id, node_id, data):
    """Update fields on a single blueprint node via the SDK.

    Uses ``client.blueprints[bp_id].nodes[node_id].update(data, allow_unsafe=...)``.
    Automatically sets ``allow_unsafe=True`` when any field outside
    ``_SAFE_PATCH_FIELDS`` is present in the data payload.

    Args:
        client_factory: ``ApstraClientFactory``.
        blueprint_id: Blueprint UUID.
        node_id: Node UUID.
        data: Dict of fields to patch.  Common fields:
            - ``system_id`` -- physical device serial number
            - ``deploy_mode`` -- ``"deploy"`` / ``"undeploy"`` / ``"drain"``
            - ``hostname`` -- device hostname
            - ``label`` -- display label
            - ``if_name`` -- interface name (requires allow_unsafe)
            - ``external`` -- external flag (requires allow_unsafe)

    Returns:
        dict: The API response (may be empty on 204).
    """
    unsafe_fields = set(data.keys()) - _SAFE_PATCH_FIELDS
    allow_unsafe = bool(unsafe_fields)

    bp = _get_blueprint(client_factory, blueprint_id)
    return bp.nodes[node_id].update(data, allow_unsafe=allow_unsafe)


def patch_nodes_bulk(client_factory, blueprint_id, data):
    """Bulk-update multiple blueprint nodes via the SDK.

    Uses ``client.blueprints[bp_id].nodes.update(data, allow_unsafe=True)``.

    Args:
        client_factory: ``ApstraClientFactory``.
        blueprint_id: Blueprint UUID.
        data: Dict payload for bulk node update (keyed by node_id).

    Returns:
        dict: The API response.
    """
    bp = _get_blueprint(client_factory, blueprint_id)
    return bp.nodes.update(data, allow_unsafe=True)


# ──────────────────────────────────────────────────────────────────
#  Convenience helpers
# ──────────────────────────────────────────────────────────────────


def assign_system_id(client_factory, blueprint_id, node_id, system_id):
    """Assign a physical device serial number to a blueprint node.

    This is the primary operation for binding a real device to a
    blueprint switch placeholder.

    Args:
        client_factory: ``ApstraClientFactory``.
        blueprint_id: Blueprint UUID.
        node_id: The blueprint node UUID (e.g. from QE query).
        system_id: The device serial number (from system agents).

    Returns:
        dict: The patch response.
    """
    return patch_node(
        client_factory,
        blueprint_id,
        node_id,
        {
            "system_id": system_id,
        },
    )


def set_deploy_mode(client_factory, blueprint_id, node_id, deploy_mode):
    """Set the deploy mode on a blueprint node.

    Args:
        client_factory: ``ApstraClientFactory``.
        blueprint_id: Blueprint UUID.
        node_id: Node UUID.
        deploy_mode: One of ``"deploy"``, ``"undeploy"``, ``"drain"``,
            ``"ready"``.

    Returns:
        dict: The patch response.
    """
    return patch_node(
        client_factory,
        blueprint_id,
        node_id,
        {
            "deploy_mode": deploy_mode,
        },
    )


def node_needs_update(current_node, desired):
    """Compare current node state with desired fields.

    Args:
        current_node: The current node dict from the API.
        desired: Dict of desired field values.

    Returns:
        dict: Only the fields that need changing.  Empty dict means
        no update needed.
    """
    changes = {}
    for key, value in desired.items():
        current_value = current_node.get(key)
        if current_value != value:
            changes[key] = value
    return changes
