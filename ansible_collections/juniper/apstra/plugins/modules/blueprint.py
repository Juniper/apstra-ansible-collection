#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# Apache License, Version 2.0 (see https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: blueprint
short_description: Manage Apstra blueprints
description:
  - Create, commit, lock, unlock, and delete Apstra blueprints.
  - Run graph queries (QE) to discover nodes and interfaces within
    a blueprint using C(state=queried).
  - Patch individual node properties such as system_id and deploy_mode
    using C(state=node_updated).
  - The QE query and node utilities are also available as importable
    helpers in C(module_utils/apstra/bp_query.py) and
    C(module_utils/apstra/bp_nodes.py) for use by other modules.
version_added: "0.1.0"
author:
  - "Edwin Jacques (@edwinpjacques)"
  - "Vamsi Gavini (@vgavini)"
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
    default: true
  username:
    description:
      - The username for authentication.
    type: str
    required: false
  password:
    description:
      - The password for authentication.
    type: str
    required: false
  auth_token:
    description:
      - The authentication token to use if already authenticated.
    type: str
    required: false
  id:
    description:
      - The ID of the blueprint.
      - "Example: C({blueprint: abc-123})"
    required: false
    type: dict
  body:
    description:
      - A dictionary representing the blueprint to create.
      - "Must include C(label) and C(design)."
      - "Supported designs: C(two_stage_l3clos) (spine-leaf), C(three_stage_l3clos) (5-stage),
        C(freeform), C(collapsed)."
      - "Optional keys: C(init_type) (e.g. C(template_reference)), C(template_id)."
      - "C(template_id) accepts either the template ID (e.g. C(L2_Virtual_EVPN)) or
        the template display name (e.g. C(L2 Virtual EVPN)). When a display name is
        provided, the module resolves it to the corresponding template ID automatically."
    required: false
    type: dict
  lock_state:
    description:
      - Status to transition lock to.
    required: false
    type: str
    choices: ["locked", "unlocked", "ignore"]
    default: "locked"
  lock_timeout:
    description:
      - The timeout in seconds for locking the blueprint.
    required: false
    type: int
    default: 60
  rack_type:
    description:
      - Rack type reference for C(state=rack_added).
      - Accepts either rack type ID (for example C(L2_Virtual)) or display name
        (for example C(L2 Virtual)).
      - Required when C(state=rack_added).
    type: str
    required: false
  rack_count:
    description:
      - Desired total number of racks of C(rack_type) to exist in the blueprint.
      - Declarative/idempotent behavior: the module only adds missing racks until
        the desired total is reached.
      - Mutually exclusive with C(racks_to_add).
      - Only used when C(state=rack_added).
    type: int
    required: false
    default: 1
  racks_to_add:
    description:
      - Number of racks to add in this run.
      - Imperative/non-idempotent behavior (WebUI-style): each run adds this many
        racks regardless of current count.
      - Mutually exclusive with C(rack_count).
      - Only used when C(state=rack_added).
    type: int
    required: false
  commit_timeout:
    description:
      - The timeout in seconds for committing the blueprint.
    required: false
    type: int
    default: 30
  commit_description:
    description:
      - Optional description for the commit, visible in the Apstra
        revision history (same as the C(Description) field in the Web UI).
      - Only used when C(state=committed).
    required: false
    type: str
  unlock:
    description:
      - When set to C(true), unlocks the blueprint after the operation completes.
    required: false
    type: bool
    default: false
  state:
    description:
      - The desired state of the blueprint.
      - C(present) creates or verifies the blueprint exists.
      - C(committed) deploys (commits) the blueprint.
      - C(absent) deletes the blueprint.
      - C(queried) runs a graph query against the blueprint
        (read-only, never modifies the blueprint).
      - C(node_updated) patches properties on one or more blueprint
        nodes. Use C(node_id) to target a single node by UUID, or
        C(assignment) to assign multiple nodes by label in one task.
      - C(rack_added) adds racks of a rack type using either C(rack_count)
        (desired total, idempotent) or C(racks_to_add) (delta, non-idempotent).
      - C(rack_deleted) deletes rack(s) by C(rack_id) / C(node_id).
      - C(interface_updated) sets the admin state (shut/no-shut) of a
        blueprint interface node. Use C(system_name), C(interface_name),
        and C(admin_state) to target and configure the interface.
      - C(interface_tagged) adds or removes tags on a blueprint interface
        node. Use C(system_name), C(interface_name), C(tags), and
        C(state=interface_tagged) with C(tag_state=present/absent).
      - C(lag_updated) sets C(lag_mode) (and optionally C(port_channel_id))
        on a port-channel interface of a managed switch.
    required: false
    type: str
    choices: ["present", "committed", "absent", "queried", "node_updated", "rack_added", "rack_deleted", "interface_updated", "interface_tagged", "lag_updated"]
    default: "present"
  system_name:
    description:
      - The label of the system (switch/server) node in the blueprint.
      - Required when C(state=interface_updated), C(state=interface_tagged),
        or C(state=lag_updated).
    type: str
    required: false
  interface_name:
    description:
      - The interface name on the system (e.g. C(ge-0/0/0), C(ae4)).
      - Required when C(state=interface_updated), C(state=interface_tagged),
        or C(state=lag_updated).
    type: str
    required: false
  admin_state:
    description:
      - Desired administrative state of the interface.
      - C(up) enables the interface (no-shut).
      - C(down) disables the interface (shut).
      - Only used when C(state=interface_updated) in single-interface mode.
    type: str
    required: false
    choices: ["up", "down"]
  interfaces:
    description:
      - List of interfaces to update in a single task (batch mode).
      - Only used when C(state=interface_updated).
      - Each entry must have C(system_name), C(interface_name), and C(admin_state).
      - Mutually exclusive with single-interface mode (C(system_name) / C(interface_name) / C(admin_state)).
    type: list
    elements: dict
    required: false
  tags:
    description:
      - List of tag labels to add or remove on the interface node.
      - Only used when C(state=interface_tagged).
      - Combined with C(tag_state) to determine whether tags are added
        or removed.
    type: list
    elements: str
    required: false
  tag_state:
    description:
      - Whether to add or remove the specified C(tags) on the interface.
      - C(present) ensures the tags exist on the interface node.
      - C(absent) removes the tags from the interface node.
      - Only used when C(state=interface_tagged).
    type: str
    required: false
    choices: ["present", "absent"]
    default: "present"
  lag_mode:
    description:
      - LAG mode to set on a port-channel interface of a managed switch.
      - Only used when C(state=lag_updated).
    type: str
    required: false
    choices: ["lacp_active", "lacp_passive", "static_lag", "none"]
  port_channel_id:
    description:
      - Optional port-channel interface number (e.g. C(4) for C(ae4)).
      - When set, updates the C(port_channel_id) field alongside C(lag_mode).
      - Only used when C(state=lag_updated).
    type: int
    required: false
  query:
    description:
      - A raw QE query string.
      - Only used when C(state=queried).
      - Uses Apstra graph query syntax, for example
        C(node('system', role='spine', name='system')).
      - Mutually exclusive with C(query_type).
    type: str
    required: false
  query_type:
    description:
      - A built-in convenience query.
      - Only used when C(state=queried).
      - C(nodes_by_role) returns system nodes filtered by C(roles).
      - C(nodes_by_type) returns system nodes filtered by
        C(system_type).
      - C(interfaces_by_neighbor) returns switch interfaces linked
        to systems whose labels are in C(neighbor_labels).
      - C(host_bond_interfaces) returns port-channel interfaces on
        host generic systems, optionally filtered by C(host_labels).
      - C(host_evpn_interfaces) returns ESI-LAG group interfaces
        (EVPN port-channels) for host systems, optionally filtered
        by C(host_labels). These are the correct application points
        for VN endpoint-policy assignment in dual-homed topologies.
      - Mutually exclusive with C(query).
    type: str
    required: false
    choices:
      - nodes_by_role
      - nodes_by_type
      - interfaces_by_neighbor
      - host_bond_interfaces
      - host_evpn_interfaces
  roles:
    description:
      - List of system roles to filter (C(query_type=nodes_by_role)).
    type: list
    elements: str
    required: false
  system_type:
    description:
      - System type filter (C(query_type=nodes_by_type)).
    type: str
    required: false
  neighbor_labels:
    description:
      - Neighbor labels to match
        (C(query_type=interfaces_by_neighbor)).
    type: list
    elements: str
    required: false
  host_labels:
    description:
      - Host labels filter (C(query_type=host_bond_interfaces)).
    type: list
    elements: str
    required: false
  neighbor_system_type:
    description:
      - Neighbor system_type
        (C(query_type=interfaces_by_neighbor)).
    type: str
    required: false
    default: server
  local_role:
    description:
      - Local switch role
        (C(query_type=interfaces_by_neighbor)).
    type: str
    required: false
    default: leaf
  if_type:
    description:
      - Interface type filter
        (C(query_type=interfaces_by_neighbor)).
    type: str
    required: false
    default: ethernet
  assignment:
    description:
      - Dict mapping blueprint node labels to physical device serial
        numbers (C(system_id)) for bulk assignment.
      - "Example: C({spine1: SERIAL001, spine2: SERIAL002, leaf1: SERIAL003})."
      - When C(deploy_mode) is also specified, it is applied to every
        node in the dict.
      - Mutually exclusive with C(node_id).
      - Only used when C(state=node_updated).
    type: dict
    required: false
  node_id:
    description:
      - The blueprint node(s) to patch in C(state=node_updated).
      - Accepts a single value or a list of values.
      - Each value may be a node UUID, a graph-node short ID, or a
        device label (e.g. C(leaf1)).  Labels are resolved to their
        graph-node UUID automatically.
      - Mutually exclusive with C(assignment).
      - Only used when C(state=node_updated).
      - Alias C(rack_id) can be used for rack operations.
    type: raw
    required: false
    aliases: [rack_id]
  system_id:
    description:
      - Physical device serial to assign to the node.
      - Only used when C(state=node_updated).
    type: str
    required: false
  deploy_mode:
    description:
      - Deploy mode to set on the node.
      - Only used when C(state=node_updated).
    type: str
    required: false
    choices: ["deploy", "undeploy", "drain", "ready"]
  hostname:
    description:
      - Hostname to set on the node.
      - Only used when C(state=node_updated).
    type: str
    required: false
  current_label:
    description:
      - Current label (display name) of the node to update.
      - Used as an alternative to C(node_id) — the module resolves the label
        to a node UUID automatically.
      - Mutually exclusive with C(node_id).
      - Only used when C(state=node_updated).
    type: str
    required: false
  node_type:
    description:
      - Node type filter used when resolving C(current_label) to a node UUID.
      - When set (e.g. C(rack), C(system)), only nodes of that type are
        considered during label lookup, avoiding false matches when nodes
        of different types share the same label.
      - Only used when C(state=node_updated) together with C(current_label).
    type: str
    required: false
  node_label:
    description:
      - Label to set on the node.
      - Only used when C(state=node_updated).
      - Alias C(rack_label) can be used for rack operations.
    type: str
    required: false
    aliases: [rack_label]
  node_properties:
    description:
      - Arbitrary dict of node properties to patch.
      - Only used when C(state=node_updated).
      - Use this for fields not covered by the dedicated params
        (e.g. C(if_name), C(external)).
      - Fields requiring C(allow_unsafe=true) are handled automatically.
    type: dict
    required: false
