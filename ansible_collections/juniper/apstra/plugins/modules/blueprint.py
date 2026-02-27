#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

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
    patch_node,
    node_needs_update,
)

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
    default: APSTRA_API_URL environment variable
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
    default: APSTRA_USERNAME environment variable
  password:
    description:
      - The password for authentication.
    type: str
    required: false
    default: APSTRA_PASSWORD environment variable
  auth_token:
    description:
      - The authentication token to use if already authenticated.
    type: str
    required: false
    default: APSTRA_AUTH_TOKEN environment variable
  id:
    description:
      - The ID of the blueprint.
      - "Example: C({blueprint: abc-123})"
    required: false
    type: dict
  body:
    description:
      - A dictionary representing the blueprint to create.
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
  commit_timeout:
    description:
      - The timeout in seconds for committing the blueprint.
    required: false
    type: int
    default: 30
  state:
    description:
      - The desired state of the blueprint.
      - C(present) creates or verifies the blueprint exists.
      - C(committed) deploys (commits) the blueprint.
      - C(absent) deletes the blueprint.
      - C(queried) runs a graph query against the blueprint
        (read-only, never modifies the blueprint).
      - C(node_updated) patches properties on a single blueprint
        node (system_id, deploy_mode, hostname, label).
    required: false
    type: str
    choices: ["present", "committed", "absent", "queried", "node_updated"]
    default: "present"
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
  node_id:
    description:
      - The blueprint node ID to patch.
      - Only used when C(state=node_updated).
    type: str
    required: false
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
  node_label:
    description:
      - Label to set on the node.
      - Only used when C(state=node_updated).
    type: str
    required: false
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
# Create a new blueprint
- name: Create blueprint
  juniper.apstra.blueprint:
    body:
      label: my-blueprint
      design: two_stage_l3clos
      init_type: template_reference
      template_id: my-template
    state: present
  register: bp

# Commit (deploy) a blueprint
- name: Deploy blueprint
  juniper.apstra.blueprint:
    id:
      blueprint: "{{ bp.id.blueprint }}"
    lock_state: ignore
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

# Assign system_id to a blueprint node
- name: Bind device serial to spine1
  juniper.apstra.blueprint:
    id:
      blueprint: "{{ blueprint_id }}"
    node_id: "{{ spine1_node_id }}"
    system_id: "SERIAL12345"
    state: node_updated

# Set deploy mode on a node
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
node:
    description:
        - Node properties after patch.
        - Returned by C(state=node_updated).
    returned: when using node_updated
    type: dict
"""


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
    """Handle state=node_updated -- patch a single blueprint node."""
    params = module.params
    node_id = params.get("node_id")

    if not node_id:
        module.fail_json(msg="node_id is required when state=node_updated")

    # Read current node state
    current = get_node(client_factory, blueprint_id, node_id)
    if current is None:
        module.fail_json(
            msg=f"Node '{node_id}' not found in blueprint '{blueprint_id}'"
        )

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
            node=current,
            msg="no node fields to update",
        )

    # Only patch what actually changed
    changes = node_needs_update(current, desired)
    if not changes:
        return dict(
            changed=False,
            node=current,
            msg="node already up to date",
        )

    patch_node(client_factory, blueprint_id, node_id, changes)
    final = get_node(client_factory, blueprint_id, node_id)
    return dict(
        changed=True,
        node=final,
        msg=f"node updated: {', '.join(changes.keys())}",
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
        unlock=dict(type="bool", required=False, default=False),
        state=dict(
            type="str",
            required=False,
            choices=["present", "committed", "absent", "queried", "node_updated"],
            default="present",
        ),
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
        node_id=dict(type="str", required=False),
        system_id=dict(type="str", required=False),
        deploy_mode=dict(
            type="str",
            required=False,
            choices=["deploy", "undeploy", "drain", "ready"],
        ),
        hostname=dict(type="str", required=False),
        node_label=dict(type="str", required=False),
        node_properties=dict(type="dict", required=False),
    )
    client_module_args = apstra_client_module_args()
    module_args = client_module_args | blueprint_module_args

    # values expected to get set: changed, blueprint, msg
    result = dict(changed=False)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        mutually_exclusive=[("query", "query_type")],
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

        # ── state=present / committed / absent (original logic) ───
        if state != "absent":
            if id is None:
                if body is None:
                    raise ValueError(
                        "Must specify 'body' with a 'label' property if blueprint id is unspecified"
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
            committed = client_factory.commit_blueprint(blueprint_id, commit_timeout)
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
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
