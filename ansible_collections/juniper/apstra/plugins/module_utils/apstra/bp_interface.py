# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

"""Blueprint interface utilities.

Provides reusable helpers for reading and patching blueprint interface
nodes via the Apstra REST API.

Primary use cases:
  - Set ``operation_state`` (admin up/down) on interface nodes
  - Set ``tags`` on interface nodes (ethernet or port_channel)
  - Set ``lag_mode`` and ``port_channel_id`` on port_channel interface nodes
  - Resolve interface nodes via graph queries

These helpers are consumed by:
  - modules/blueprint.py  (state=interface_updated, interface_tagged, lag_updated)

Usage inside a module::

    from ansible_collections.juniper.apstra.plugins.module_utils.apstra.bp_interface import (
        find_interface_node,
        set_operation_state,
        set_interface_tags,
        set_lag_mode,
    )

    iface = find_interface_node(client_factory, bp_id, "leaf1", "ge-0/0/0")
    result = set_operation_state(client_factory, bp_id, iface["id"], "down")
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.juniper.apstra.plugins.module_utils.apstra.bp_query import (
    run_qe_query,
)
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.bp_nodes import (
    get_node,
    patch_node,
    node_needs_update,
)

# ──────────────────────────────────────────────────────────────────
#  Admin state mapping
# ──────────────────────────────────────────────────────────────────

# Apstra stores the interface admin-down state as "admin_down" in the
# operation_state field.  The module param uses "up" / "down" as values.
_ADMIN_STATE_MAP = {
    "up": "up",
    "down": "admin_down",
}

# Valid lag_mode values accepted by Apstra
_VALID_LAG_MODES = frozenset({"lacp_active", "lacp_passive", "static_lag", "none"})


# ──────────────────────────────────────────────────────────────────
#  Interface node discovery
# ──────────────────────────────────────────────────────────────────


def find_interface_node(client_factory, blueprint_id, system_label, if_name):
    """Resolve a system label + interface name to an interface node dict.

    Runs a blueprint graph query (QE) to find the interface node
    ``if_name`` that is hosted on the system with label ``system_label``.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        system_label: The blueprint node label for the switch/system
            (e.g. ``"leaf1"``).
        if_name: The interface name (e.g. ``"ge-0/0/0"`` or ``"ae4"``).

    Returns:
        dict or None: The interface node properties dict (including ``id``),
        or *None* if not found.
    """
    qe = (
        f"node('system', label='{system_label}', name='sys')"
        f".out('hosted_interfaces')"
        f".node('interface', if_name='{if_name}', name='iface')"
    )
    items = run_qe_query(client_factory, blueprint_id, qe)
    if not items:
        return None
    return items[0].get("iface")


def find_interface_nodes_by_type(
    client_factory, blueprint_id, system_label, if_type=None
):
    """Find all interface nodes hosted on a system, optionally filtered by if_type.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        system_label: The blueprint node label for the switch/system.
        if_type: Optional interface type filter, e.g. ``"ethernet"``
            or ``"port_channel"``.  When *None*, all interfaces are returned.

    Returns:
        list[dict]: List of interface node property dicts.
    """
    if if_type:
        qe = (
            f"node('system', label='{system_label}', name='sys')"
            f".out('hosted_interfaces')"
            f".node('interface', if_type='{if_type}', name='iface')"
        )
    else:
        qe = (
            f"node('system', label='{system_label}', name='sys')"
            f".out('hosted_interfaces')"
            f".node('interface', name='iface')"
        )
    items = run_qe_query(client_factory, blueprint_id, qe)
    return [item["iface"] for item in items if item.get("iface")]


# ──────────────────────────────────────────────────────────────────
#  Feature 2: Interface admin state (shut / no-shut)
# ──────────────────────────────────────────────────────────────────


def set_operation_state(client_factory, blueprint_id, iface_id, admin_state):
    """Set the admin state of an interface node (shut / no-shut).

    In Apstra v6, the interface node ``operation_state`` field is used to
    configure interface shutdown:

    * ``"up"`` — interface is administratively enabled (no-shut).
    * ``"admin_down"`` — interface is administratively disabled (shut).

    This function accepts the human-readable ``admin_state`` values
    ``"up"`` and ``"down"`` and maps them to the Apstra ``operation_state``
    values before patching.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        iface_id: The interface node UUID in the blueprint.
        admin_state: ``"up"`` (no-shut) or ``"down"`` (shut).

    Returns:
        dict: ``{changed, node_id, admin_state, operation_state, msg}``
    """
    desired_op_state = _ADMIN_STATE_MAP.get(admin_state)
    if desired_op_state is None:
        raise ValueError(
            f"Invalid admin_state '{admin_state}'. "
            f"Valid values: {sorted(_ADMIN_STATE_MAP.keys())}"
        )

    current = get_node(client_factory, blueprint_id, iface_id)
    if current is None:
        raise ValueError(
            f"Interface node '{iface_id}' not found in blueprint '{blueprint_id}'"
        )

    current_op_state = current.get("operation_state")

    # Treat None (unset) as "up" for idempotency purposes
    effective_current = current_op_state if current_op_state is not None else "up"

    if effective_current == desired_op_state:
        return dict(
            changed=False,
            node_id=iface_id,
            admin_state=admin_state,
            operation_state=current_op_state,
            msg=f"Interface already in admin_state='{admin_state}' (no change)",
        )

    patch_node(
        client_factory,
        blueprint_id,
        iface_id,
        {"operation_state": desired_op_state},
    )

    return dict(
        changed=True,
        node_id=iface_id,
        admin_state=admin_state,
        operation_state=desired_op_state,
        msg=f"Interface admin_state set to '{admin_state}' (operation_state='{desired_op_state}')",
    )


# ──────────────────────────────────────────────────────────────────
#  Feature 3: Interface tags
# ──────────────────────────────────────────────────────────────────


def _get_current_tags(client_factory, blueprint_id, iface_id):
    """Return the list of tag labels currently applied to an interface node.

    Uses the blueprint graph to read ``type='tag'`` relationships that
    point TO the interface node.  This is the authoritative source — the
    Apstra UI also reads these graph relationships (not the node's ``tags``
    property field).

    Returns:
        list[str]: Tag labels currently applied.
    """
    qe = f"node(id='{iface_id}', name='n').in_('tag').node('tag', name='t')"
    items = run_qe_query(client_factory, blueprint_id, qe)
    return [item["t"]["label"] for item in items if item.get("t")]


def _ensure_tags_exist(client_factory, blueprint_id, tag_labels):
    """Ensure tag objects exist in the blueprint for all given labels.

    ``POST /blueprints/{id}/tagging`` silently ignores labels that do not
    have a corresponding tag object.  This helper creates any missing tag
    objects via ``POST /blueprints/{id}/tags`` before the tagging API is
    called.

    Args:
        tag_labels: Iterable of tag label strings to ensure exist.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(f"/blueprints/{blueprint_id}/nodes?node_type=tag")
    if resp.status_code not in (200, 201, 202):
        raise RuntimeError(
            f"GET /nodes?node_type=tag failed: HTTP {resp.status_code} — {resp.text}"
        )
    existing_labels = {
        v["label"] for v in resp.json().get("nodes", {}).values() if v.get("label")
    }
    for label in tag_labels:
        if label not in existing_labels:
            cr = base.raw_request(
                f"/blueprints/{blueprint_id}/tags",
                method="POST",
                data={"label": label},
            )
            if cr.status_code not in (200, 201, 202):
                raise RuntimeError(
                    f"Failed to create tag '{label}': "
                    f"HTTP {cr.status_code} — {cr.text}"
                )