"""

EXAMPLES = """
# Create a new blueprint (using template ID)
- name: Create blueprint
  juniper.apstra.blueprint:
    body:
      label: my-blueprint
      design: two_stage_l3clos
      init_type: template_reference
      template_id: L2_Virtual_EVPN
    state: present
  register: bp

# Create a new blueprint (using template display name)
- name: Create blueprint by template name
  juniper.apstra.blueprint:
    body:
      label: my-blueprint
      design: two_stage_l3clos
      init_type: template_reference
      template_id: "L2 Virtual EVPN"
    state: present
  register: bp

# Commit (deploy) a blueprint
- name: Deploy blueprint
  juniper.apstra.blueprint:
    id:
      blueprint: "{{ bp.id.blueprint }}"
    lock_state: ignore
    state: committed

# Commit with a description (visible in revision history)
- name: Deploy blueprint with description
  juniper.apstra.blueprint:
    id:
      blueprint: "{{ bp.id.blueprint }}"
    lock_state: ignore
    commit_description: "Push spine/leaf IP addressing changes"
    state: committed

# Delete a blueprint
- name: Delete blueprint
  juniper.apstra.blueprint:
    id:
      blueprint: "{{ blueprint_id }}"
    state: absent

# Run a raw QE query
- name: Query all spine nodes
  juniper.apstra.blueprint:
    id:
      blueprint: "{{ blueprint_id }}"
    query: "node('system', role='spine', name='system')"
    state: queried
  register: spines

# Discover nodes by role (convenience query)
- name: Get all spine and leaf nodes
  juniper.apstra.blueprint:
    id:
      blueprint: "{{ blueprint_id }}"
    query_type: nodes_by_role
    roles:
      - spine
      - leaf
    state: queried
  register: switch_nodes

# Find SRX-facing interfaces for CT assignment
- name: Find interfaces connected to SRX systems
  juniper.apstra.blueprint:
    id:
      blueprint: "{{ blueprint_id }}"
    query_type: interfaces_by_neighbor
    neighbor_labels:
      - srx1
      - srx2
    state: queried
  register: srx_intfs

# Find host bond interfaces
- name: Find all host port-channel interfaces
  juniper.apstra.blueprint:
    id:
      blueprint: "{{ blueprint_id }}"
    query_type: host_bond_interfaces
    host_labels:
      - host1
      - host2
    state: queried
  register: host_intfs

# Bulk-assign serials to multiple nodes by label in one task
- name: Assign devices to all fabric nodes
  juniper.apstra.blueprint:
    id:
      blueprint: "{{ blueprint_id }}"
    assignment:
      spine1: "SERIAL001"
      spine2: "SERIAL002"
      leaf1: "SERIAL003"
      leaf2: "SERIAL004"
    deploy_mode: deploy
    state: node_updated
  register: assigned

