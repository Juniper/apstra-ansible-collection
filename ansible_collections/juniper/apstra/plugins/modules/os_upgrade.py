#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# Apache License, Version 2.0 (see https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: os_upgrade

short_description: Manage device OS upgrades in an Apstra blueprint

version_added: "0.4.0"

author:
  - "Vamsi Gavini (@vgavini)"

description:
  - Triggers a device OS upgrade (DOS) for a single device in an Apstra blueprint.
  - Waits for the upgrade job to reach a terminal state (success or error).
  - Can also run an upgrade-impact assessment (C(state=impact_report)) or
    list all globally available OS images (C(state=gathered)).
  - Requires Apstra 6.0+ for single-device upgrade.
    Upgrade groups (C(upgrade_group.py)) require Apstra 6.1+.

options:
  api_url:
    description:
      - The URL used to access the Apstra API.
    type: str
    required: false
  verify_certificates:
    description:
      - If set to false, SSL certificates will not be verified.
    type: bool
    required: false
    default: True
  username:
    description:
      - The Apstra username for authentication.
    type: str
    required: false
  password:
    description:
      - The Apstra password for authentication.
    type: str
    required: false
  auth_token:
    description:
      - The authentication token to use if already authenticated.
    type: str
    required: false
  id:
    description:
      - A dict identifying the target blueprint and (for most states) device.
    required: false
    type: dict
    suboptions:
      blueprint:
        description:
          - The blueprint UUID or label that owns the device.
          - Required for all states.
        type: str
        required: true
      system:
        description:
          - Identifies the target system agent — accepts an agent UUID,
            device label, or management IP address.
          - Required for C(state=present).
          - When provided with C(state=impact_report), the assessment is
            scoped to that single device.  Omit to assess all blueprint
            devices.
        type: str
        required: false
  body:
    description:
      - A dict with runtime parameters for the operation.
    required: false
    type: dict
    suboptions:
      image:
        description:
          - The target OS image — accepts an image UUID, image_name
            (the .tgz/.iso filename shown in the UI), or description.
          - Required for C(state=present).
        type: str
        required: false
      agent_ids:
        description:
          - Explicit list of system-agent UUIDs to include in an
            C(impact_report).
          - Ignored for C(state=present).
          - When omitted (and C(id.system) is not set), all agents
            belonging to the blueprint are assessed.
        type: list
        elements: str
        required: false
      wait_timeout:
        description:
          - Maximum seconds to wait for the upgrade job to complete.
          - Only used by C(state=present).
        type: int
        required: false
        default: 600
  state:
    description:
      - Desired operation to perform.
      - C(present) triggers an OS upgrade on the specified device and waits
        for the job to reach a terminal state (success or error).
        The module always triggers the upgrade (non-idempotent) — use
        C(impact_report) first to assess readiness.
      - C(impact_report) runs a pre-upgrade impact assessment (read-only)
        and returns the assessment report without changing any device state.
      - C(gathered) lists all OS images currently available globally in Apstra
        and returns their metadata.  OS images are not tied to a blueprint —
        they are managed globally at ``/device-os/images``.  No changes are made.
    type: str
    required: false
    choices: ["present", "impact_report", "gathered"]
    default: "present"
"""

EXAMPLES = """
# ── List available OS images ──────────────────────────────────────

- name: Gather all available OS images (globally managed, not per-blueprint)
  juniper.apstra.os_upgrade:
    id:
      blueprint: "my-blueprint"
    state: gathered
  register: images_result

- name: Show image list
  ansible.builtin.debug:
    var: images_result.images

# ── Assess upgrade impact (all devices) ───────────────────────────

- name: Run upgrade-impact for all blueprint devices
  juniper.apstra.os_upgrade:
    id:
      blueprint: "my-blueprint"
    state: impact_report
  register: impact

- name: Show impact report
  ansible.builtin.debug:
    var: impact.impact_report

# ── Assess upgrade impact (single device) ─────────────────────────

