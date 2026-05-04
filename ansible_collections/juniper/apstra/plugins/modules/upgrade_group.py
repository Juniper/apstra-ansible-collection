#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# Apache License, Version 2.0 (see https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: upgrade_group

short_description: Manage Apstra OS upgrade groups

version_added: "0.4.0"

author:
  - "Vamsi Gavini (@vgavini)"

description:
  - Manages OS upgrade groups in Apstra 6.1+.
  - Upgrade groups are implicit — they are string labels stored in each
    device's C(user_config.upgrade_group) field.  There is no dedicated
    group resource; creating a group means assigning devices to a named
    group label.  Dissolving a group means resetting all its members to
    the C(default) group.
  - Requires Apstra 6.1 or later.  On older versions the C(user_config)
    field is still present but the C(upgrade_group) key may be ignored;
    the module will still succeed at the API level.

options:
  api_url:
    description: The URL used to access the Apstra API.
    type: str
    required: false
  verify_certificates:
    description: If false, SSL certificates are not verified.
    type: bool
    required: false
    default: True
  username:
    description: Apstra username for authentication.
    type: str
    required: false
  password:
    description: Apstra password for authentication.
    type: str
    required: false
  auth_token:
    description: Authentication token (if already authenticated).
    type: str
    required: false
  id:
    description:
      - Identifies the upgrade group to operate on.
    required: false
    type: dict
    suboptions:
      name:
        description:
          - The upgrade group name.
          - Required for C(state=present), C(state=absent), and
            C(state=impact_report).
          - Omit for C(state=gathered) to list all groups.
        type: str
        required: false
      blueprint:
        description:
          - Blueprint UUID or label used to resolve device node labels
            to system IDs.
          - Optional but required when C(body.members) contains device
            labels as they appear in an Apstra blueprint (e.g.
            C(apstra_esi_001_leaf1)).
          - Not needed if members are specified as management IPs or
            device keys (MAC/serial).
        type: str
        required: false
  body:
    description:
      - Parameters for the operation.
    required: false
    type: dict
    suboptions:
      members:
        description:
          - List of devices to include in the group.
          - Each entry may be a blueprint node label (requires
            C(id.blueprint)), management IP address, or device key
            (MAC/serial).
          - Required for C(state=present).
          - Optional for C(state=absent) — when provided, only those
            specific devices are removed from the group (reset to
            C(default)).  When omitted the entire group is dissolved.
        type: list
        elements: str
        required: false
  state:
    description:
      - Desired operation.
      - C(present) ensures the listed C(body.members) belong to the
        named group.  Devices already in the group are left unchanged
        (idempotent).  Devices in the group that are NOT listed are
        NOT removed — use C(state=absent) first to dissolve cleanly.
      - C(absent) dissolves the group.  When C(body.members) is
        provided, only those members are removed from the group
        (reset to C(default)).  When omitted, every device currently
        in the group is reset to C(default), effectively deleting the
        group.
      - C(gathered) lists all upgrade groups and their current
        members.  Read-only, no changes made.  When C(id.name) is
        provided only that group is returned.
      - C(impact_report) runs a pre-upgrade impact assessment for all
        members of the named group.  Read-only, no device changes.
    type: str
    required: false
    choices: ["present", "absent", "gathered", "impact_report"]
    default: "present"
"""

EXAMPLES = """
# ── List all groups and members ──────────────────────────────────

- name: Gather all upgrade groups
  juniper.apstra.upgrade_group:
    state: gathered
  register: groups_result

- name: Show groups
  ansible.builtin.debug:
    var: groups_result.groups

# ── List a specific group ─────────────────────────────────────────

- name: Gather spines group
  juniper.apstra.upgrade_group:
    id:
      name: "spines"
    state: gathered
  register: spines_group

# ── Create a group / add devices by blueprint label ───────────────

- name: Create "spines" upgrade group
  juniper.apstra.upgrade_group:
    id:
      name: "spines"
      blueprint: "apstra-pod1"
    body:
      members:
        - "spine1"
        - "spine2"
    state: present

# ── Create a group using management IPs (no blueprint needed) ─────

- name: Create "leaves" upgrade group by IP
  juniper.apstra.upgrade_group:
    id:
      name: "leaves"
    body:
      members:
        - "172.20.34.13"
        - "172.20.34.14"
        - "172.20.34.15"
    state: present

# ── Run upgrade-impact assessment for a group ─────────────────────

- name: Assess upgrade impact for spines group
  juniper.apstra.upgrade_group:
    id:
      name: "spines"
    state: impact_report
  register: impact

- name: Show impact
  ansible.builtin.debug:
    var: impact.impact_report

