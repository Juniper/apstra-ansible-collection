#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# Apache License, Version 2.0 (see https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: virtual_infra_manager

short_description: Manage Virtual Infrastructure Managers in Apstra

version_added: "0.2.0"

author:
  - "Vijay Gavini (@vgavini)"

description:
  - Provides create, read, update and delete operations for Virtual
    Infrastructure Managers (VIMs) in Apstra.
  - Supports two scopes depending on whether C(blueprint) is provided
    in the C(id) parameter.
  - B(Global scope) (no C(blueprint) in C(id)) manages VIM definitions in
    the C(External Systems > Virtual Infra Managers) catalog at
    C(/api/virtual-infra-managers).  These are the connection definitions
    to vCenter, NSX, or Nutanix environments.
  - B(Blueprint scope) (C(blueprint) in C(id)) manages the VIM nodes
    assigned to a specific blueprint at
    C(/api/blueprints/{id}/virtual_infra).  This is where a global VIM
    is linked to a blueprint, specifying C(infra_type) and C(system_id).

options:
  api_url:
    description:
      - The URL used to access the Apstra api.
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
      - Dictionary containing identifiers.
      - B(Global scope) — omit C(blueprint).  Use C(virtual_infra_manager)
        (UUID or display_name) for get/update/delete.
      - B(Blueprint scope) — include C(blueprint) (UUID or label).  Use
        C(virtual_infra) (UUID) for get/update/delete an existing node.
      - B(vcenter scope) — when C(scope=vcenter), optionally include
        C(vcenter) (UUID) to target a specific vCenter instance under the
        VIM.  Omit C(vcenter) to operate on the vCenters collection
        (list or create).
      - B(anomaly_resolver scope) — blueprint only.  Triggers the
        virtual-infra VLAN-match anomaly resolver at
        C(/api/blueprints/{id}/virtual_infra/predefined_probes/virtual_infra_vlan_match/anomaly_resolver).
        Requires C(id.blueprint).  Body is passed through as-is.
      - B(query_vm scope) — blueprint only.  Queries the VM inventory
        for a blueprint at
        C(/api/blueprints/{id}/virtual_infra/query/vm).
        Requires C(id.blueprint).  Body contains the query parameters.
      - B(vnet scope) — blueprint only.  Retrieves virtual-network
        details from the virtual-infra layer at
        C(/api/blueprints/{id}/virtual_infra/vnet/{vnet_id}).
        Requires C(id.blueprint) and C(id.vnet) (UUID).
    type: dict
    required: false
  body:
    description:
      - Dictionary containing the configuration to create or update.
      - B(Global scope) key fields — C(display_name) (str) human-readable
        name for the VIM; C(virtual_infra_type) (str) platform type C(vcenter)/C(nsx)/
        C(nutanix); C(management_ip) (str) management IP or hostname;
        C(username) (str) and C(password) (str) login credentials;
        C(port) (int) optional management port.
      - B(Blueprint scope) key fields — C(infra_type) (str) one of
        C(vcenter), C(nsxt), C(nutanix), C(nsx); C(agent_id) (str)
        the VIM UUID (C(id.virtual_infra_manager) from the global VIM create);
        C(system_id) (str) the Apstra system identifier found in the VIM's
        top-level C(system_id) field after the VIM connects to vCenter.
        Both C(agent_id) and C(system_id) are required when creating a
        blueprint virtual_infra entry.
      - B(Shorthand) — instead of specifying C(agent_id) and C(system_id)
        manually, provide C(vim_ip) (the VIM's management IP address) and
        the module will look up the matching VIM automatically, resolving
        both C(agent_id) and C(system_id) from the global VIM list.
        Requires the VIM to be already connected to vCenter (so that
        C(system_id) is populated).
      - B(VLAN Remediation Policy) — when creating or updating a blueprint
        virtual_infra node, include C(vlan_remediation_policy) (str) in
        the body to set the VLAN remediation behaviour.  Accepted values
        depend on the Apstra version; common values are C(drop) (default)
        and C(remediate).  This field is passed through to the API as-is.
    type: dict
    required: false
  scope:
    description:
      - Selects the sub-resource to operate on.
      - C(manager) (default) — the VIM itself at
        C(/api/virtual-infra-managers/{id}).  Global scope only.
      - C(vcenter) — the vCenter instances at
        C(/api/virtual-infra-managers/{id}/vcenters) and
        C(/api/virtual-infra-managers/{id}/vcenters/{vcenter_id}).
        Requires C(id.virtual_infra_manager) to be set.  Supports full
        CRUD — list, create, get, PATCH, PUT, and delete — via direct
        API calls.  Global scope only.
        B(Note:) The C(create) operation (C(state=present) with a body
        and no C(id.vcenter)) is only supported for VIMs of type
        C(virtual_infra_type=nsx).  For C(vcenter)-type VIMs the
        C(/vcenters) endpoint is read-only and Apstra returns HTTP 422
        ("Vcenters can be added to virtual infra manager of the type
        NSX only").  List (C(state=present) without a body) works for
        all VIM types.
      - C(anomaly_resolver) — POSTs to
        C(/api/blueprints/{id}/virtual_infra/predefined_probes/virtual_infra_vlan_match/anomaly_resolver)
        to trigger auto-resolution of virtual-infra VLAN-match anomalies.
        Blueprint scope only (requires C(id.blueprint)).
      - C(query_vm) — POSTs to
        C(/api/blueprints/{id}/virtual_infra/query/vm) to query the VM
        inventory visible through the blueprint's virtual-infra layer.
        Returns C(result.vms) list.  Blueprint scope only.
      - C(vnet) — GETs
        C(/api/blueprints/{id}/virtual_infra/vnet/{vnet_id}) to retrieve
        virtual-network details from the virtual-infra layer.  Requires
        C(id.vnet) (UUID).  Blueprint scope only.
    type: str
    required: false
    choices: ["manager", "vcenter", "anomaly_resolver", "query_vm", "vnet"]
    default: "manager"
  state:
    description:
      - Desired state.
      - C(present) — create, or partially update (PATCH).
      - C(replaced) — fully replace an existing object (PUT).  For
        C(scope=manager) requires C(id.virtual_infra_manager).  For
        C(scope=vcenter) requires C(id.vcenter).
      - C(absent) — delete.
    type: str
    required: false
    choices: ["present", "replaced", "absent"]
    default: "present"
"""

EXAMPLES = """
# ── Global scope: create a vCenter VIM ───────────────────────────

- name: Create global vCenter VIM
  juniper.apstra.virtual_infra_manager:
    body:
      display_name: "prod-vcenter"
      virtual_infra_type: "vcenter"
      management_ip: "vcenter.example.com"
      username: "administrator@vsphere.local"
      password: "S3cret!"
    state: present
  register: vim_result

- name: Show created VIM ID
  ansible.builtin.debug:
    var: vim_result.id.virtual_infra_manager

# ── Global scope: update by display_name ─────────────────────────

- name: Update VIM management_ip by display_name (auto-resolved to ID)
  juniper.apstra.virtual_infra_manager:
    id:
      virtual_infra_manager: "prod-vcenter"   # display_name works
    body:
      management_ip: "vcenter2.example.com"
    state: present

# ── Global scope: update by UUID ─────────────────────────────────

- name: Update VIM by UUID
  juniper.apstra.virtual_infra_manager:
    id:
      virtual_infra_manager: "{{ vim_result.id.virtual_infra_manager }}"
    body:
      management_ip: "vcenter2.example.com"
    state: present

# ── Global scope: delete ─────────────────────────────────────────

- name: Delete global VIM by UUID
  juniper.apstra.virtual_infra_manager:
    id:
      virtual_infra_manager: "{{ vim_result.id.virtual_infra_manager }}"
    state: absent

- name: Delete global VIM by display_name
  juniper.apstra.virtual_infra_manager:
    id:
      virtual_infra_manager: "prod-vcenter"
    state: absent

# ── Global scope: full replace via PUT (state=replaced) ─────────

- name: Fully replace a VIM definition (PUT)
  juniper.apstra.virtual_infra_manager:
    id:
      virtual_infra_manager: "{{ vim_result.id.virtual_infra_manager }}"
    body:
      display_name: "prod-vcenter"
      virtual_infra_type: "vcenter"
      management_ip: "vcenter3.example.com"
      username: "administrator@vsphere.local"
      password: "NewPass123!"
    state: replaced

# ── Global scope: list vCenters for a VIM (scope=vcenter) ────────

- name: List all vCenters under a VIM
  juniper.apstra.virtual_infra_manager:
    id:
      virtual_infra_manager: "{{ vim_result.id.virtual_infra_manager }}"
    scope: vcenter
    state: present
  register: vcenter_list

- name: Show vCenters
  ansible.builtin.debug:
    var: vcenter_list.vcenters

# ── Global scope: create a vCenter under a VIM ───────────────────

- name: Add a vCenter instance to a VIM (NSX-type VIM only)
  juniper.apstra.virtual_infra_manager:
    id:
      virtual_infra_manager: "{{ vim_result.id.virtual_infra_manager }}"
    scope: vcenter
    body:
      management_ip: "vc1.example.com"
      username: "admin@vsphere.local"
      password: "VcPass!"
    state: present
  register: vcenter_created

# ── Global scope: get a specific vCenter by ID ────────────────────

- name: Get individual vCenter details
  juniper.apstra.virtual_infra_manager:
    id:
      virtual_infra_manager: "{{ vim_result.id.virtual_infra_manager }}"
      vcenter: "{{ vcenter_created.id.vcenter }}"
    scope: vcenter
    state: present
  register: vc_detail

# ── Global scope: patch a specific vCenter ────────────────────────

- name: Update vCenter credentials (PATCH)
  juniper.apstra.virtual_infra_manager:
    id:
      virtual_infra_manager: "{{ vim_result.id.virtual_infra_manager }}"
      vcenter: "{{ vcenter_created.id.vcenter }}"
    scope: vcenter
    body:
      password: "NewVcPass!"
    state: present

# ── Global scope: replace a specific vCenter (PUT) ────────────────

- name: Fully replace a vCenter definition (PUT)
  juniper.apstra.virtual_infra_manager:
    id:
      virtual_infra_manager: "{{ vim_result.id.virtual_infra_manager }}"
      vcenter: "{{ vcenter_created.id.vcenter }}"
    scope: vcenter
    body:
      management_ip: "vc2.example.com"
      username: "admin@vsphere.local"
      password: "VcPass!"
    state: replaced

# ── Global scope: delete a specific vCenter ───────────────────────

- name: Remove a vCenter from the VIM
  juniper.apstra.virtual_infra_manager:
    id:
      virtual_infra_manager: "{{ vim_result.id.virtual_infra_manager }}"
      vcenter: "{{ vcenter_created.id.vcenter }}"
    scope: vcenter
    state: absent

# ── Blueprint scope: list all VIM nodes ─────────────────────────

- name: List all virtual_infra nodes in a blueprint
  juniper.apstra.virtual_infra_manager:
    id:
      blueprint: "prod-dc1"
    state: present
    auth_token: "{{ auth_token }}"
  register: bp_vim_list

- name: Show all blueprint VIM nodes
  ansible.builtin.debug:
    var: bp_vim_list.virtual_infra

# ── Blueprint scope: assign VIM node to a blueprint ──────────────

# Option A — explicit agent_id + system_id
- name: Add virtual infra node to blueprint (explicit IDs)
  # agent_id = VIM UUID (id.virtual_infra_manager from the global VIM create)
  # system_id = VIM's own system_id field (returned after VIM connects to vCenter)
  # Both are REQUIRED by the Apstra API when creating a blueprint virtual_infra entry.
  juniper.apstra.virtual_infra_manager:
    id:
      blueprint: "prod-dc1"   # name or UUID
    body:
      infra_type: "vcenter"
      agent_id: "{{ vim_result.id.virtual_infra_manager }}"
      system_id: "{{ vim_result.virtual_infra_manager.system_id }}"
    state: present
  register: bp_vim

# Option B — shorthand via vim_ip (auto-resolves agent_id + system_id)
- name: Add virtual infra node to blueprint (by VIM IP — simpler)
  juniper.apstra.virtual_infra_manager:
    id:
      blueprint: "prod-dc1"
    body:
      infra_type: "vcenter"
      vim_ip: "10.0.0.100"   # management IP of the VIM — agent_id/system_id resolved automatically
    state: present
  register: bp_vim

# ── Blueprint scope: assign VIM with VLAN Remediation Policy ──────

- name: Add VIM to blueprint with VLAN remediation policy
  juniper.apstra.virtual_infra_manager:
    id:
      blueprint: "prod-dc1"
    body:
      infra_type: "vcenter"
      vim_ip: "10.0.0.100"
      vlan_remediation_policy: "remediate"   # or "drop" (default)
    state: present
  register: bp_vim

# ── Blueprint scope: update VIM node ─────────────────────────────

- name: Update blueprint VIM node
  juniper.apstra.virtual_infra_manager:
    id:
      blueprint: "prod-dc1"
      virtual_infra: "{{ bp_vim.id.virtual_infra }}"
    body:
      infra_type: "nsx"
    state: present

# ── Blueprint scope: remove VIM node ─────────────────────────────

- name: Remove virtual infra node from blueprint
  juniper.apstra.virtual_infra_manager:
    id:
      blueprint: "prod-dc1"
      virtual_infra: "{{ bp_vim.id.virtual_infra }}"
    state: absent
# ── Blueprint scope: trigger VLAN match anomaly resolver ────────
# POSTs to /virtual_infra/predefined_probes/virtual_infra_vlan_match/
# anomaly_resolver and asks Apstra to auto-resolve VLAN mismatches.

- name: Resolve virtual-infra VLAN match anomalies
  juniper.apstra.virtual_infra_manager:
    id:
      blueprint: "prod-dc1"
    scope: anomaly_resolver
    body:
      anomaly_ids: []   # empty list = resolve all
    state: present
  register: anomaly_result

- name: Show resolver response
  ansible.builtin.debug:
    var: anomaly_result.response

# ── Blueprint scope: query VM inventory ───────────────────────
# POSTs a query to /virtual_infra/query/vm and returns matching VMs.

- name: Query VMs in the virtual infra layer of a blueprint
  juniper.apstra.virtual_infra_manager:
    id:
      blueprint: "prod-dc1"
    scope: query_vm
    body:
      filter: {}
    state: present
  register: vm_query

- name: Show VMs
  ansible.builtin.debug:
    var: vm_query.vms

# ── Blueprint scope: get virtual-network from virtual infra layer ──
# GETs /virtual_infra/vnet/{vnet_id} — needs id.vnet (UUID).

- name: Get vnet details from virtual infra layer
  juniper.apstra.virtual_infra_manager:
    id:
      blueprint: "prod-dc1"
      vnet: "{{ vnet_uuid }}"
    scope: vnet
    state: present
  register: vnet_info

- name: Show vnet
  ansible.builtin.debug:
    var: vnet_info.vnet
"""

RETURN = """
changed:
  description: Indicates whether the module made any changes.
  type: bool
  returned: always
id:
  description: >
    The resolved ID dictionary for the created or targeted object.
    For global scope: contains C(virtual_infra_manager) key.
    For blueprint scope: contains C(blueprint) and C(virtual_infra) keys.
  type: dict
  returned: on create or when object identified by name
  sample:
    virtual_infra_manager: "a1b2c3d4-..."
response:
  description: The full API response object returned on create or patch.
  type: dict
  returned: on create or update
virtual_infra_manager:
  description: The VIM object details (global scope).
  type: dict
  returned: on present (global scope)
virtual_infra:
  description: >-
    Blueprint VIM node details (blueprint scope with C(id.virtual_infra)),
    or list of all virtual_infra nodes (blueprint scope without C(id.virtual_infra)
    and without body).
  type: raw
  returned: on present (blueprint scope)
vcenters:
  description: List of vCenter instances under the VIM (scope=vcenter, no id.vcenter).
  type: list
  returned: on present with scope=vcenter and no id.vcenter
vcenter:
  description: A single vCenter instance details (scope=vcenter with id.vcenter).
  type: dict
  returned: on present with scope=vcenter and id.vcenter and no body
vms:
  description: List of VMs returned by the scope=query_vm POST.
  type: list
  returned: on present with scope=query_vm (blueprint scope)
vnet:
  description: Virtual-network details from the virtual-infra layer (scope=vnet).
  type: dict
  returned: on present with scope=vnet (blueprint scope)
changes:
  description: Dictionary of fields that were updated.
  type: dict
  returned: on update
msg:
  description: Human-readable status message.
  type: str
  returned: always
resolved_from_vim_ip:
  description: >-
    When C(body.vim_ip) is used, contains the resolved C(vim_ip),
    C(agent_id), and C(system_id) that were substituted into the request.
  type: dict
  returned: when body.vim_ip is provided (blueprint scope)
"""

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.client import (
    apstra_client_module_args,
    ApstraClientFactory,
    singular_leaf_object_type,
)
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.name_resolution import (
    resolve_virtual_infra_manager_id,
    resolve_vim_agent_and_system_id,
    resolve_security_zone_id,
)
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.vim_vcenter import (
    list_vim_vcenters,
    create_vim_vcenter,
    get_vim_vcenter,
    update_vim_vcenter,
    patch_vim_vcenter,
    delete_vim_vcenter,
)
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.vim_blueprint_utils import (
    resolve_blueprint_virtual_infra_anomalies,
    query_blueprint_vms,
    get_blueprint_vnet,
)


# ──────────────────────────────────────────────────────────────────
#  vCenters sub-scope handler  (scope=vcenter)
# ──────────────────────────────────────────────────────────────────


def _handle_vcenters(module, client_factory, vim_id, body, state, result):
    """Handle vCenter sub-resource at /api/virtual-infra-managers/{id}/vcenters.

    Collection operations (list / create) are performed against
    /vcenters.  Individual operations (GET/PATCH/PUT/DELETE) are
    performed against /vcenters/{vcenter_id} via direct API calls
    using vim_vcenter module_utils (SDK gap fill).

    **NSX vs vcenter VIM architecture:**

    ``vcenter`` VIM type: The VIM IS the direct connection to vCenter.
    ``POST /vcenters`` returns HTTP 422 for vcenter-type VIMs — this is
    intentional Apstra API behaviour, not a bug.  Use the global VIM
    create/update scope (scope=manager) to manage vcenter-type VIMs.

    ``nsx`` VIM type: NSX is the parent; /vcenters sub-resources represent
    individual vCenters managed by that NSX instance.  CREATE works only
    for nsx-type VIMs.

    Routing:
      id.vcenter absent + no body  → list_vim_vcenters
      id.vcenter absent + body     → create_vim_vcenter  (NSX VIMs only)
      id.vcenter present + no body + state=present  → get_vim_vcenter
      id.vcenter present + body    + state=present  → patch_vim_vcenter
      id.vcenter present + body    + state=replaced → update_vim_vcenter
      id.vcenter present           + state=absent   → delete_vim_vcenter
    """
    vcenter_id = (module.params.get("id") or {}).get("vcenter")

    if vcenter_id is None:
        # ── Collection operations ──────────────────────────────────
        if state == "present":
            if body:
                # POST — create a new vCenter under this VIM
                created = create_vim_vcenter(client_factory, vim_id, body)
                result["changed"] = True
                result["response"] = created
                result["msg"] = "vcenter created successfully"
            else:
                # GET — list all vCenters
                vcenters = list_vim_vcenters(client_factory, vim_id)
                result["changed"] = False
                result["vcenters"] = vcenters if vcenters is not None else []
                result["msg"] = f"gathered {len(result['vcenters'])} vcenter(s)"
        else:
            raise ValueError(
                "scope=vcenter state=absent/replaced requires id.vcenter to "
                "target a specific vCenter UUID."
            )
    else:
        # ── Individual vcenter operations ─────────────────────────
        if state == "present":
            if body:
                # PATCH — partial update
                updated = patch_vim_vcenter(client_factory, vim_id, vcenter_id, body)
                result["changed"] = True
                result["response"] = updated
                result["id"] = {"vcenter": vcenter_id}
                result["msg"] = "vcenter patched successfully"
            else:
                # GET — fetch single vcenter
                vcenter = get_vim_vcenter(client_factory, vim_id, vcenter_id)
                result["changed"] = False
                result["vcenter"] = vcenter
                result["id"] = {"vcenter": vcenter_id}
                result["msg"] = "vcenter retrieved"
        elif state == "replaced":
            if not body:
                raise ValueError(
                    "scope=vcenter state=replaced requires a body (PUT payload)."
                )
            updated = update_vim_vcenter(client_factory, vim_id, vcenter_id, body)
            result["changed"] = True
            result["response"] = updated
            result["id"] = {"vcenter": vcenter_id}
            result["msg"] = "vcenter replaced (PUT) successfully"
        elif state == "absent":
            delete_vim_vcenter(client_factory, vim_id, vcenter_id)
            result["changed"] = True
            result["id"] = {"vcenter": vcenter_id}
            result["msg"] = "vcenter deleted successfully"


# ──────────────────────────────────────────────────────────────────
#  Global scope handler
# ──────────────────────────────────────────────────────────────────


def _handle_global_vim(module, client_factory, id, body, state, result):
    """Handle global VIM CRUD at /api/virtual-infra-managers."""
    object_type = "virtual_infra_managers"
    leaf_object_type = "virtual_infra_manager"  # singular per framework

    object_id = id.get(leaf_object_type) if id else None

    # Resolve display_name → UUID if needed
    if object_id:
        object_id = resolve_virtual_infra_manager_id(client_factory, object_id)
        id[leaf_object_type] = object_id

    # Look up existing object
    current_object = None
    if object_id is not None:
        raw = client_factory.object_request(object_type, "get", id)
        # The Apstra VIM GET API returns {"items": [...]} even for a single
        # object.  Unwrap to get the actual VIM dict so compare_and_update
        # can see fields like management_ip at the top level.
        if isinstance(raw, dict) and "items" in raw:
            items = raw.get("items", [])
            current_object = items[0] if items else None
        else:
            current_object = raw
    elif body and body.get("display_name"):
        # Search by display_name in the list
        all_vims = client_factory.object_request(object_type, "get", {})
        # Handle both bare list and {"items": [...]} wrapper
        if isinstance(all_vims, dict) and "items" in all_vims:
            all_vims = all_vims.get("items", [])
        if isinstance(all_vims, list):
            for vim in all_vims:
                if vim.get("display_name") == body["display_name"]:
                    current_object = vim
                    if id is None:
                        id = {}
                    id[leaf_object_type] = vim["id"]
                    break

    if state == "present":
        if current_object:
            result["id"] = id
            if body:
                changes = {}
                if client_factory.compare_and_update(current_object, body, changes):
                    updated = client_factory.object_request(
                        object_type, "patch", id, changes
                    )
                    result["changed"] = True
                    if updated:
                        result["response"] = updated
                    result["changes"] = changes
                    result["msg"] = f"{leaf_object_type} updated successfully"
                else:
                    result["changed"] = False
                    result["msg"] = (
                        f"{leaf_object_type} already exists, no changes needed"
                    )
            else:
                result["changed"] = False
                result["msg"] = f"No changes specified for {leaf_object_type}"
        else:
            if body is None:
                raise ValueError(f"Must specify 'body' to create a {leaf_object_type}")
            created = client_factory.object_request(object_type, "create", {}, body)
            if isinstance(created, dict) and "id" in created:
                if id is None:
                    id = {}
                id[leaf_object_type] = created["id"]
            result["id"] = id
            result["changed"] = True
            result["response"] = created
            result["msg"] = f"{leaf_object_type} created successfully"

        # Return final object state
        if current_object is not None:
            result[leaf_object_type] = current_object
        elif id and id.get(leaf_object_type):
            result[leaf_object_type] = client_factory.object_request(
                object_type=object_type,
                op="get",
                id=id,
                retry=10,
                retry_delay=3,
            )

    elif state == "replaced":
        # PUT — full replace of the VIM definition
        if id is None or leaf_object_type not in id:
            raise ValueError(
                f"Must specify '{leaf_object_type}' in id to use state=replaced"
            )
        if body is None:
            raise ValueError("Must specify 'body' to use state=replaced")
        base = client_factory.get_base_client()
        updated = base.virtual_infra_managers[id[leaf_object_type]].update(body)
        result["id"] = id
        result["changed"] = True
        if updated:
            result["response"] = updated
        result["msg"] = f"{leaf_object_type} replaced (PUT) successfully"

    elif state == "absent":
        if id is None or leaf_object_type not in id:
            raise ValueError(
                f"Must specify '{leaf_object_type}' in id "
                "(UUID or display_name) to delete"
            )
        client_factory.object_request(object_type, "delete", id)
        result["changed"] = True
        result["msg"] = f"{leaf_object_type} deleted successfully"


# ──────────────────────────────────────────────────────────────────


def _handle_blueprint_vim(module, client_factory, id, body, state, result):
    """Handle blueprint-level VIM CRUD at /api/blueprints/{id}/virtual_infra."""
    object_type = "blueprints.virtual_infra"
    leaf_object_type = singular_leaf_object_type(object_type)  # "virtual_infra"

    # ── vim_ip shorthand: resolve management IP → agent_id + system_id ──
    if body and body.get("vim_ip"):
        vim_ip = body.pop("vim_ip")
        agent_id, system_id = resolve_vim_agent_and_system_id(client_factory, vim_ip)
        body.setdefault("agent_id", agent_id)
        body.setdefault("system_id", system_id)
        result["resolved_from_vim_ip"] = {
            "vim_ip": vim_ip,
            "agent_id": agent_id,
            "system_id": system_id,
        }

    # ── vnet_remediation_policy: resolve security_zone_id name → UUID ──
    vrp = body.get("vnet_remediation_policy") if body else None
    if vrp and vrp.get("security_zone_id"):
        blueprint_id_for_sz = id.get("blueprint")
        vrp["security_zone_id"] = resolve_security_zone_id(
            client_factory, blueprint_id_for_sz, vrp["security_zone_id"]
        )

    object_id = id.get(leaf_object_type)
    collection_id = {k: v for k, v in id.items() if k != leaf_object_type}

    # ── List all virtual_infra nodes (no object_id, no body) ──────────────
    if object_id is None and not body and state == "present":
        all_vims = client_factory.object_request(object_type, "get", collection_id)
        result["changed"] = False
        result["virtual_infra"] = all_vims if isinstance(all_vims, list) else []
        result["msg"] = f"gathered {len(result['virtual_infra'])} virtual_infra node(s)"
        return

    # Look up existing object
    current_object = None
    if object_id is not None:
        current_object = client_factory.object_request(object_type, "get", id)
    elif body and body.get("system_id"):
        # Search by system_id in the list
        all_vims = client_factory.object_request(object_type, "get", collection_id)
        if isinstance(all_vims, list):
            for vim in all_vims:
                if vim.get("system_id") == body["system_id"]:
                    current_object = vim
                    id[leaf_object_type] = vim["id"]
                    break

    if state == "present":
        if current_object:
            result["id"] = id
            if body:
                changes = {}
                if client_factory.compare_and_update(current_object, body, changes):
                    updated = client_factory.object_request(
                        object_type, "patch", id, changes
                    )
                    result["changed"] = True
                    if updated:
                        result["response"] = updated
                    result["changes"] = changes
                    result["msg"] = f"{leaf_object_type} updated successfully"
                else:
                    result["changed"] = False
                    result["msg"] = (
                        f"{leaf_object_type} already exists, no changes needed"
                    )
            else:
                result["changed"] = False
                result["msg"] = f"No changes specified for {leaf_object_type}"
        else:
            if body is None:
                raise ValueError(f"Must specify 'body' to create a {leaf_object_type}")
            created = client_factory.object_request(object_type, "create", id, body)
            if isinstance(created, dict) and "id" in created:
                id[leaf_object_type] = created["id"]
            result["id"] = id
            result["changed"] = True
            result["response"] = created
            result["msg"] = f"{leaf_object_type} created successfully"

        # Return final object state
        if current_object is not None:
            result[leaf_object_type] = current_object
        elif id.get(leaf_object_type):
            result[leaf_object_type] = client_factory.object_request(
                object_type=object_type,
                op="get",
                id=id,
                retry=10,
                retry_delay=3,
            )

    elif state == "absent":
        if leaf_object_type not in id:
            raise ValueError(f"Must specify '{leaf_object_type}' in id to delete")
        client_factory.object_request(object_type, "delete", id)
        result["changed"] = True
        result["msg"] = f"{leaf_object_type} deleted successfully"


# ──────────────────────────────────────────────────────────────────
#  Module entry point
# ──────────────────────────────────────────────────────────────────


def main():
    object_module_args = dict(
        id=dict(type="dict", required=False, default=None),
        body=dict(type="dict", required=False),
        scope=dict(
            type="str",
            required=False,
            choices=["manager", "vcenter", "anomaly_resolver", "query_vm", "vnet"],
            default="manager",
        ),
        state=dict(
            type="str",
            required=False,
            choices=["present", "replaced", "absent"],
            default="present",
        ),
    )
    client_module_args = apstra_client_module_args()
    module_args = client_module_args | object_module_args

    result = dict(changed=False)

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)

    try:
        client_factory = ApstraClientFactory.from_params(module)

        id = dict(module.params.get("id") or {})
        body = module.params.get("body")
        scope = module.params["scope"]
        state = module.params["state"]

        # Resolve blueprint name → ID if present
        if "blueprint" in id:
            id["blueprint"] = client_factory.resolve_blueprint_id(id["blueprint"])

        is_blueprint_scope = "blueprint" in id

        if is_blueprint_scope:
            if scope == "vcenter":
                raise ValueError(
                    "scope=vcenter is only valid for global scope "
                    "(omit 'blueprint' from id)"
                )
            elif scope == "anomaly_resolver":
                response = resolve_blueprint_virtual_infra_anomalies(
                    client_factory, id["blueprint"], body
                )
                result["changed"] = True
                result["response"] = response
                result["msg"] = "virtual-infra VLAN match anomaly resolver triggered"
            elif scope == "query_vm":
                vms = query_blueprint_vms(client_factory, id["blueprint"], body)
                result["changed"] = False
                result["vms"] = vms
                result["msg"] = f"query/vm returned {len(vms)} VM(s)"
            elif scope == "vnet":
                vnet_id = id.get("vnet")
                if not vnet_id:
                    raise ValueError("Must specify 'id.vnet' for scope=vnet")
                vnet = get_blueprint_vnet(client_factory, id["blueprint"], vnet_id)
                result["changed"] = False
                result["vnet"] = vnet
                result["msg"] = (
                    f"vnet {vnet_id} retrieved" if vnet else f"vnet {vnet_id} not found"
                )
            else:
                _handle_blueprint_vim(module, client_factory, id, body, state, result)
        elif scope == "vcenter":
            # Resolve VIM name → ID before vcenters call
            vim_ref = id.get("virtual_infra_manager")
            if not vim_ref:
                raise ValueError(
                    "Must specify 'id.virtual_infra_manager' for scope=vcenter"
                )
            vim_id = resolve_virtual_infra_manager_id(client_factory, vim_ref)
            _handle_vcenters(module, client_factory, vim_id, body, state, result)
        else:
            _handle_global_vim(module, client_factory, id, body, state, result)

    except Exception as e:
        tb = traceback.format_exc()
        module.debug(f"Exception occurred: {str(e)}\n\nStack trace:\n{tb}")
        result.pop("msg", None)
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
