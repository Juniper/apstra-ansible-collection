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
    Optionally waits for the device to reconnect after the reboot.
options:
  id:
    description:
      - Identifies the target device.
    type: dict
    suboptions:
      system_name:
        description:
          - The label of the system in a blueprint (requires C(id.blueprint)).
        type: str
      blueprint:
        description:
          - Blueprint name or UUID (required when using C(id.system_name)).
        type: str
      agent_id:
        description:
          - Global system-agent UUID.  Takes precedence over C(system_name).
        type: str
      hostname:
        description:
          - Management IP or hostname of the device.  Used for lookup when
            neither C(agent_id) nor C(system_name) is provided.
        type: str
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
          - Wait for the device agent to reconnect after the reboot before
            returning.
        type: bool
        default: false
      timeout:
        description:
          - Maximum seconds to wait for reconnection when
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
  - The device must be in C(connected) state and have C(management_level=full_control)
    before reboot is attempted.
  - In check mode the module reports whether a reboot would be triggered without
    issuing any API calls.
extends_documentation_fragment:
  - juniper.apstra.apstra_client
author:
  - Juniper Networks
"""

EXAMPLES = r"""
# Reboot a device by system name (blueprint context)
- name: Reboot DC2-Leaf1
  juniper.apstra.device_management:
    id:
      blueprint: DC2
      system_name: DC2-Leaf1
    state: rebooted

# Reboot and wait for the device to reconnect (5 min timeout)
- name: Reboot DC2-Leaf1 and wait for reconnection
  juniper.apstra.device_management:
    id:
      blueprint: DC2
      system_name: DC2-Leaf1
    body:
      wait_for_online: true
      timeout: 300
    state: rebooted

# Reboot using global agent ID
- name: Reboot by agent ID
  juniper.apstra.device_management:
    id:
      agent_id: "a1b2c3d4-0000-0000-0000-000000000001"
    state: rebooted

# Force reboot even when device is in a blueprint
- name: Force reboot
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
  description: True when the reboot was triggered.
  type: bool
  returned: always
msg:
  description: Human-readable status message.
  type: str
  returned: always
agent_id:
  description: The global system-agent UUID used for the operation.
  type: str
  returned: always
system_id:
  description: The device serial / MAC (system_id) from the agent status.
  type: str
  returned: when resolved
connection_state:
  description: |
    Agent connection state at the time the module returned.
    Meaningful when C(wait_for_online=true).
  type: str
  returned: always
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


def _handle_rebooted(module, client_factory):
    """Handle state=rebooted — trigger a device reboot."""
    id_params = module.params.get("id") or {}
    body = module.params.get("body") or {}

    force = bool(body.get("force", False))
    wait_for_online = bool(body.get("wait_for_online", False))
    timeout = int(body.get("timeout", 300))

    # ── Resolve agent_id ──────────────────────────────────────────────────
    agent_id = id_params.get("agent_id")
    blueprint_ref = id_params.get("blueprint")
    system_name = id_params.get("system_name")
    hostname = id_params.get("hostname")

    if not agent_id:
        # resolve_agent_id accepts system_name, hostname, or management_ip
        system_ref = system_name or hostname
        if not system_ref:
            module.fail_json(
                msg="One of 'id.agent_id', 'id.system_name', or 'id.hostname' is required."
            )
        # Resolve blueprint_id when system_name is used
        blueprint_id = None
        if blueprint_ref and system_name:
            base = client_factory.get_base_client()
            bp_list = base.blueprints.list() or []
            for bp in bp_list:
                if bp.get("label") == blueprint_ref or bp.get("id") == blueprint_ref:
                    blueprint_id = bp.get("id")
                    break
            if not blueprint_id:
                module.fail_json(
                    msg=f"Blueprint '{blueprint_ref}' not found."
                )
        agent_id = resolve_agent_id(client_factory, system_ref, blueprint_id)

    if not agent_id:
        module.fail_json(
            msg=f"Could not resolve a system agent for the given id parameters."
        )

    # ── Safety check — device must be connected and fully managed ─────────
    status = get_agent_status(client_factory, agent_id)
    connection_state = status.get("connection_state", "")
    management_level = status.get("management_level", "")

    if connection_state != "connected":
        module.fail_json(
            msg=(
                f"Device agent '{agent_id}' is not connected "
                f"(connection_state={connection_state!r}). "
                "Reboot requires the agent to be in 'connected' state."
            )
        )

    if management_level and management_level != "full_control":
        module.fail_json(
            msg=(
                f"Device agent '{agent_id}' is not fully managed "
                f"(management_level={management_level!r}). "
                "Reboot requires management_level='full_control'."
            )
        )

    # ── Check mode ────────────────────────────────────────────────────────
    if module.check_mode:
        return dict(
            changed=True,
            msg=f"Would reboot device agent '{agent_id}' (check mode — no action taken).",
            agent_id=agent_id,
            system_id=status.get("system_id", ""),
            connection_state=connection_state,
        )

    # ── Trigger reboot ────────────────────────────────────────────────────
    reboot_device(client_factory, agent_id, force=force)

    # ── Wait for reconnection (optional) ─────────────────────────────────
    if wait_for_online:
        final_state = wait_for_agent_online(client_factory, agent_id, timeout)
        if final_state != "connected":
            module.fail_json(
                msg=(
                    f"Device agent '{agent_id}' did not reconnect within "
                    f"{timeout}s after reboot (last state: {final_state!r})."
                ),
                agent_id=agent_id,
                connection_state=final_state,
            )
        return dict(
            changed=True,
            msg=f"Device agent '{agent_id}' rebooted and reconnected successfully.",
            agent_id=agent_id,
            system_id=status.get("system_id", ""),
            connection_state=final_state,
        )

    return dict(
        changed=True,
        msg=f"Reboot triggered for device agent '{agent_id}'.",
        agent_id=agent_id,
        system_id=status.get("system_id", ""),
        connection_state=connection_state,
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