# ── Remove specific devices from a group ─────────────────────────

- name: Remove spine1 from spines group
  juniper.apstra.upgrade_group:
    id:
      name: "spines"
      blueprint: "apstra-pod1"
    body:
      members:
        - "spine1"
    state: absent

# ── Dissolve an entire group ──────────────────────────────────────

- name: Dissolve spines group (all members go back to default)
  juniper.apstra.upgrade_group:
    id:
      name: "spines"
    state: absent

# ── Full upgrade-group workflow ───────────────────────────────────

- name: 1 Create spines group
  juniper.apstra.upgrade_group:
    id:
      name: "spines"
      blueprint: "{{ bp_id }}"
    body:
      members: ["spine1", "spine2"]
    state: present

- name: 2 Impact assessment before upgrade
  juniper.apstra.upgrade_group:
    id:
      name: "spines"
    state: impact_report
  register: impact

- name: 3a Trigger upgrade SEQUENTIALLY (one device at a time — safe default)
  juniper.apstra.os_upgrade:
    id:
      blueprint: "{{ bp_id }}"
      system: "{{ item }}"
    body:
      image: "{{ target_image }}"
      wait_timeout: 1800
    state: present
  loop: "{{ impact.agent_ids }}"
  when: not impact.failed

# ── OR ── parallel upgrade (matches WebUI behaviour) ─────────────

- name: 3b Trigger upgrade IN PARALLEL (all devices simultaneously — like WebUI)
  juniper.apstra.os_upgrade:
    id:
      blueprint: "{{ bp_id }}"
      system: "{{ item }}"
    body:
      image: "{{ target_image }}"
      wait_timeout: 1800
    state: present
  loop: "{{ impact.agent_ids }}"
  when: not impact.failed
  async: 1800   # must be >= wait_timeout; tells Ansible to run the task asynchronously
  poll: 0       # fire and move on immediately — do not wait before launching next device
  register: upgrade_jobs

- name: 3b Wait for all parallel upgrades to complete
  ansible.builtin.async_status:
    jid: "{{ item.ansible_job_id }}"
  loop: "{{ upgrade_jobs.results | selectattr('ansible_job_id', 'defined') | list }}"
  register: job_results
  until: job_results.finished
  retries: 120
  delay: 30
  when: not impact.failed

- name: 4 Dissolve group after upgrade
  juniper.apstra.upgrade_group:
    id:
      name: "spines"
    state: absent

# ── Mixed OS types in one group (JunOS + JunOS-EVO) ───────────────
#
# Option A (recommended): use separate upgrade groups per OS type so
# each group maps cleanly to one image.  Create "spines-junos" and
# "spines-evo", then run the workflow above for each group.
#
# Option B: single group, filter by os_family at playbook level.
# The gathered member dicts include os_family / os_variant / os_version
# so you can split agent_ids into two lists and apply different images.

- name: Gather group members (includes os_family per device)
  juniper.apstra.upgrade_group:
    id:
      name: "mixed-spines"
    state: gathered
  register: grp

- name: Build per-OS agent lists
  ansible.builtin.set_fact:
    junos_keys:     "{{ grp.groups['mixed-spines'] | selectattr('os_variant', 'ne', 'qfx-ms-fixed') | map(attribute='device_key') | list }}"
    evo_keys:       "{{ grp.groups['mixed-spines'] | selectattr('os_variant', 'equalto', 'qfx-ms-fixed') | map(attribute='device_key') | list }}"

- name: Upgrade JunOS devices
  juniper.apstra.os_upgrade:
    id:
      blueprint: "{{ bp_id }}"
      system: "{{ item }}"
    body:
      image: "jinstall-host-qfx-5e-x86-64-23.4R2-S6.10-secure-signed.tgz"
      wait_timeout: 1800
    state: present
  loop: "{{ junos_keys }}"
  async: 1800
  poll: 0
  register: junos_jobs

- name: Upgrade JunOS-EVO devices
  juniper.apstra.os_upgrade:
    id:
      blueprint: "{{ bp_id }}"
      system: "{{ item }}"
    body:
      image: "junos-evo-install-qfx-ms-x86-64-23.4R2-S6.9-EVO.iso"
      wait_timeout: 1800
    state: present
  loop: "{{ evo_keys }}"
  async: 1800
  poll: 0
  register: evo_jobs

- name: Wait for all upgrades to complete
  ansible.builtin.async_status:
    jid: "{{ item.ansible_job_id }}"
  loop: >-
    {{ (junos_jobs.results | default([]) + evo_jobs.results | default([]))
       | selectattr('ansible_job_id', 'defined') | list }}
  register: all_results
  until: all_results.finished
  retries: 120
  delay: 30