# Assign system_id to a single blueprint node (by UUID)
- name: Bind device serial to spine1
  juniper.apstra.blueprint:
    id:
      blueprint: "{{ blueprint_id }}"
    node_id: "{{ spine1_node_id }}"
    system_id: "SERIAL12345"
    state: node_updated

# Set deploy mode on a node by label (no UUID lookup needed)
- name: Set leaf1 to drain mode by label
  juniper.apstra.blueprint:
    id:
      blueprint: "{{ blueprint_id }}"
    node_id: "leaf1"
    deploy_mode: drain
    state: node_updated

# Set deploy mode on multiple nodes by label (list form)
- name: Set leaf1 and leaf2 to drain mode
  juniper.apstra.blueprint:
    id:
      blueprint: "{{ blueprint_id }}"
    node_id:
      - "leaf1"
      - "leaf2"
    deploy_mode: drain
    state: node_updated

# Set deploy mode on a node (legacy UUID form still works)
- name: Set leaf1 to deploy mode
  juniper.apstra.blueprint:
    id:
      blueprint: "{{ blueprint_id }}"
    node_id: "{{ leaf1_node_id }}"
    deploy_mode: deploy
    state: node_updated

# Set arbitrary node properties (e.g. interface name)
- name: Set interface name on SRX
  juniper.apstra.blueprint:
    id:
      blueprint: "{{ blueprint_id }}"
    node_id: "{{ srx_intf_id }}"
    node_properties:
      if_name: ge-0/0/0
    state: node_updated

# Update device name and hostname by current label (no node_id needed)
- name: Rename leaf1 and update its hostname
  juniper.apstra.blueprint:
    id:
      blueprint: "{{ blueprint_id }}"
    current_label: "leaf1"
    node_label: "leaf1-new"
    hostname: "leaf1-new.example.com"
    state: node_updated

# Rename a rack by its current label (use node_type to target rack nodes)
- name: Rename rack from 'da_rack_001' to 'border-rack-1'
  juniper.apstra.blueprint:
    id:
      blueprint: "{{ blueprint_id }}"
    current_label: "da_rack_001"
    rack_label: "border-rack-1"
    node_type: rack
    state: node_updated


# Add 2 racks (WebUI-style, non-idempotent)
- name: Add 2 racks of type 'AOS-2x10-1' (non-idempotent)
  juniper.apstra.blueprint:
    id:
      blueprint: "{{ blueprint_id }}"
    rack_type: "AOS-2x10-1"
    racks_to_add: 2
    state: rack_added
  register: racks_result

# Ensure at least 1 rack exists (idempotent)
- name: Ensure at least 1 rack of type 'AOS-2x10-1' exists (idempotent)
  juniper.apstra.blueprint:
    id:
      blueprint: "{{ blueprint_id }}"
    rack_type: "AOS-2x10-1"
    rack_count: 1
    state: rack_added

# Delete a rack by its blueprint rack ID
- name: Remove a rack from the blueprint
  juniper.apstra.blueprint:
    id:
      blueprint: "{{ blueprint_id }}"
    rack_id: "{{ rack_node_id }}"
    state: rack_deleted

# Delete a rack by its label (name resolution handled automatically)
- name: Remove rack by label
  juniper.apstra.blueprint:
    id:
      blueprint: "{{ blueprint_id }}"
    rack_id: "da_rack_001"
    state: rack_deleted

# Shut down an interface (admin down)
- name: Shut leaf1 ge-0/0/0 interface
  juniper.apstra.blueprint:
    id:
      blueprint: "{{ blueprint_id }}"
    system_name: "leaf1"
    interface_name: "ge-0/0/0"
    admin_state: "down"
    state: interface_updated
  register: intf_shut

# Re-enable a shut-down interface
- name: No-shut leaf1 ge-0/0/0
  juniper.apstra.blueprint:
    id:
      blueprint: "{{ blueprint_id }}"
    system_name: "leaf1"
    interface_name: "ge-0/0/0"
    admin_state: "up"
    state: interface_updated

# Batch shut multiple interfaces in one task
- name: Shut down multiple spine interfaces
  juniper.apstra.blueprint:
    id:
      blueprint: "{{ blueprint_id }}"
    interfaces:
      - system_name: "spine1"
        interface_name: "et-0/0/0"
        admin_state: "down"
      - system_name: "spine1"
        interface_name: "et-0/0/1"
        admin_state: "down"
      - system_name: "spine2"
        interface_name: "et-0/0/0"
        admin_state: "up"
    state: interface_updated

# Add tags to an ethernet interface
- name: Tag leaf1 ge-0/0/0 as 'uplink' and 'production'
  juniper.apstra.blueprint:
    id:
      blueprint: "{{ blueprint_id }}"
    system_name: "leaf1"
    interface_name: "ge-0/0/0"
    tags:
      - uplink
      - production
    tag_state: present
    state: interface_tagged

# Remove a tag from an interface
- name: Remove 'uplink' tag from leaf1 ge-0/0/0
  juniper.apstra.blueprint:
    id:
      blueprint: "{{ blueprint_id }}"
    system_name: "leaf1"
    interface_name: "ge-0/0/0"
    tags:
      - uplink
    tag_state: absent
    state: interface_tagged

# Change LAG mode on a port-channel interface
- name: Set leaf1 ae4 to lacp_passive
  juniper.apstra.blueprint:
    id:
      blueprint: "{{ blueprint_id }}"
    system_name: "leaf1"
    interface_name: "ae4"
    lag_mode: "lacp_passive"
    state: lag_updated
"""

RETURN = """
changed:
    description: Whether the blueprint was changed.
    returned: always
    type: bool
    sample: true
id:
    description: The ID of the created blueprint.
    returned: on create
    type: dict
    sample:
        blueprint: "blueprint-123"
msg:
    description: A message describing the result.
    returned: always
    type: str
    sample: "blueprint created successfully"
lock_state:
    description: State of the blueprint lock.
    returned: on present/committed/absent
    type: str
    sample: "locked"
response:
    description: The response from the Apstra API.
    returned: on create
    type: dict
results:
    description:
        - Raw QE query results (list of dicts).
        - Returned when C(state=queried) with C(query).
    returned: when using raw query
    type: list
    elements: dict
nodes:
    description:
        - "Mapping of node label to node properties."
        - Returned by C(nodes_by_role) and C(nodes_by_type).
    returned: when using nodes_by_role or nodes_by_type
    type: dict
    sample:
        spine1:
            id: "abc-123"
            role: "spine"
interfaces:
    description:
        - List of interface dicts.
        - Returned by C(interfaces_by_neighbor).
    returned: when using interfaces_by_neighbor
    type: list
    elements: dict
interface_ids:
    description:
        - Flat list of interface IDs for easy consumption.
        - Returned by C(interfaces_by_neighbor).
    returned: when using interfaces_by_neighbor
    type: list
    elements: str
host_interfaces:
    description:
        - "Mapping of host label to port-channel interface ID."
        - Returned by C(host_bond_interfaces).
    returned: when using host_bond_interfaces
    type: dict
nodes_updated:
    description:
        - "Mapping of node label to final node properties for every node that
          was patched during a bulk C(assignment) call."
        - Returned by C(state=node_updated) with C(assignment).
    returned: when using assignment
    type: dict
