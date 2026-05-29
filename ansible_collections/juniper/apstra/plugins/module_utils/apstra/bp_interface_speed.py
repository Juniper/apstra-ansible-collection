# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

"""Blueprint interface speed utilities.

Provides reusable helpers for changing physical link speed on blueprint
interfaces via the official Apstra WebUI APIs:

    PUT /blueprints/{id}/set-physical-link-speed
    PUT /blueprints/{id}/set-switch-system-link-speed

Link resolution strategy
------------------------
The ``link_id`` required by those endpoints is obtained by a single
blueprint graph query (QE):

    node('system', label=<system>)
      .out('hosted_interfaces')
      .node('interface', if_name=<if_name>, name='ifc')
      .out()
      .node('link', name='lnk')

This returns the link node directly, including its ``id`` (used as
``link_id``), ``speed`` (current speed string, e.g. ``"100G"``), and
``role`` (used to select the correct API endpoint).

This approach works for both normal design IMs and blueprint-local IMs
(Apstra v6.1.1): for connected ports the blueprint graph interface node
always carries ``if_name``; ``if_name=None`` only appears on
disconnected/unassigned ports which have no link attached anyway.

Idempotency
-----------
The current link speed is read from the link node ``speed`` field in the
same QE call.  If it already matches the desired speed the module returns
``changed=False`` without calling any write API.

Speed validation
----------------
Before applying the change, the desired speed is checked against the
device-profile transforms for the interface.  An informative error lists
the supported speeds when the requested value is invalid.

These helpers are consumed by:
    - modules/interface_map.py  (state=speed_updated)

Usage inside a module::

    from ansible_collections.juniper.apstra.plugins.module_utils.apstra.bp_interface_speed import (
        SpeedChangeError,
        normalize_speed,
        change_interface_speed,
        get_im_for_system,
        get_effective_im_node,
        im_has_transform_id,
    )

    try:
        result = change_interface_speed(
            client_factory, blueprint_id, system_name,
            if_name, desired_value, desired_unit, speed_str, check_mode,
        )
    except SpeedChangeError as exc:
        module.fail_json(msg=str(exc))
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
import re

from ansible_collections.juniper.apstra.plugins.module_utils.apstra.bp_query import (
    run_qe_query,
)

# ──────────────────────────────────────────────────────────────────
#  Constants
# ──────────────────────────────────────────────────────────────────

# Link roles that require set-switch-system-link-speed instead of
# set-physical-link-speed (mirrors Apstra WebUI logic).
_SWITCH_SYS_ROLES = frozenset({"to_generic", "access_l3", "to_access_switch"})


# ──────────────────────────────────────────────────────────────────
#  Public exception
# ──────────────────────────────────────────────────────────────────


class SpeedChangeError(Exception):
    """Raised when a speed change cannot be completed.

    Callers should catch this and call ``module.fail_json(msg=str(exc))``.
    """


# ──────────────────────────────────────────────────────────────────
#  Speed string helpers
# ──────────────────────────────────────────────────────────────────


def normalize_speed(speed_str):
    """Normalize a speed string to a ``(value, unit)`` tuple.

    Accepted formats: ``"25G"``, ``"25g"``, ``"100G"``, ``"10G"``, etc.

    Args:
        speed_str (str): Raw speed string from playbook params.

    Returns:
        tuple[int, str]: ``(value, unit)`` e.g. ``(100, "G")``.

    Raises:
        SpeedChangeError: If the string cannot be parsed.
    """
    m = re.match(r"^(\d+)\s*([A-Za-z]+)$", speed_str.strip())
    if not m:
        raise SpeedChangeError(
            "Cannot parse speed '{0}'. "
            "Expected format like '25G', '100G', '10G'.".format(speed_str)
        )
    return int(m.group(1)), m.group(2).upper()


# ──────────────────────────────────────────────────────────────────
#  SDK client helper
# ──────────────────────────────────────────────────────────────────


def _get_client(client_factory):
    """Return the l3clos SDK client."""
    return client_factory.get_l3clos_client()


# ──────────────────────────────────────────────────────────────────
#  Link resolution via blueprint graph QE
# ──────────────────────────────────────────────────────────────────


def find_link_via_qe(client_factory, blueprint_id, system_name, if_name):
    """Find the physical link for a system interface using a graph QE.

    Traverses the blueprint graph::

        node('system', label=<system_name>)
          .out('hosted_interfaces')
          .node('interface', if_name=<if_name>, name='ifc')
          .out()
          .node('link', name='lnk')

    The ``link`` node carries ``id`` (the ``link_id`` needed by
    ``set-physical-link-speed``), ``speed`` (current speed string, e.g.
    ``"100G"``), and ``role`` (used to select the correct write API).

    This works for both normal design IMs and blueprint-local IMs
    (Apstra v6.1.1).  For connected ports the blueprint graph interface
    node always carries ``if_name``; ``if_name=None`` only appears on
    disconnected/unassigned ports which have no link attached anyway.

    Args:
        client_factory: ``ApstraClientFactory``.
        blueprint_id (str): Blueprint UUID.
        system_name (str): Blueprint node label, e.g. ``"DC2-Leaf1"``.
        if_name (str): Interface name, e.g. ``"et-0/0/49"``.

    Returns:
        tuple: ``(link_id, current_speed, link_role)`` or
        ``(None, None, None)`` when not found.
    """
    qe_str = (
        "node('system', label='{0}', name='sys')"
        ".out('hosted_interfaces')"
        ".node('interface', if_name='{1}', name='ifc')"
        ".out()"
        ".node('link', name='lnk')"
    ).format(system_name, if_name)

    items = run_qe_query(client_factory, blueprint_id, qe_str)
    if not items:
        return None, None, None

    lnk = items[0].get("lnk", {})
    return lnk.get("id"), lnk.get("speed", ""), lnk.get("role", "")


# ──────────────────────────────────────────────────────────────────
#  Interface map assignment helpers
# ──────────────────────────────────────────────────────────────────


def get_im_assignments(client_factory, blueprint_id):
    """Return the IM assignment dict ``{system_node_id: im_id}``."""
    client = _get_client(client_factory)
    result = client.blueprints[blueprint_id].get_im_assignments()
    if result and isinstance(result, dict):
        return result
    return {}


def get_im_for_system(client_factory, blueprint_id, system_name):
    """Resolve ``system_name`` to ``(system_node_id, im_id)``.

    Args:
        client_factory: ``ApstraClientFactory``.
        blueprint_id (str): Blueprint UUID.
        system_name (str): Blueprint node label of the target switch.

    Returns:
        tuple[str, str]: ``(system_node_id, im_id)``.

    Raises:
        SpeedChangeError: If the system or IM assignment is not found.
    """
    qe = "node('system', label='{0}', name='sys')".format(system_name)
    items = run_qe_query(client_factory, blueprint_id, qe)
    if not items:
        raise SpeedChangeError(
            "System '{0}' not found in blueprint '{1}'".format(
                system_name, blueprint_id
            )
        )
    system_node_id = items[0].get("sys", {}).get("id")
    if not system_node_id:
        raise SpeedChangeError(
            "System '{0}' graph node has no id".format(system_name)
        )

    assignments = get_im_assignments(client_factory, blueprint_id)
    im_id = assignments.get(system_node_id)
    if not im_id:
        raise SpeedChangeError(
            "No interface map assignment found for system '{0}'. "
            "Assign an interface map before changing port speed.".format(system_name)
        )

    return system_node_id, im_id


# ──────────────────────────────────────────────────────────────────
#  Interface map node helpers
# ──────────────────────────────────────────────────────────────────


def get_blueprint_im_node(client_factory, blueprint_id, im_id):
    """Fetch the blueprint-level IM node.

    Returns:
        dict: The IM node properties dict, or empty dict if not found.
    """
    client = _get_client(client_factory)
    try:
        return (
            client.request(
                "/blueprints/{0}/nodes/{1}".format(blueprint_id, im_id),
                method="GET",
            )
            or {}
        )
    except Exception:
        return {}


def get_design_im(client_factory, im_id):
    """Fetch a design-level interface map by ID.

    Returns:
        dict: The design IM dict, or empty dict if not found.
    """
    client = _get_client(client_factory)
    try:
        return (
            client.request(
                "/design/interface-maps/{0}".format(im_id), method="GET"
            )
            or {}
        )
    except Exception:
        return {}


def get_effective_im_node(client_factory, blueprint_id, im_id):
    """Return the best available IM node — blueprint-local first, then design.

    Blueprint-local IMs (``_v2`` variants) only exist at the blueprint level;
    they are not in the design catalog.

    Returns:
        dict: IM node properties dict (non-empty).

    Raises:
        SpeedChangeError: If neither source returns a usable IM.
    """
    im_node = get_blueprint_im_node(client_factory, blueprint_id, im_id)
    if im_node and im_node.get("interfaces"):
        return im_node
    im_node = get_design_im(client_factory, im_id)
    if im_node and im_node.get("interfaces"):
        return im_node
    raise SpeedChangeError(
        "Interface map '{0}' not found at blueprint or design level.".format(im_id)
    )


def find_im_entry(im_node, if_name):
    """Find the IM interface entry for ``if_name``.

    Args:
        im_node (dict): IM node from ``get_effective_im_node``.
        if_name (str): Interface name, e.g. ``"et-0/0/49"``.

    Returns:
        dict or None: The matching entry dict, or ``None`` if not found.
    """
    for entry in im_node.get("interfaces", []):
        entry_name = entry.get("name") or entry.get("if_name")
        if entry_name == if_name:
            return entry
    return None


def parse_im_entry_setting(entry):
    """Parse ``entry['setting']['param']`` JSON into a plain dict.

    The IM setting is stored as a JSON string inside ``setting.param``.

    Returns:
        dict: Parsed setting dict.  Returns empty dict on parse failure.
    """
    raw = entry.get("setting", {}).get("param", "{}")
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return {}


def im_has_transform_id(im_node, if_name, transform_id):
    """Return ``True`` if ``if_name`` already uses ``transform_id``.

    Checks ``mapping[1]`` of the matching interface entry.
    """
    for entry in im_node.get("interfaces", []):
        entry_name = entry.get("name") or entry.get("if_name")
        if entry_name == if_name:
            mapping = entry.get("mapping", [])
            current_tid = mapping[1] if len(mapping) > 1 else None
            return current_tid == transform_id
    return False


# ──────────────────────────────────────────────────────────────────
#  Device profile helpers (speed validation)
# ──────────────────────────────────────────────────────────────────


def get_dp_ports(client_factory, blueprint_id, im_id):
    """Return device profile port list for the given blueprint IM.

    Traverses ``interface_map → device_profile`` in the blueprint graph.

    Returns:
        list: Port list with transformations, or empty list.
    """
    qe = (
        "node('interface_map', id='{0}', name='im')"
        ".out().node('device_profile', name='dp')".format(im_id)
    )
    items = run_qe_query(client_factory, blueprint_id, qe)
    if not items:
        return []
    return items[0].get("dp", {}).get("ports", [])


def find_transform_for_speed(dp_ports, if_name, desired_value, desired_unit):
    """Return the ``transformation_id`` for a non-breakout port at given speed.

    Searches each port's transformations for one whose sole interface matches
    ``if_name`` and speed ``(desired_value, desired_unit)``.

    Returns:
        int or None: Matching transformation_id, or ``None`` if not found.
    """
    for port in dp_ports:
        for transform in port.get("transformations", []):
            ifaces = transform.get("interfaces", [])
            if len(ifaces) == 1 and ifaces[0].get("name") == if_name:
                sp = ifaces[0].get("speed", {})
                if (
                    sp.get("value") == desired_value
                    and sp.get("unit", "").upper() == desired_unit
                ):
                    return transform["transformation_id"]
    return None


def list_speeds_for_iface(dp_ports, if_name):
    """Return unique non-breakout speeds available for ``if_name``.

    Returns:
        list[str]: E.g. ``["40G", "100G"]``.
    """
    seen = []
    for port in dp_ports:
        for transform in port.get("transformations", []):
            ifaces = transform.get("interfaces", [])
            if len(ifaces) == 1 and ifaces[0].get("name") == if_name:
                sp = ifaces[0].get("speed", {})
                label = "{0}{1}".format(sp.get("value", "?"), sp.get("unit", ""))
                if label not in seen:
                    seen.append(label)
    return seen


# ──────────────────────────────────────────────────────────────────
#  Speed apply operation
# ──────────────────────────────────────────────────────────────────


def set_link_speed(client_factory, blueprint_id, link_id, link_role, value, unit):
    """Call ``set-physical-link-speed`` or ``set-switch-system-link-speed``.

    Selects the correct Apstra API based on ``link_role``:

    - Access / generic-system links (``to_generic``, ``access_l3``,
      ``to_access_switch``) → ``set-switch-system-link-speed``
    - All other roles (e.g. ``spine_leaf``) → ``set-physical-link-speed``

    Apstra updates both the topology link speed and the interface map
    automatically.

    Args:
        client_factory: ``ApstraClientFactory``.
        blueprint_id (str): Blueprint UUID.
        link_id (str): The link UUID from the blueprint graph.
        link_role (str): Link role string, e.g. ``"spine_leaf"``.
        value (int): Speed value, e.g. ``100``.
        unit (str): Speed unit, e.g. ``"G"``.

    Raises:
        SpeedChangeError: On API failure.
    """
    client = _get_client(client_factory)
    payload = {
        "links": [
            {
                "link_id": link_id,
                "speed": {"unit": unit, "value": value},
            }
        ]
    }
    try:
        if link_role in _SWITCH_SYS_ROLES:
            client.blueprints[blueprint_id].set_switch_system_link_speed(payload)
        else:
            client.blueprints[blueprint_id].set_physical_link_speed(payload)
    except Exception as exc:
        raise SpeedChangeError(
            "Speed change API failed for link '{0}': {1}".format(link_id, exc)
        )


# ──────────────────────────────────────────────────────────────────
#  Top-level speed change orchestrator
# ──────────────────────────────────────────────────────────────────


def change_interface_speed(
    client_factory,
    blueprint_id,
    system_name,
    if_name,
    desired_value,
    desired_unit,
    speed_str,
    check_mode=False,
):
    """Change the speed of a physical interface.

    Workflow:

    1. **Link resolution** — Run a blueprint graph QE to find the link
       attached to ``(system_name, if_name)``.  The QE returns ``link_id``,
       current ``link_speed``, and ``link_role`` in a single call.

    2. **Speed validation** — Check the desired speed against the
       device-profile transforms.  Fail early with a list of supported
       speeds if the value is invalid.

    3. **Idempotency** — Compare ``link.speed`` against ``desired_speed``.
       Return ``changed=False`` without any write API call if already set.

    4. **Apply** — Call ``set-physical-link-speed`` or
       ``set-switch-system-link-speed`` based on ``link_role``.

    Args:
        client_factory: ``ApstraClientFactory``.
        blueprint_id (str): Blueprint UUID.
        system_name (str): Blueprint node label of the target switch.
        if_name (str): Interface name, e.g. ``"et-0/0/49"``.
        desired_value (int): Speed value from ``normalize_speed``.
        desired_unit (str): Speed unit from ``normalize_speed``.
        speed_str (str): Original speed string for messages, e.g. ``"100G"``.
        check_mode (bool): When ``True``, report the intended change
            without applying it.

    Returns:
        dict: Ansible result with ``changed`` (bool) and ``msg`` (str).

    Raises:
        SpeedChangeError: On any unrecoverable error.  The caller should
            call ``module.fail_json(msg=str(exc))``.
    """
    desired_speed_str = "{0}{1}".format(desired_value, desired_unit)

    # ── Step 1: find the link via blueprint graph QE ───────────────────────
    link_id, current_speed, link_role = find_link_via_qe(
        client_factory, blueprint_id, system_name, if_name
    )

    if not link_id:
        raise SpeedChangeError(
            "Interface '{0}' not found on system '{1}' in the blueprint "
            "graph (no connected link).  Verify the interface name and that "
            "a physical link is present in the cabling map.".format(
                if_name, system_name
            )
        )

    # ── Step 2: validate desired speed against device profile ──────────────
    _system_node_id, im_id = get_im_for_system(
        client_factory, blueprint_id, system_name
    )
    dp_ports = get_dp_ports(client_factory, blueprint_id, im_id)
    transform_id = find_transform_for_speed(
        dp_ports, if_name, desired_value, desired_unit
    )
    if transform_id is None:
        available = list_speeds_for_iface(dp_ports, if_name)
        raise SpeedChangeError(
            "Speed {0} is not valid for interface '{1}' on '{2}'.  "
            "Available speeds: {3}".format(
                speed_str, if_name, system_name,
                available or "none found in device profile",
            )
        )

    # ── Step 3: idempotency check ──────────────────────────────────────────
    if current_speed == desired_speed_str:
        return dict(
            changed=False,
            msg=(
                "Link speed of '{0}' on '{1}' is already {2} "
                "(no change)".format(if_name, system_name, speed_str)
            ),
        )

    # ── Step 4: check_mode ─────────────────────────────────────────────────
    if check_mode:
        return dict(
            changed=True,
            msg=(
                "Would change link speed of '{0}' on '{1}' "
                "from {2} to {3}".format(
                    if_name, system_name, current_speed, speed_str
                )
            ),
        )

    # ── Step 5: apply via set-physical-link-speed ──────────────────────────
    set_link_speed(
        client_factory, blueprint_id, link_id, link_role, desired_value, desired_unit
    )

    return dict(
        changed=True,
        msg=(
            "Link speed of '{0}' on '{1}' changed "
            "from {2} to {3}".format(
                if_name, system_name, current_speed, speed_str
            )
        ),
    )
