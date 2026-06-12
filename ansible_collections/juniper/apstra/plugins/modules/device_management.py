# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: device_management
short_description: Manage physical devices through Apstra (reboot, etc.)
version_added: "1.0.0"
description:
  - Provides lifecycle operations for devices managed by Apstra.
  - C(state=rebooted) — Triggers a device reboot via the system agent.
    Accepts a single device or a list of devices.
    Optionally waits for each device to reconnect after the reboot.
options:
  id:
    description:
      - Identifies the target device(s).
      - For a single device use C(agent_id), C(system_name), or C(hostname).
      - For multiple devices use C(agent_ids), C(system_names), or C(hostnames).
    type: dict
    suboptions:
      agent_id:
        description:
          - Global system-agent UUID (single device).
        type: str
      agent_ids:
        description:
          - List of global system-agent UUIDs (multiple devices).
        type: list
        elements: str
      system_name:
        description:
          - Blueprint node label for a single device (requires C(id.blueprint)).
        type: str
      system_names:
        description:
          - List of blueprint node labels (requires C(id.blueprint)).
        type: list
        elements: str
      blueprint:
        description:
          - Blueprint name or UUID (required when using C(id.system_name) or
            C(id.system_names)).
        type: str
      hostname:
        description:
          - Management IP or hostname of a single device.  Used for lookup
            when neither C(agent_id) nor C(system_name) is provided.
        type: str
      hostnames:
        description:
          - List of management IPs or hostnames (multiple devices).
        type: list
        elements: str
  body:
    description:
      - Operation-specific parameters.
    type: dict
    suboptions:
      force:
        description:
          - Force the reboot even when the device is actively managed in a
            blueprint.  Use with caution.
        type: bool
        default: false
      wait_for_online:
        description:
          - Wait for each device agent to reconnect after the reboot before
            returning.
        type: bool
        default: false
      timeout:
        description:
          - Maximum seconds to wait for reconnection per device when
            C(wait_for_online=true).
        type: int
        default: 300
  state:
    description:
      - Desired operation.
      - C(rebooted) — Trigger a device reboot via the system agent.
    type: str
    required: true
    choices: ["rebooted"]
notes:
  - Each device must be in C(connected) state and have
    C(management_level=full_control) before reboot is attempted.
  - In check mode the module reports which devices would be rebooted without
    issuing any API calls.
  - When multiple devices are specified a C(results) list is returned with
    per-device outcome.  C(changed) is True when at least one device was
    rebooted.
extends_documentation_fragment:
  - juniper.apstra.apstra_client
author:
  - Juniper Networks
"""

EXAMPLES = r"""
# Reboot a single device by blueprint system name
- name: Reboot DC2-Leaf1
  juniper.apstra.device_management:
    id:
      blueprint: DC2
      system_name: DC2-Leaf1
    state: rebooted

# Reboot multiple devices by system names
- name: Reboot DC2 leaf devices
  juniper.apstra.device_management:
    id:
      blueprint: DC2
      system_names:
        - DC2-Leaf1
        - DC2-Leaf2
    body:
      force: true
    state: rebooted

# Reboot multiple devices and wait for reconnection
- name: Reboot and wait
  juniper.apstra.device_management:
    id:
      blueprint: DC2
      system_names:
        - DC2-Leaf1
        - DC2-Leaf2
    body:
      wait_for_online: true
      timeout: 300
    state: rebooted

# Reboot using a list of agent IDs
- name: Reboot by agent IDs
  juniper.apstra.device_management:
    id:
      agent_ids:
        - "a1b2c3d4-0000-0000-0000-000000000001"
        - "a1b2c3d4-0000-0000-0000-000000000002"
    state: rebooted

# Reboot a single device by agent ID
- name: Reboot by agent ID
  juniper.apstra.device_management:
    id:
      agent_id: "a1b2c3d4-0000-0000-0000-000000000001"
    state: rebooted