nodes_unchanged:
    description:
        - List of node labels that were already at the desired state
          (no patch needed) during a bulk C(assignment) call.
        - Returned by C(state=node_updated) with C(assignment).
    returned: when using assignment
    type: list
    elements: str
node:
    description:
        - Node properties after patch.
        - Returned by C(state=node_updated).
    returned: when using node_updated
    type: dict
racks:
    description:
        - List of rack dicts currently in the blueprint for the requested
          rack type after the operation.
        - Returned by C(state=rack_added).
    returned: when using rack_added
    type: list
    elements: dict
racks_added:
    description:
        - Number of racks added during this run.
        - Returned by C(state=rack_added) when C(changed=true).
    returned: when racks were added
    type: int
rack_type_id:
    description:
        - Resolved rack type ID used for the operation.
        - Returned by C(state=rack_added).
    returned: when using rack_added
    type: str
racks_deleted:
    description:
        - List of rack node IDs that were deleted.
        - Returned by C(state=rack_deleted) when C(changed=true).
    returned: when racks were deleted
    type: list
    elements: str
interface_node_id:
    description:
        - The blueprint node UUID of the interface that was targeted.
        - Returned by C(state=interface_updated), C(state=interface_tagged),
          and C(state=lag_updated).
    returned: when using interface management states
    type: str
admin_state:
    description:
        - The resolved admin state of the interface after the operation.
        - Returned by C(state=interface_updated).
    returned: when using interface_updated
    type: str
    sample: "down"
operation_state:
    description:
        - The raw Apstra C(operation_state) value on the interface node.
        - C("up") means enabled; C("admin_down") means shut.
        - Returned by C(state=interface_updated).
    returned: when using interface_updated
    type: str
    sample: "admin_down"
interface_tags:
    description:
        - Final list of tag labels on the interface node after the operation.
        - Returned by C(state=interface_tagged).
    returned: when using interface_tagged
    type: list
    elements: str
lag_mode:
    description:
        - The final C(lag_mode) on the interface node after the operation.
        - Returned by C(state=lag_updated).
    returned: when using lag_updated
    type: str
    sample: "lacp_passive"