"""

RETURN = """
changed:
  description: True when one or more device group assignments were modified.
  type: bool
  returned: always
group_name:
  description: The upgrade group name operated on.
  type: str
  returned: when state=present, absent, or impact_report
groups:
  description: >
    Dict mapping group name → list of member dicts.
    Each member dict contains C(device_key), C(mgmt_ip), C(hostname),
    C(upgrade_group), C(os_family), C(os_variant), C(os_version),
    and C(user_config) (full).
  type: dict
  returned: when state=gathered
members_changed:
  description: List of device_keys whose group assignment was changed.
  type: list
  elements: str
  returned: when state=present or absent
members_current:
  description: >
    Current members of the group after the operation.
    Each item contains C(device_key), C(mgmt_ip), C(hostname),
    C(os_family), C(os_variant), C(os_version), and C(user_config).
  type: list
  elements: dict
  returned: when state=present or absent
impact_report:
  description: >
    The upgrade-impact response from Apstra.
    Contains per-device assessment data.
  type: dict
  returned: when state=impact_report
agent_ids:
  description: Agent UUIDs that were included in the impact assessment.
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
    list_all_systems,
    get_group_members,
    resolve_device_key,
    set_upgrade_group,
    get_upgrade_impact,
    _build_system_id_to_agent_map,
)


_DEFAULT_GROUP = "default"


# ──────────────────────────────────────────────────────────────────
#  Internal helpers
# ──────────────────────────────────────────────────────────────────


def _system_summary(system):
    """Return a compact, human-friendly dict for a /systems item."""
    facts = system.get("facts", {})
    return {
        "device_key": system.get("device_key", ""),
        "mgmt_ip": facts.get("mgmt_ipaddr", ""),
        "hostname": facts.get("hostname", ""),
        "upgrade_group": system.get("user_config", {}).get("upgrade_group", ""),
        "os_family": facts.get("os_family", ""),
        "os_variant": facts.get("os_variant", ""),
        "os_version": facts.get("os_version", ""),
        "user_config": system.get("user_config", {}),
    }


def _resolve_members(client_factory, member_refs, blueprint_id):
    """Resolve a list of device references to device_keys.

    Raises ``ValueError`` on first unresolvable reference.
    """
    return [
        resolve_device_key(client_factory, ref, blueprint_id=blueprint_id)
        for ref in member_refs
    ]


# ──────────────────────────────────────────────────────────────────
#  State handlers
# ──────────────────────────────────────────────────────────────────


def _handle_gathered(module, client_factory, group_name):
    """List all upgrade groups (or a single named group) and their members."""
    items, all_group_names = list_all_systems(client_factory)

    # Build group → members map
    groups = {}
    for system in items:
        grp = system.get("user_config", {}).get("upgrade_group", _DEFAULT_GROUP)
        groups.setdefault(grp, []).append(_system_summary(system))

    # Ensure all known groups appear (even if 0 members)
    for gn in all_group_names:
        groups.setdefault(gn, [])

    if group_name:
        # Scope to requested group
        scoped = {group_name: groups.get(group_name, [])}
        return dict(
            changed=False,
            groups=scoped,
            msg=(
                f"group '{group_name}' has " f"{len(scoped[group_name])} member(s)"
                if group_name in groups
                else f"group '{group_name}' does not exist"
            ),
        )

    total = sum(len(v) for v in groups.values())
    return dict(
        changed=False,
        groups=groups,
        msg=f"gathered {len(groups)} upgrade group(s) with {total} total device(s)",
    )


def _handle_present(module, client_factory, group_name, blueprint_id):
    """Ensure listed members belong to the group.  Additive + idempotent."""
    body = module.params.get("body") or {}
    member_refs = body.get("members") or []

    if not member_refs:
        raise ValueError(
            "'body.members' is required for state=present. "
            "Provide a list of device references to add to the group."
        )

    # Resolve all member refs to device_keys first (fail fast on bad refs)
    device_keys = _resolve_members(client_factory, member_refs, blueprint_id)

    # Build a current user_config cache to avoid repeated GETs
    items, _groups = list_all_systems(client_factory)
    uc_cache = {s["device_key"]: s.get("user_config", {}) for s in items}

    changed_keys = []
    for dk in device_keys:
        current_uc = uc_cache.get(dk)
        was_changed = set_upgrade_group(
            client_factory, dk, group_name, current_user_config=current_uc
        )
        if was_changed:
            changed_keys.append(dk)

    # Refresh to return current state
    current_members = get_group_members(client_factory, group_name)

    return dict(
        changed=bool(changed_keys),
        group_name=group_name,
        members_changed=changed_keys,
        members_current=[_system_summary(s) for s in current_members],
        msg=(
            f"{len(changed_keys)} device(s) added to group '{group_name}'"
            if changed_keys
            else f"all {len(device_keys)} device(s) already in group '{group_name}'"
        ),
    )