# Force reboot a single device with wait
- name: Force reboot with wait
  juniper.apstra.device_management:
    id:
      blueprint: DC2
      system_name: DC2-Leaf1
    body:
      force: true
      wait_for_online: true
      timeout: 600
    state: rebooted
"""

RETURN = r"""
changed:
  description: True when at least one reboot was triggered.
  type: bool
  returned: always
msg:
  description: Human-readable status message.
  type: str
  returned: always
agent_id:
  description: The system-agent UUID (single-device result only).
  type: str
  returned: when a single device was specified
system_id:
  description: The device serial / MAC from the agent status (single-device only).
  type: str
  returned: when a single device was specified
connection_state:
  description: Agent connection state at the time the module returned (single-device only).
  type: str
  returned: when a single device was specified
results:
  description: >
    Per-device result list when multiple devices were specified.
    Each entry contains agent_id, changed, msg, and connection_state.
  type: list
  elements: dict
  returned: when multiple devices were specified
"""

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.client import (
    apstra_client_module_args,
    ApstraClientFactory,
)
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.upgrade import (
    resolve_agent_id,
)
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.device_mgmt import (
    get_agent_status,
    reboot_device,
    wait_for_agent_online,
)


# ---------------------------------------------------------------------------
# State handlers
# ---------------------------------------------------------------------------


def _resolve_blueprint_id(client_factory, blueprint_ref):
    """Resolve a blueprint label or UUID to its UUID."""
    base = client_factory.get_base_client()
    bp_list = base.blueprints.list() or []
    for bp in bp_list:
        if bp.get("label") == blueprint_ref or bp.get("id") == blueprint_ref:
            return bp.get("id")
    raise ValueError(f"Blueprint '{blueprint_ref}' not found.")


def _resolve_single_agent(client_factory, id_params):
    """Resolve one id dict entry (agent_id/system_name/hostname) to an agent_id."""
    agent_id = id_params.get("agent_id")
    blueprint_ref = id_params.get("blueprint")
    system_name = id_params.get("system_name")
    hostname = id_params.get("hostname")

    if agent_id:
        return agent_id

    system_ref = system_name or hostname
    if not system_ref:
        raise ValueError(
            "One of 'id.agent_id', 'id.system_name', or 'id.hostname' is required."
        )

    blueprint_id = None
    if blueprint_ref and system_name:
        blueprint_id = _resolve_blueprint_id(client_factory, blueprint_ref)

    return resolve_agent_id(client_factory, system_ref, blueprint_id)


def _handle_rebooted(module, client_factory):
    """Handle state=rebooted — trigger a reboot on one or more devices."""
    id_params = module.params.get("id") or {}
    body = module.params.get("body") or {}

    force = bool(body.get("force", False))
    wait_for_online = bool(body.get("wait_for_online", False))
    timeout = int(body.get("timeout", 300))

    # ── Build list of per-device id dicts ─────────────────────────────────
    blueprint_ref = id_params.get("blueprint")

    if id_params.get("agent_ids"):
        target_dicts = [{"agent_id": aid} for aid in id_params["agent_ids"]]
    elif id_params.get("system_names"):
        target_dicts = [
            {"system_name": name, "blueprint": blueprint_ref}
            for name in id_params["system_names"]
        ]
    elif id_params.get("hostnames"):
        target_dicts = [{"hostname": h} for h in id_params["hostnames"]]
    else:
        # Single-device: use id_params as-is
        target_dicts = [id_params]

    multi = len(target_dicts) > 1

    # ── Resolve all agent IDs upfront (fail early if any lookup fails) ────
    resolved = []
    for td in target_dicts:
        try:
            agent_id = _resolve_single_agent(client_factory, td)
        except Exception as e:
            module.fail_json(msg=str(e))
        resolved.append(agent_id)

    # ── Safety-check all devices before rebooting any ─────────────────────
    statuses = {}
    failed_safety = []
    for agent_id in resolved:
        status = get_agent_status(client_factory, agent_id)
        statuses[agent_id] = status
        conn = status.get("connection_state", "")
        mgmt = status.get("management_level", "")
        if conn != "connected":
            failed_safety.append(
                f"agent '{agent_id}': not connected (connection_state={conn!r})"
            )
        elif mgmt and mgmt != "full_control":
            failed_safety.append(
                f"agent '{agent_id}': not fully managed (management_level={mgmt!r})"
            )

    if failed_safety:
        module.fail_json(
            msg="Reboot safety check failed — "
            + "; ".join(failed_safety)
        )

    # ── Check mode ────────────────────────────────────────────────────────
    if module.check_mode:
        if multi:
            results = [
                dict(
                    agent_id=aid,
                    changed=True,
                    msg=f"Would reboot agent '{aid}' (check mode).",
                    connection_state=statuses[aid].get("connection_state", ""),
                )
                for aid in resolved
            ]
            return dict(
                changed=True,
                msg=f"Would reboot {len(resolved)} device(s) (check mode — no action taken).",
                results=results,
            )
        agent_id = resolved[0]
        status = statuses[agent_id]
        return dict(
            changed=True,
            msg=f"Would reboot device agent '{agent_id}' (check mode — no action taken).",
            agent_id=agent_id,
            system_id=status.get("system_id", ""),
            connection_state=status.get("connection_state", ""),
        )

    # ── Reboot all devices ────────────────────────────────────────────────
    results = []
    any_changed = False

    for agent_id in resolved:
        status = statuses[agent_id]
        reboot_device(client_factory, agent_id, force=force)
        any_changed = True

        if wait_for_online:
            final_state = wait_for_agent_online(client_factory, agent_id, timeout)
            if final_state != "connected":
                results.append(dict(
                    agent_id=agent_id,
                    changed=True,
                    failed=True,
                    msg=(
                        f"Agent '{agent_id}' did not reconnect within {timeout}s "
                        f"after reboot (last state: {final_state!r})."
                    ),
                    connection_state=final_state,
                ))
                continue
            results.append(dict(
                agent_id=agent_id,
                changed=True,
                msg=f"Agent '{agent_id}' rebooted and reconnected successfully.",
                connection_state=final_state,
                system_id=status.get("system_id", ""),
            ))
        else:
            results.append(dict(
                agent_id=agent_id,
                changed=True,
                msg=f"Reboot triggered for agent '{agent_id}'.",
                connection_state=status.get("connection_state", ""),
                system_id=status.get("system_id", ""),
            ))

    # ── Check for post-reboot wait failures ───────────────────────────────
    failed = [r for r in results if r.get("failed")]
    if failed:
        module.fail_json(
            msg=f"Reboot failed for {len(failed)} agent(s): "
                + "; ".join(r["msg"] for r in failed),
            results=results,
            changed=any_changed,
        )

    # ── Flatten for single-device case ────────────────────────────────────
    if not multi:
        r = results[0]
        return dict(
            changed=r["changed"],
            msg=r["msg"],
            agent_id=r["agent_id"],
            system_id=r.get("system_id", ""),
            connection_state=r["connection_state"],
        )

    return dict(
        changed=any_changed,
        msg=f"Reboot triggered for {len(results)} device(s).",
        results=results,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    object_module_args = dict(
        id=dict(type="dict", required=False),
        body=dict(type="dict", required=False),
        state=dict(
            type="str",
            required=True,
            choices=["rebooted"],
        ),
    )
    module_args = apstra_client_module_args() | object_module_args

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    result = dict(changed=False)

    try:
        client_factory = ApstraClientFactory.from_params(module)
        state = module.params["state"]

        if state == "rebooted":
            result = _handle_rebooted(module, client_factory)

    except Exception as e:
        tb = traceback.format_exc()
        module.debug(f"Exception occurred: {str(e)}\n\nStack trace:\n{tb}")
        result.pop("msg", None)
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