- name: Run upgrade-impact for spine-1 only
  juniper.apstra.os_upgrade:
    id:
      blueprint: "my-blueprint"
      system: "spine-1"
    state: impact_report
  register: spine1_impact

# ── Trigger upgrade on a single device ────────────────────────────

- name: Upgrade spine-1 to a specific OS image
  juniper.apstra.os_upgrade:
    id:
      blueprint: "my-blueprint"
      system: "spine-1"
    body:
      image: "junos-21.4R3-S5.9-install-media.tgz"
      wait_timeout: 900
    state: present
  register: upgrade_result

- name: Upgrade a device using UUIDs directly
  juniper.apstra.os_upgrade:
    id:
      blueprint: "ad1cb3c1-7c83-4834-8a85-953ccf113833"
      system: "f1e2d3c4-abcd-0000-0000-000000000001"
    body:
      image: "b5a4c3d2-1111-0000-0000-000000000099"
    state: present
  register: upgrade_result

# ── Full upgrade workflow ────────────────────────────────────────

- name: 1 — Assess impact before upgrading
  juniper.apstra.os_upgrade:
    id:
      blueprint: "{{ bp_id }}"
      system: "leaf-1"
    state: impact_report
  register: impact
  failed_when: impact.impact_report.warnings | default([]) | length > 0

- name: 2 — Trigger upgrade
  juniper.apstra.os_upgrade:
    id:
      blueprint: "{{ bp_id }}"
      system: "leaf-1"
    body:
      image: "{{ target_image }}"
      wait_timeout: 900
    state: present
  register: upgrade
  when: not impact.failed
"""

RETURN = """
changed:
  description: True when an upgrade was triggered (C(state=present) only).
  type: bool
  returned: always
state:
  description: >
    Terminal state of the upgrade job — C(success) or C(error).
    Only returned for C(state=present).
  type: str
  returned: when state=present
agent_id:
  description: The system-agent UUID that was upgraded.
  type: str
  returned: when state=present
blueprint_id:
  description: The resolved blueprint UUID.
  type: str
  returned: always
image_id:
  description: The resolved OS-image UUID used for the upgrade.
  type: str
  returned: when state=present
agent:
  description: Full system-agent response dict after the job completes.
  type: dict
  returned: when state=present
images:
  description: >
    List of OS images available globally in Apstra (not blueprint-scoped).
    Each item contains C(id), C(image_name), C(description), C(platform),
    C(type), C(image_url), C(image_size), and C(checksum).
  type: list
  elements: dict
  returned: when state=gathered
impact_report:
  description: >
    The upgrade-impact response from Apstra.
    Contains per-device assessment data including warnings and
    expected side-effects.
  type: dict
  returned: when state=impact_report
agent_ids:
  description: List of agent UUIDs included in the impact assessment.
  type: list
  elements: str
  returned: when state=impact_report
msg:
  description: Human-readable summary of the operation.
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
    resolve_image_id,
    list_blueprint_images,
    list_blueprint_agent_ids,
    trigger_upgrade,
    get_upgrade_impact,
    wait_for_upgrade_job,
)


# ──────────────────────────────────────────────────────────────────
#  State handlers
# ──────────────────────────────────────────────────────────────────


def _handle_gathered(module, client_factory, blueprint_id):
    """List all OS images available globally (not blueprint-scoped)."""
    raw_images = list_blueprint_images(client_factory, blueprint_id)

    images = []
    for img in raw_images:
        images.append(
            {
                "id": img.get("id", ""),
                "image_name": img.get("image_name", "") or img.get("filename", ""),
                "description": img.get("description", "") or img.get("label", ""),
                "platform": img.get("platform", ""),
                "type": img.get("type", ""),
                "image_url": img.get("image_url", ""),
                "image_size": img.get("image_size", 0),
                "checksum": img.get("checksum", ""),
            }
        )

    return dict(
        changed=False,
        blueprint_id=blueprint_id,
        images=images,
        msg=f"gathered {len(images)} globally available OS image(s)",
    )