def _call_tagging_api(client_factory, blueprint_id, iface_id, add, remove):
    """POST /blueprints/{id}/tagging to add/remove tag graph relationships.

    This is the only correct way to tag nodes so that the Apstra UI shows
    the tags.  Patching the node's ``tags`` property directly does NOT
    create the required ``type='tag'`` graph edges.

    Args:
        add: List of tag label strings to add (pass ``[]`` or ``None`` to skip).
        remove: List of tag label strings to remove (pass ``[]`` or ``None`` to skip).
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(
        f"/blueprints/{blueprint_id}/tagging",
        method="POST",
        data={
            "nodes": [iface_id],
            "add": add if add else None,
            "remove": remove if remove else None,
        },
    )
    if resp.status_code not in (200, 201, 202):
        raise RuntimeError(
            f"POST /tagging failed: HTTP {resp.status_code} — {resp.text}"
        )


def set_interface_tags(client_factory, blueprint_id, iface_id, tags, state="present"):
    """Set or remove tags on an interface node using the Apstra tagging API.

    Uses ``POST /blueprints/{id}/tagging`` which creates proper ``type='tag'``
    graph relationships between the tag node and the interface node.  This is
    the only approach that makes tags visible in the Apstra UI.

    Tag objects are automatically created in the blueprint when ``state=present``
    if they do not yet exist.

    Idempotent: reads current tag relationships before deciding whether to
    call the tagging API.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        iface_id: The interface node UUID.
        tags: List of tag label strings to add (``state=present``) or
            remove (``state=absent``).
        state: ``"present"`` (ensure tags exist) or ``"absent"``
            (ensure tags are removed).

    Returns:
        dict: ``{changed, node_id, tags, msg}``
    """
    current_tags = _get_current_tags(client_factory, blueprint_id, iface_id)
    desired_tags = list(tags or [])

    if state == "present":
        to_add = [t for t in desired_tags if t not in current_tags]
        if not to_add:
            return dict(
                changed=False,
                node_id=iface_id,
                tags=current_tags,
                msg="Tags already present (no change)",
            )
        _ensure_tags_exist(client_factory, blueprint_id, to_add)
        _call_tagging_api(
            client_factory, blueprint_id, iface_id, add=to_add, remove=None
        )
        return dict(
            changed=True,
            node_id=iface_id,
            tags=list(set(current_tags + to_add)),
            msg=f"Added tags: {to_add}",
        )

    elif state == "absent":
        to_remove = [t for t in desired_tags if t in current_tags]
        if not to_remove:
            return dict(
                changed=False,
                node_id=iface_id,
                tags=current_tags,
                msg="Tags already absent (no change)",
            )
        _call_tagging_api(
            client_factory, blueprint_id, iface_id, add=None, remove=to_remove
        )
        new_tags = [t for t in current_tags if t not in to_remove]
        return dict(
            changed=True,
            node_id=iface_id,
            tags=new_tags,
            msg=f"Removed tags: {to_remove}",
        )

    else:
        raise ValueError(f"Invalid state '{state}'. Use 'present' or 'absent'.")


# ──────────────────────────────────────────────────────────────────
#  Feature 4: LAG mode
# ──────────────────────────────────────────────────────────────────


def set_lag_mode(
    client_factory, blueprint_id, iface_id, lag_mode, port_channel_id=None
):
    """Set the LAG mode (and optionally port_channel_id) on an interface node.

    This is used for port_channel (LAG) interfaces on managed switches.
    Valid ``lag_mode`` values: ``lacp_active``, ``lacp_passive``,
    ``static_lag``, ``none``.

    Args:
        client_factory: An ``ApstraClientFactory`` instance.
        blueprint_id: The blueprint UUID.
        iface_id: The interface node UUID (should be a ``port_channel``
            interface for this operation to be meaningful).
        lag_mode: The desired LAG mode string.
        port_channel_id: Optional integer port channel / AE interface
            number (e.g. ``4`` for ``ae4``).  When *None*, the existing
            ``port_channel_id`` is left unchanged.

    Returns:
        dict: ``{changed, node_id, lag_mode, port_channel_id, msg}``
    """
    if lag_mode not in _VALID_LAG_MODES:
        raise ValueError(
            f"Invalid lag_mode '{lag_mode}'. "
            f"Valid values: {sorted(_VALID_LAG_MODES)}"
        )

    current = get_node(client_factory, blueprint_id, iface_id)
    if current is None:
        raise ValueError(
            f"Interface node '{iface_id}' not found in blueprint '{blueprint_id}'"
        )

    desired = {"lag_mode": lag_mode}
    if port_channel_id is not None:
        desired["port_channel_id"] = port_channel_id

    changes = node_needs_update(current, desired)
    if not changes:
        return dict(
            changed=False,
            node_id=iface_id,
            lag_mode=current.get("lag_mode"),
            port_channel_id=current.get("port_channel_id"),
            msg="LAG configuration already up to date (no change)",
        )

    patch_node(client_factory, blueprint_id, iface_id, changes)
    final_lag_mode = changes.get("lag_mode", current.get("lag_mode"))
    final_pc_id = changes.get("port_channel_id", current.get("port_channel_id"))

    return dict(
        changed=True,
        node_id=iface_id,
        lag_mode=final_lag_mode,
        port_channel_id=final_pc_id,
        msg=(
            f"LAG configuration updated: "
            + ", ".join(f"{k}={v}" for k, v in changes.items())
        ),
    )