"""

from time import sleep

from ansible.module_utils.basic import AnsibleModule
import traceback

from ansible_collections.juniper.apstra.plugins.module_utils.apstra.client import (
    apstra_client_module_args,
    ApstraClientFactory,
    DEFAULT_BLUEPRINT_LOCK_TIMEOUT,
    DEFAULT_BLUEPRINT_COMMIT_TIMEOUT,
)
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.bp_query import (
    run_qe_query,
    find_nodes_by_role,
    find_nodes_by_type,
    find_interfaces_by_neighbor,
    find_host_bond_interfaces,
    find_host_evpn_interfaces,
)
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.bp_nodes import (
    get_node,
    list_nodes,
    patch_node,
    node_needs_update,
    assign_nodes_by_label,
)


from ansible_collections.juniper.apstra.plugins.module_utils.apstra.name_resolution import (
    resolve_template_id as _resolve_template_id,
    resolve_rack_type_id,
    resolve_graph_node_id,
    resolve_rack_node_id,
    resolve_system_node_id,
)
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.bp_interface import (
    find_interface_node,
    set_operation_state,
    set_interface_tags,
    set_lag_mode,
)

# ──────────────────────────────────────────────────────────────────
#  Rack management helpers
# ──────────────────────────────────────────────────────────────────


def _get_racks_by_type(client_factory, blueprint_id, rack_type_id):
    """Return rack node dicts from the blueprint filtered by rack_type_id.

    Blueprint rack nodes store the full rack type definition as the JSON
    string ``rack_type_json``.  The ``id`` inside that JSON is a content
    hash, not the design-API rack type ID.  We look up the rack type's
    ``display_name`` via the design API and match against
    ``rack_type_json.display_name`` to filter correctly.
    """
    import json as _json

    items = run_qe_query(client_factory, blueprint_id, "node('rack', name='rack')")
    racks = [r.get("rack", {}) for r in items if r.get("rack")]
    if not rack_type_id:
        return racks

    # Resolve the design-API display_name for this rack_type_id.
    base = client_factory.get_base_client()
    resp = base.raw_request("/design/rack-types")
    design_display_name = None
    if resp.status_code == 200:
        for rt in (resp.json() or {}).get("items", []):
            if rt.get("id") == rack_type_id:
                design_display_name = rt.get("display_name")
                break

    if not design_display_name:
        # Cannot match by display_name — return unfiltered
        return racks

    filtered = []
    for rack in racks:
        rt_json_str = rack.get("rack_type_json")
        if rt_json_str:
            try:
                if _json.loads(rt_json_str).get("display_name") == design_display_name:
                    filtered.append(rack)
            except Exception:
                pass
    return filtered


# ──────────────────────────────────────────────────────────────────
#  Rack management handlers (state=rack_added / state=rack_deleted)
# ──────────────────────────────────────────────────────────────────


def _handle_rack_added(module, client_factory, blueprint_id):
    """Handle state=rack_added — add racks of a given type to the blueprint."""
    rack_type_ref = module.params.get("rack_type")
    rack_count = module.params.get("rack_count")
    racks_to_add = module.params.get("racks_to_add")

    if not rack_type_ref:
        module.fail_json(msg="rack_type is required when state=rack_added")

    if rack_count is not None and racks_to_add is not None:
        module.fail_json(
            msg="rack_count and racks_to_add are mutually exclusive. Use only one."
        )

    # Resolve rack type name/display_name → design ID
    try:
        rack_type_id = resolve_rack_type_id(client_factory, rack_type_ref)
    except (ValueError, Exception) as exc:
        module.fail_json(msg=str(exc))

    base = client_factory.get_base_client()

    # Non-idempotent: racks_to_add (WebUI style)
    if racks_to_add is not None:
        if racks_to_add < 1:
            module.fail_json(msg="racks_to_add must be >= 1 if specified.")
        # Fetch the full rack type definition required by the add-racks body
        rt_resp = base.raw_request(f"/design/rack-types/{rack_type_id}")
        if rt_resp.status_code != 200:
            raise Exception(
                f"Failed to fetch rack type definition for '{rack_type_id}': "
                f"HTTP {rt_resp.status_code} — {rt_resp.text}"
            )
        rack_type_def = rt_resp.json()
        resp = base.raw_request(
            f"/blueprints/{blueprint_id}/add-racks",
            method="POST",
            data={
                "rack_types": [rack_type_def],
                "rack_type_counts": {rack_type_id: racks_to_add},
            },
        )
        if resp.status_code not in (200, 201, 202):
            raise Exception(
                f"Failed to add racks to blueprint: HTTP {resp.status_code} — {resp.text}"
            )
        all_racks = _get_racks_by_type(client_factory, blueprint_id, rack_type_id)
        return dict(
            changed=True,
            racks=all_racks,
            racks_added=racks_to_add,
            rack_type_id=rack_type_id,
            msg=(
                f"Added {racks_to_add} rack(s) of type '{rack_type_ref}' to blueprint "
                f"(total: {len(all_racks)})"
            ),
        )

    # Idempotent: rack_count (Ansible style, default)
    if rack_count is None:
        rack_count = 1

    # Idempotency check: count existing racks of this type in the blueprint
    existing = _get_racks_by_type(client_factory, blueprint_id, rack_type_id)
    current_count = len(existing)

    if current_count >= rack_count:
        return dict(
            changed=False,
            racks=existing,
            rack_type_id=rack_type_id,
            msg=(
                f"Blueprint already has {current_count} rack(s) of type "
                f"'{rack_type_ref}' (desired: {rack_count}). No changes needed."
            ),
        )

    to_add = rack_count - current_count
    # Fetch the full rack type definition required by the add-racks body
    rt_resp = base.raw_request(f"/design/rack-types/{rack_type_id}")
    if rt_resp.status_code != 200:
        raise Exception(
            f"Failed to fetch rack type definition for '{rack_type_id}': "
            f"HTTP {rt_resp.status_code} — {rt_resp.text}"
        )
    rack_type_def = rt_resp.json()
    resp = base.raw_request(
        f"/blueprints/{blueprint_id}/add-racks",
        method="POST",
        data={
            "rack_types": [rack_type_def],
            "rack_type_counts": {rack_type_id: to_add},
        },
    )
    if resp.status_code not in (200, 201, 202):
        raise Exception(
            f"Failed to add racks to blueprint: HTTP {resp.status_code} — {resp.text}"
        )
    all_racks = _get_racks_by_type(client_factory, blueprint_id, rack_type_id)
    return dict(
        changed=True,
        racks=all_racks,
        racks_added=to_add,
        rack_type_id=rack_type_id,
        msg=(
            f"Added {to_add} rack(s) of type '{rack_type_ref}' to blueprint "
            f"(total: {len(all_racks)})"
        ),
    )


def _handle_rack_deleted(module, client_factory, blueprint_id):
    """Handle state=rack_deleted — remove rack(s) from the blueprint."""
    # node_id has alias rack_id (defined in argspec)
    rack_id = module.params.get("node_id")

    if not rack_id:
        module.fail_json(msg="rack_id is required when state=rack_deleted")

    rack_ids = [rack_id] if isinstance(rack_id, str) else list(rack_id)

    # Resolve each reference (label or UUID) to a blueprint rack node ID.
    # Racks that cannot be found are silently skipped (idempotency).
    resolved_ids = []
    for rid in rack_ids:
        try:
            resolved = resolve_rack_node_id(client_factory, blueprint_id, rid)
            resolved_ids.append((rid, resolved))
        except ValueError:
            pass  # already deleted or never existed

    if not resolved_ids:
        return dict(
            changed=False,
            racks_deleted=[],
            msg="Rack(s) not found in blueprint (already deleted or never existed)",
        )

    base = client_factory.get_base_client()
    resp = base.raw_request(
        f"/blueprints/{blueprint_id}/delete-racks",
        method="POST",
        data={"racks_to_delete": [resolved_id for _, resolved_id in resolved_ids]},
    )
    if resp.status_code not in (200, 201, 202, 204):
        raise Exception(
            f"Failed to delete racks: " f"HTTP {resp.status_code} — {resp.text}"
        )
    deleted = [resolved_id for _, resolved_id in resolved_ids]

    n = len(deleted)
    return dict(
        changed=True,
        racks_deleted=deleted,
        msg=f"Deleted {n} rack(s) from blueprint",
    )


# ──────────────────────────────────────────────────────────────────
#  Interface management handlers (Features 2, 3, 4)
# ──────────────────────────────────────────────────────────────────


def _resolve_interface_node_id(module, client_factory, blueprint_id):
    """Resolve system_name + interface_name to an interface node UUID.

    Fails the module with a descriptive error if either the system or the
    interface cannot be found.

    Returns:
        str: The interface node UUID.
    """
    system_name = module.params.get("system_name")
    interface_name = module.params.get("interface_name")

    if not system_name:
        module.fail_json(msg="system_name is required for interface management states")
    if not interface_name:
        module.fail_json(
            msg="interface_name is required for interface management states"
        )

    iface = find_interface_node(
        client_factory, blueprint_id, system_name, interface_name
    )
    if iface is None:
        module.fail_json(
            msg=(
                f"Interface '{interface_name}' not found on system '{system_name}' "
                f"in blueprint '{blueprint_id}'"
            )
        )
    return iface["id"]


def _handle_interface_updated(module, client_factory, blueprint_id):
    """Handle state=interface_updated — set admin state (shut/no-shut).

    Supports both single-interface mode (system_name + interface_name + admin_state)
    and batch mode (interfaces list of {system_name, interface_name, admin_state}).
    """
    interfaces = module.params.get("interfaces")

    if interfaces:
        # Batch mode: iterate over the list
        results = []
        any_changed = False
        for entry in interfaces:
            sys_name = entry.get("system_name")
            if_name = entry.get("interface_name")
            adm_state = entry.get("admin_state")
            if not sys_name or not if_name or not adm_state:
                module.fail_json(
                    msg=(
                        "Each entry in 'interfaces' must have "
                        "system_name, interface_name, and admin_state"
                    )
                )
            iface = find_interface_node(client_factory, blueprint_id, sys_name, if_name)
            if iface is None:
                module.fail_json(
                    msg=(
                        f"Interface '{if_name}' not found on system '{sys_name}' "
                        f"in blueprint '{blueprint_id}'"
                    )
                )
            r = set_operation_state(
                client_factory, blueprint_id, iface["id"], adm_state
            )
            if r.get("changed"):
                any_changed = True
            results.append(
                {
                    "system_name": sys_name,
                    "interface_name": if_name,
                    "admin_state": adm_state,
                    "changed": r.get("changed", False),
                    "interface_node_id": r.get("node_id", iface["id"]),
                }
            )
        return dict(
            changed=any_changed,
            interfaces=results,
            msg=f"Updated {len(interfaces)} interface(s)",
        )

    # Single-interface mode (backward compatible)
    admin_state = module.params.get("admin_state")
    if not admin_state:
        module.fail_json(msg="admin_state is required when state=interface_updated")
    iface_id = _resolve_interface_node_id(module, client_factory, blueprint_id)
    result = set_operation_state(client_factory, blueprint_id, iface_id, admin_state)
    result["interface_node_id"] = result.pop("node_id", iface_id)
    return result


def _handle_interface_tagged(module, client_factory, blueprint_id):
    """Handle state=interface_tagged — add or remove tags on an interface.

    Supports both single-interface mode (system_name + interface_name + tags)
    and batch mode (interfaces list of {system_name, interface_name} with
    shared tags / tag_state params).
    """
    tags = module.params.get("tags")
    if not tags:
        module.fail_json(msg="tags is required when state=interface_tagged")

    tag_state = module.params.get("tag_state") or "present"
    interfaces = module.params.get("interfaces")

    if interfaces:
        # Batch mode: apply same tags/tag_state to all listed interfaces
        results = []
        any_changed = False
        for entry in interfaces:
            sys_name = entry.get("system_name")
            if_name = entry.get("interface_name")
            if not sys_name or not if_name:
                module.fail_json(
                    msg=(
                        "Each entry in 'interfaces' must have "
                        "system_name and interface_name"
                    )
                )
            iface = find_interface_node(client_factory, blueprint_id, sys_name, if_name)
            if iface is None:
                module.fail_json(
                    msg=(
                        f"Interface '{if_name}' not found on system '{sys_name}' "
                        f"in blueprint '{blueprint_id}'"
                    )
                )
            r = set_interface_tags(
                client_factory, blueprint_id, iface["id"], tags, state=tag_state
            )
            if r.get("changed"):
                any_changed = True
            results.append(
                {
                    "system_name": sys_name,
                    "interface_name": if_name,
                    "changed": r.get("changed", False),
                    "interface_node_id": r.get("node_id", iface["id"]),
                    "interface_tags": r.get("tags", []),
                }
            )
        return dict(
            changed=any_changed,
            interfaces=results,
            msg=f"Tagged {len(interfaces)} interface(s)",
        )

    # Single-interface mode (backward compatible)
    iface_id = _resolve_interface_node_id(module, client_factory, blueprint_id)
    result = set_interface_tags(
        client_factory, blueprint_id, iface_id, tags, state=tag_state
    )
    result["interface_node_id"] = result.pop("node_id", iface_id)
    result["interface_tags"] = result.pop("tags", [])
    return result


def _handle_lag_updated(module, client_factory, blueprint_id):
    """Handle state=lag_updated — set lag_mode on a port-channel interface."""
    lag_mode = module.params.get("lag_mode")
    if not lag_mode:
        module.fail_json(msg="lag_mode is required when state=lag_updated")

    port_channel_id = module.params.get("port_channel_id")
    iface_id = _resolve_interface_node_id(module, client_factory, blueprint_id)
    result = set_lag_mode(
        client_factory,
        blueprint_id,
        iface_id,
        lag_mode,
        port_channel_id=port_channel_id,
    )
    result["interface_node_id"] = result.pop("node_id", iface_id)
    return result


# ──────────────────────────────────────────────────────────────────
#  QE query handlers (state=queried)
# ──────────────────────────────────────────────────────────────────


def _handle_raw_query(client_factory, blueprint_id, query_str):
    """Run a raw QE query string."""
    items = run_qe_query(client_factory, blueprint_id, query_str)
    return dict(
        changed=False,
        results=items,
        msg=f"QE query returned {len(items)} item(s)",
    )


def _handle_nodes_by_role(client_factory, blueprint_id, roles):
    """Discover system nodes filtered by role."""
    nodes = find_nodes_by_role(client_factory, blueprint_id, roles)
    return dict(
        changed=False,
        nodes=nodes,
        msg=f"Found {len(nodes)} node(s)",
    )


def _handle_nodes_by_type(client_factory, blueprint_id, system_type):
    """Discover system nodes by system_type."""
    nodes = find_nodes_by_type(client_factory, blueprint_id, system_type)
    return dict(
        changed=False,
        nodes=nodes,
        msg=f"Found {len(nodes)} node(s) of type '{system_type}'",
    )


def _handle_interfaces_by_neighbor(client_factory, blueprint_id, params):
    """Find switch interfaces linked to specific neighbor systems."""
    interfaces = find_interfaces_by_neighbor(
        client_factory,
        blueprint_id,
        params.get("neighbor_labels"),
        neighbor_system_type=params.get("neighbor_system_type", "server"),
        if_type=params.get("if_type", "ethernet"),
        local_role=params.get("local_role", "leaf"),
    )
    intf_ids = [i["intf_id"] for i in interfaces if i.get("intf_id")]
    return dict(
        changed=False,
        interfaces=interfaces,
        interface_ids=intf_ids,
        msg=f"Found {len(interfaces)} interface(s)",
    )


def _handle_host_bond_interfaces(client_factory, blueprint_id, host_labels):
    """Find port-channel (bond) interfaces on host generic systems."""
    host_intfs = find_host_bond_interfaces(
        client_factory,
        blueprint_id,
        host_labels,
    )
    return dict(
        changed=False,
        host_interfaces=host_intfs,
        msg=f"Found bond interfaces for {len(host_intfs)} host(s)",
    )


def _handle_host_evpn_interfaces(client_factory, blueprint_id, host_labels):
    """Find ESI-LAG group interfaces (EVPN application points) for hosts."""
    host_intfs = find_host_evpn_interfaces(
        client_factory,
        blueprint_id,
        host_labels,
    )
    return dict(
        changed=False,
        host_interfaces=host_intfs,
        msg=f"Found EVPN interfaces for {len(host_intfs)} host(s)",
    )


def _handle_queried(module, client_factory, blueprint_id):
    """Handle state=queried -- dispatch to the right query handler."""
    params = module.params
    raw_query = params.get("query")
    query_type = params.get("query_type")

    if not raw_query and not query_type:
        module.fail_json(msg="state=queried requires either 'query' or 'query_type'")
    if raw_query and query_type:
        module.fail_json(msg="'query' and 'query_type' are mutually exclusive")

    if raw_query:
        return _handle_raw_query(client_factory, blueprint_id, raw_query)

    handlers = {
        "nodes_by_role": lambda: _handle_nodes_by_role(
            client_factory,
            blueprint_id,
            params.get("roles"),
        ),
        "nodes_by_type": lambda: _handle_nodes_by_type(
            client_factory,
            blueprint_id,
            params.get("system_type"),
        ),
        "interfaces_by_neighbor": lambda: _handle_interfaces_by_neighbor(
            client_factory,
            blueprint_id,
            params,
        ),
        "host_bond_interfaces": lambda: _handle_host_bond_interfaces(
            client_factory,
            blueprint_id,
            params.get("host_labels"),
        ),
        "host_evpn_interfaces": lambda: _handle_host_evpn_interfaces(
            client_factory,
            blueprint_id,
            params.get("host_labels"),
        ),
    }

    handler = handlers.get(query_type)
    if not handler:
        module.fail_json(msg=f"Unknown query_type: {query_type}")

    return handler()


# ──────────────────────────────────────────────────────────────────
#  Node update handler (state=node_updated)
# ──────────────────────────────────────────────────────────────────


def _handle_node_updated(module, client_factory, blueprint_id):
    """Handle state=node_updated -- single-node or bulk-by-label assignment.

    Supports three modes:
      1. ``assignment`` dict -- bulk assign by label
      2. ``node_id`` + ``node_properties`` -- patch by UUID (top-level params)
      3. ``body.node_id`` + ``body.node_properties`` -- patch by label
         (e.g. ``body.node_id: "leaf1:xe-0/0/7.100"``)
    """
    params = module.params
    node_id = params.get("node_id")
    assignment = params.get("assignment")
    body = params.get("body")

    # ── Body-based mode (body.node_id + body.node_properties) ─────────
    if body and "node_id" in body:
        if node_id or assignment:
            module.fail_json(
                msg="body.node_id cannot be used with top-level "
                "node_id or assignment"
            )
        body_node_id = body["node_id"]
        body_props = body.get("node_properties", {})
        if not body_props:
            module.fail_json(
                msg="body.node_properties is required when using body.node_id"
            )

        # Resolve label-based node_id (e.g. "leaf1:xe-0/0/7.100") to UUID
        resolved_id = body_node_id
        if ":" in body_node_id:
            try:
                resolved_id = resolve_graph_node_id(
                    client_factory, blueprint_id, body_node_id
                )
            except ValueError as exc:
                module.fail_json(msg=str(exc))

        # Read current node, compute diff, patch
        current = get_node(client_factory, blueprint_id, resolved_id)
        if current is None:
            module.fail_json(
                msg=f"Node '{body_node_id}' (resolved: {resolved_id}) "
                f"not found in blueprint '{blueprint_id}'"
            )

        changes = node_needs_update(current, body_props)
        if not changes:
            return dict(
                changed=False,
                node=current,
                node_id=resolved_id,
                msg="node already up to date",
            )

        patch_node(client_factory, blueprint_id, resolved_id, changes)
        final = {**current, **changes}
        return dict(
            changed=True,
            node=final,
            node_id=resolved_id,
            msg=f"node updated: {', '.join(changes.keys())}",
        )

    # ── Bulk assignment mode (assignment dict) ────────────────────────────
    if assignment:
        if node_id:
            module.fail_json(msg="node_id and assignment are mutually exclusive")
        deploy_mode = params.get("deploy_mode")
        result = assign_nodes_by_label(
            client_factory, blueprint_id, assignment, deploy_mode=deploy_mode
        )
        if result["labels_not_found"]:
            module.fail_json(
                msg=(
                    "The following node labels were not found in the blueprint: "
                    + ", ".join(result["labels_not_found"])
                ),
                **result,
            )
        n = len(result["nodes_updated"])
        u = len(result["nodes_unchanged"])
        result["msg"] = f"{n} node(s) updated, {u} already up to date"
        return result

    # ── Resolve current_label → node_id ────────────────────────────────────
    current_label = params.get("current_label")
    node_type = params.get("node_type")
    node_id_already_resolved = False
    if current_label and not node_id:
        if node_type == "rack":
            try:
                node_id = resolve_rack_node_id(
                    client_factory, blueprint_id, current_label
                )
            except ValueError as exc:
                module.fail_json(msg=str(exc))
        else:
            all_nodes = list_nodes(client_factory, blueprint_id)
            matched_id = next(
                (
                    nid
                    for nid, nprops in all_nodes.items()
                    if nprops.get("label") == current_label
                    and (node_type is None or nprops.get("type") == node_type)
                ),
                None,
            )
            if matched_id is None:
                filter_msg = f" of type '{node_type}'" if node_type else ""
                module.fail_json(
                    msg=f"No node{filter_msg} with label '{current_label}' found in blueprint '{blueprint_id}'"
                )
            node_id = matched_id
        node_id_already_resolved = True

    # ── Single-node mode (node_id) ────────────────────────────────────────
    if not node_id:
        module.fail_json(
            msg="Either node_id, current_label, or assignment is required when state=node_updated"
        )

    # Normalise: node_id may be a str or a list of str
    if isinstance(node_id, str):
        node_ids = [node_id]
    else:
        node_ids = list(node_id)

    # Resolve each entry: label → graph-node UUID via system/rack node resolution
    # Skip resolution if node_id was already resolved from current_label
    if node_id_already_resolved:
        resolved_ids = [(nid, nid) for nid in node_ids]
    else:
        resolved_ids = []
        for nid in node_ids:
            try:
                if node_type == "rack":
                    resolved = resolve_rack_node_id(client_factory, blueprint_id, nid)
                else:
                    resolved = resolve_system_node_id(client_factory, blueprint_id, nid)
            except ValueError as exc:
                module.fail_json(msg=str(exc))
            resolved_ids.append((nid, resolved))

    # Build desired fields from params
    desired = {}
    for field, param in (
        ("system_id", "system_id"),
        ("deploy_mode", "deploy_mode"),
        ("hostname", "hostname"),
        ("label", "node_label"),
    ):
        value = params.get(param)
        if value is not None:
            desired[field] = value

    # Merge arbitrary node_properties (if_name, external, etc.)
    node_properties = params.get("node_properties")
    if node_properties and isinstance(node_properties, dict):
        desired.update(node_properties)

    if not desired:
        return dict(
            changed=False,
            msg="no node fields to update",
        )

    # Apply to each resolved node
    nodes_updated = []
    nodes_unchanged = []
    for orig_ref, resolved_id in resolved_ids:
        current = get_node(client_factory, blueprint_id, resolved_id)
        if current is None:
            module.fail_json(
                msg=f"Node '{orig_ref}' (resolved: {resolved_id}) not found in blueprint '{blueprint_id}'"
            )

        changes = node_needs_update(current, desired)
        if not changes:
            nodes_unchanged.append(resolved_id)
            continue

        patch_node(client_factory, blueprint_id, resolved_id, changes)
        nodes_updated.append({**current, **changes, "node_id": resolved_id})

    # Return single-node result format when only one node was targeted
    if len(resolved_ids) == 1:
        orig_ref, resolved_id = resolved_ids[0]
        if nodes_updated:
            node_state = nodes_updated[0]
            return dict(
                changed=True,
                node=node_state,
                node_id=resolved_id,
                msg=f"node updated: {', '.join(k for k in desired if k in node_state)}",
            )
        else:
            return dict(
                changed=False,
                node=get_node(client_factory, blueprint_id, resolved_id),
                node_id=resolved_id,
                msg="node already up to date",
            )

    # Multi-node result format
    n = len(nodes_updated)
    u = len(nodes_unchanged)
    return dict(
        changed=bool(nodes_updated),
        nodes_updated=nodes_updated,
        nodes_unchanged=nodes_unchanged,
        msg=f"{n} node(s) updated, {u} already up to date",
    )


# ──────────────────────────────────────────────────────────────────
#  Module entry point
# ──────────────────────────────────────────────────────────────────


def main():
    blueprint_module_args = dict(
        id=dict(type="dict", required=False),
        body=dict(type="dict", required=False),
        lock_state=dict(
            type="str",
            required=False,
            choices=["locked", "unlocked", "ignore"],
            default="locked",
        ),
        lock_timeout=dict(
            type="int", required=False, default=DEFAULT_BLUEPRINT_LOCK_TIMEOUT
        ),
        commit_timeout=dict(
            type="int", required=False, default=DEFAULT_BLUEPRINT_COMMIT_TIMEOUT
        ),
        commit_description=dict(type="str", required=False),
        unlock=dict(type="bool", required=False, default=False),
        state=dict(
            type="str",
            required=False,
            choices=[
                "present",
                "committed",
                "absent",
                "queried",
                "node_updated",
                "rack_added",
                "rack_deleted",
                "interface_updated",
                "interface_tagged",
                "lag_updated",
            ],
            default="present",
        ),
        # Rack management params (state=rack_added / rack_deleted)
        rack_type=dict(type="str", required=False),
        rack_count=dict(type="int", required=False),
        racks_to_add=dict(type="int", required=False),
        # Query params (state=queried)
        query=dict(type="str", required=False),
        query_type=dict(
            type="str",
            required=False,
            choices=[
                "nodes_by_role",
                "nodes_by_type",
                "interfaces_by_neighbor",
                "host_bond_interfaces",
                "host_evpn_interfaces",
            ],
        ),
        roles=dict(type="list", elements="str", required=False),
        system_type=dict(type="str", required=False),
        neighbor_labels=dict(type="list", elements="str", required=False),
        host_labels=dict(type="list", elements="str", required=False),
        neighbor_system_type=dict(type="str", required=False, default="server"),
        local_role=dict(type="str", required=False, default="leaf"),
        if_type=dict(type="str", required=False, default="ethernet"),
        # Node params (state=node_updated)
        assignment=dict(type="dict", required=False),
        node_id=dict(type="raw", required=False, aliases=["rack_id"]),
        system_id=dict(type="str", required=False),
        deploy_mode=dict(
            type="str",
            required=False,
            choices=["deploy", "undeploy", "drain", "ready"],
        ),
        current_label=dict(type="str", required=False),
        node_type=dict(type="str", required=False),
        hostname=dict(type="str", required=False),
        node_label=dict(type="str", required=False, aliases=["rack_label"]),
        node_properties=dict(type="dict", required=False),
        # Interface management params (state=interface_updated / interface_tagged / lag_updated)
        system_name=dict(type="str", required=False),
        interface_name=dict(type="str", required=False),
        admin_state=dict(type="str", required=False, choices=["up", "down"]),
        interfaces=dict(type="list", elements="dict", required=False),
        tags=dict(type="list", elements="str", required=False),
        tag_state=dict(
            type="str", required=False, choices=["present", "absent"], default="present"
        ),
        lag_mode=dict(
            type="str",
            required=False,
            choices=["lacp_active", "lacp_passive", "static_lag", "none"],
        ),
        port_channel_id=dict(type="int", required=False),
    )
    client_module_args = apstra_client_module_args()
    module_args = client_module_args | blueprint_module_args

    # values expected to get set: changed, blueprint, msg
    result = dict(changed=False)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        mutually_exclusive=[
            ("query", "query_type"),
            ("node_id", "assignment"),
            ("node_id", "current_label"),
        ],
    )

    try:
        # Instantiate the client factory
        client_factory = ApstraClientFactory.from_params(module)

        # Get the id if specified
        id = module.params.get("id", None)
        blueprint_id = id.get("blueprint", None) if id is not None else None
        body = module.params.get("body", None)
        state = module.params["state"]
        lock_state = module.params["lock_state"]
        lock_timeout = module.params["lock_timeout"]
        commit_timeout = module.params["commit_timeout"]

        # Resolve blueprint name to ID if needed
        if blueprint_id:
            blueprint_id = client_factory.resolve_blueprint_id(blueprint_id)
            id["blueprint"] = blueprint_id

        # ── state=queried ─────────────────────────────────────────
        if state == "queried":
            if not blueprint_id:
                module.fail_json(msg="id.blueprint is required when state=queried")
            result = _handle_queried(module, client_factory, blueprint_id)
            module.exit_json(**result)
            return

        # ── state=node_updated ────────────────────────────────────
        if state == "node_updated":
            if not blueprint_id:
                module.fail_json(msg="id.blueprint is required when state=node_updated")
            result = _handle_node_updated(module, client_factory, blueprint_id)
            module.exit_json(**result)
            return

        # ── state=rack_added ─────────────────────────────────────
        if state == "rack_added":
            if not blueprint_id:
                module.fail_json(msg="id.blueprint is required when state=rack_added")
            result = _handle_rack_added(module, client_factory, blueprint_id)
            module.exit_json(**result)
            return

        # ── state=rack_deleted ────────────────────────────────────
        if state == "rack_deleted":
            if not blueprint_id:
                module.fail_json(msg="id.blueprint is required when state=rack_deleted")
            result = _handle_rack_deleted(module, client_factory, blueprint_id)
            module.exit_json(**result)
            return

        # ── state=interface_updated ───────────────────────────────
        if state == "interface_updated":
            if not blueprint_id:
                module.fail_json(
                    msg="id.blueprint is required when state=interface_updated"
                )
            result = _handle_interface_updated(module, client_factory, blueprint_id)
            module.exit_json(**result)
            return

        # ── state=interface_tagged ────────────────────────────────
        if state == "interface_tagged":
            if not blueprint_id:
                module.fail_json(
                    msg="id.blueprint is required when state=interface_tagged"
                )
            result = _handle_interface_tagged(module, client_factory, blueprint_id)
            module.exit_json(**result)
            return

        # ── state=lag_updated ─────────────────────────────────────
        if state == "lag_updated":
            if not blueprint_id:
                module.fail_json(msg="id.blueprint is required when state=lag_updated")
            result = _handle_lag_updated(module, client_factory, blueprint_id)
            module.exit_json(**result)
            return

        # ── state=present / committed / absent (original logic) ───
        if state != "absent":
            if id is None:
                if body is None:
                    raise ValueError(
                        "Must specify 'body' with a 'label' property if blueprint id is unspecified"
                    )

                # Resolve template_id if provided (accepts display_name)
                if "template_id" in body:
                    body["template_id"] = _resolve_template_id(
                        client_factory, body["template_id"]
                    )

                # See if the object label exists
                blueprint = (
                    client_factory.object_request("blueprints", "get", {}, body)
                    if "label" in body
                    else None
                )
                if blueprint:
                    result["changed"] = False
                    # Blueprint does not support updates, make sure there's no changes
                    changes = {}
                    if client_factory.compare_and_update(blueprint, body, changes):
                        raise ValueError(
                            "Blueprint already exists and cannot be updated: {}".format(
                                changes
                            )
                        )
                else:
                    # Create the object
                    blueprint = client_factory.object_request(
                        "blueprints", "create", {}, body
                    )
                    result["changed"] = True
                    sleep(5)  # Wait for the blueprint to be created

                blueprint_id = blueprint["id"]
                id = {"blueprint": blueprint_id}
                # Cache the design for subsequent operations (commit, lock, etc.)
                design = body.get("design") or blueprint.get("design")
                client_factory.set_blueprint_design(blueprint_id, design)
                result["id"] = id
                result["response"] = blueprint
                result["msg"] = "blueprint created successfully"

        # If we still don't have an id, there's a problem
        if id is None:
            raise ValueError("Cannot manage a blueprint without a object id")

        # Lock the object if requested
        if lock_state == "locked" and state != "absent":
            module.log("Locking blueprint")
            if client_factory.lock_blueprint(blueprint_id, lock_timeout):
                result["changed"] = True

        if state == "absent":
            if id is None:
                raise ValueError("Cannot delete a blueprint without a object id")
            # Delete the blueprint
            client_factory.object_request("blueprints", "delete", id)
            result["changed"] = True
            result["msg"] = "blueprint deleted successfully"

        if state == "committed":
            # Commit the blueprint
            commit_description = module.params.get("commit_description")
            committed = client_factory.commit_blueprint(
                blueprint_id, commit_timeout, description=commit_description
            )
            result["changed"] = committed
            result["msg"] = "blueprint committed successfully"

        # Unlock the blueprint if requested
        if state == "absent":
            # If the blueprint is deleted, it will be unlocked (tag deleted)
            lock_state = "unlocked"
        elif lock_state == "unlocked":
            unlocked = client_factory.unlock_blueprint(blueprint_id)
            result["changed"] = unlocked

        # Always report the lock state
        result["lock_state"] = lock_state

    except Exception as e:
        tb = traceback.format_exc()
        module.debug(f"Exception occurred: {str(e)}\n\nStack trace:\n{tb}")
        result.pop("msg", None)
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