def _handle_impact_report(module, client_factory, blueprint_id):
    """Run an upgrade-impact assessment."""
    id_param = module.params.get("id") or {}
    body = module.params.get("body") or {}

    system_ref = id_param.get("system")
    explicit_agent_ids = (body.get("agent_ids") or []) if body else []

    # Determine which agent IDs to assess
    if system_ref:
        agent_id = resolve_agent_id(
            client_factory, system_ref, blueprint_id=blueprint_id
        )
        agent_ids = [agent_id]
    elif explicit_agent_ids:
        agent_ids = explicit_agent_ids
    else:
        # Default — assess all agents in the blueprint
        agent_ids = list_blueprint_agent_ids(client_factory, blueprint_id)

    if not agent_ids:
        return dict(
            changed=False,
            blueprint_id=blueprint_id,
            agent_ids=[],
            impact_report={},
            msg="No system agents found in blueprint — nothing to assess",
        )

    impact = get_upgrade_impact(client_factory, blueprint_id, agent_ids)

    return dict(
        changed=False,
        blueprint_id=blueprint_id,
        agent_ids=agent_ids,
        impact_report=impact or {},
        msg=f"upgrade-impact assessed for {len(agent_ids)} agent(s)",
    )


def _handle_present(module, client_factory, blueprint_id):
    """Trigger an OS upgrade on a single device and wait for completion."""
    id_param = module.params.get("id") or {}
    body = module.params.get("body") or {}

    system_ref = id_param.get("system")
    image_ref = body.get("image")
    wait_timeout = body.get("wait_timeout", 600)

    if not system_ref:
        raise ValueError(
            "'id.system' is required for state=present. "
            "Provide an agent UUID, device label, or management IP."
        )
    if not image_ref:
        raise ValueError(
            "'body.image' is required for state=present. "
            "Provide an OS image UUID, image_name, or description."
        )

    # Resolve identifiers
    agent_id = resolve_agent_id(client_factory, system_ref, blueprint_id=blueprint_id)
    image_id = resolve_image_id(client_factory, blueprint_id, image_ref)

    # Trigger the upgrade
    trigger_upgrade(client_factory, blueprint_id, agent_id, image_id)

    # Wait for the job to finish — raises on error or timeout
    job_result = wait_for_upgrade_job(
        client_factory, blueprint_id, agent_id, wait_timeout
    )

    return dict(
        changed=True,
        blueprint_id=blueprint_id,
        agent_id=agent_id,
        image_id=image_id,
        state=job_result["state"],
        agent=job_result["agent"],
        msg=job_result["message"],
    )


# ──────────────────────────────────────────────────────────────────
#  Module entry point
# ──────────────────────────────────────────────────────────────────


def main():
    object_module_args = dict(
        id=dict(type="dict", required=False),
        body=dict(type="dict", required=False),
        state=dict(
            type="str",
            required=False,
            choices=["present", "impact_report", "gathered"],
            default="present",
        ),
    )
    client_module_args = apstra_client_module_args()
    module_args = client_module_args | object_module_args

    result = dict(changed=False)

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)

    try:
        client_factory = ApstraClientFactory.from_params(module)

        # Resolve blueprint_id — required for all states
        id_param = module.params.get("id") or {}
        blueprint_ref = id_param.get("blueprint")
        if not blueprint_ref:
            module.fail_json(
                msg="'id.blueprint' is required. Provide a blueprint UUID or label."
            )

        blueprint_id = client_factory.resolve_blueprint_id(blueprint_ref)

        state = module.params["state"]
        if state == "gathered":
            result = _handle_gathered(module, client_factory, blueprint_id)
        elif state == "impact_report":
            result = _handle_impact_report(module, client_factory, blueprint_id)
        elif state == "present":
            result = _handle_present(module, client_factory, blueprint_id)

    except Exception as e:
        tb = traceback.format_exc()
        module.debug(f"Exception occurred: {str(e)}\n\nStack trace:\n{tb}")
        result.pop("msg", None)
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