def _handle_absent(module, client_factory, group_name, blueprint_id=None):
    """Remove members from the group (specific or all) — reset to 'default'."""
    body = module.params.get("body") or {}
    member_refs = body.get("members") or []

    if member_refs:
        # Remove only specified members
        device_keys = _resolve_members(client_factory, member_refs, blueprint_id)
    else:
        # Dissolve entire group — collect all current members
        current_members = get_group_members(client_factory, group_name)
        device_keys = [s["device_key"] for s in current_members]

    if not device_keys:
        return dict(
            changed=False,
            group_name=group_name,
            members_changed=[],
            members_current=[],
            msg=f"group '{group_name}' is already empty / does not exist",
        )

    # Build user_config cache
    items, _groups = list_all_systems(client_factory)
    uc_cache = {s["device_key"]: s.get("user_config", {}) for s in items}

    changed_keys = []
    for dk in device_keys:
        current_uc = uc_cache.get(dk, {})
        # Only reset if actually in this group (idempotent)
        if current_uc.get("upgrade_group") == group_name:
            was_changed = set_upgrade_group(
                client_factory, dk, _DEFAULT_GROUP, current_user_config=current_uc
            )
            if was_changed:
                changed_keys.append(dk)

    # Remaining members after operation
    remaining = get_group_members(client_factory, group_name)

    return dict(
        changed=bool(changed_keys),
        group_name=group_name,
        members_changed=changed_keys,
        members_current=[_system_summary(s) for s in remaining],
        msg=(
            f"{len(changed_keys)} device(s) removed from group '{group_name}' "
            f"(reset to '{_DEFAULT_GROUP}')"
            if changed_keys
            else f"no devices were in group '{group_name}' — nothing changed"
        ),
    )


def _handle_impact_report(module, client_factory, group_name):
    """Run upgrade-impact assessment for all devices in the group."""
    # Get current group members
    members = get_group_members(client_factory, group_name)

    if not members:
        return dict(
            changed=False,
            group_name=group_name,
            agent_ids=[],
            impact_report={},
            msg=f"group '{group_name}' has no members — nothing to assess",
        )

    # Map device_key → agent_id (device_key == system_id)
    sys_to_agent = _build_system_id_to_agent_map(client_factory)
    agent_ids = [
        sys_to_agent[s["device_key"]]
        for s in members
        if s["device_key"] in sys_to_agent
    ]

    if not agent_ids:
        return dict(
            changed=False,
            group_name=group_name,
            agent_ids=[],
            impact_report={},
            msg=(
                f"group '{group_name}' has {len(members)} member(s) but "
                "none could be mapped to a system agent"
            ),
        )

    impact = get_upgrade_impact(client_factory, None, agent_ids)

    return dict(
        changed=False,
        group_name=group_name,
        agent_ids=agent_ids,
        impact_report=impact or {},
        msg=f"upgrade-impact assessed for {len(agent_ids)} device(s) in group '{group_name}'",
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
            choices=["present", "absent", "gathered", "impact_report"],
            default="present",
        ),
    )
    client_module_args = apstra_client_module_args()
    module_args = client_module_args | object_module_args

    result = dict(changed=False)

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)

    try:
        client_factory = ApstraClientFactory.from_params(module)

        id_param = module.params.get("id") or {}
        group_name = id_param.get("name")
        blueprint_ref = id_param.get("blueprint")

        state = module.params["state"]

        # Validate required params per state
        if state in ("present", "absent", "impact_report") and not group_name:
            module.fail_json(
                msg=(
                    f"'id.name' is required for state={state}. "
                    "Provide the upgrade group name."
                )
            )

        # Optionally resolve blueprint label → ID for member label lookup
        blueprint_id = None
        if blueprint_ref:
            blueprint_id = client_factory.resolve_blueprint_id(blueprint_ref)

        if state == "gathered":
            result = _handle_gathered(module, client_factory, group_name)
        elif state == "present":
            result = _handle_present(module, client_factory, group_name, blueprint_id)
        elif state == "absent":
            result = _handle_absent(module, client_factory, group_name, blueprint_id)
        elif state == "impact_report":
            result = _handle_impact_report(module, client_factory, group_name)

    except Exception as e:
        tb = traceback.format_exc()
        module.debug(f"Exception occurred: {str(e)}\n\nStack trace:\n{tb}")
        result.pop("msg", None)
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
