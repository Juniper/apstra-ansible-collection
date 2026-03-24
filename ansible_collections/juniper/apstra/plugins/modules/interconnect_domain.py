#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

from __future__ import absolute_import, division, print_function

__metaclass__ = type
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.client import (
    apstra_client_module_args,
    ApstraClientFactory,
)
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.bp_interconnect_domain import (
    list_interconnect_domains,
    get_interconnect_domain,
    create_interconnect_domain,
    update_interconnect_domain,
    delete_interconnect_domain,
    find_interconnect_domain_by_label,
)

DOCUMENTATION = """
---
module: interconnect_domain

short_description: Manage EVPN Interconnect Domains in Apstra blueprints

version_added: "0.2.0"

author:
  - "Juniper Networks"

description:
  - This module allows you to create, update, and delete EVPN
    Interconnect Domains (called C(evpn_interconnect_group) in the
    Apstra API) within an Apstra blueprint.
  - An Interconnect Domain groups sites together for EVPN-based DCI
    (Data Centre Interconnect).
  - Every gateway in the domain must share the same Interconnect
    Route Target (iRT).
  - Optionally, a per-site ESI MAC can be set to generate unique
    iESI values at the MAC-VRF level.
  - This module operates at the blueprint scope and requires a
    Datacenter (two_stage_l3clos) design.
  - An Interconnect Domain is a prerequisite for the Interconnect
    Domain Gateway.
  - The equivalent Terraform resource is
    C(apstra_datacenter_interconnect_domain).

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
    default: True
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
      - Dictionary containing the blueprint and interconnect domain
        IDs.
      - C(blueprint) is always required.
      - C(evpn_interconnect_group) is optional for create (looked up
        by C(label) from C(body) for idempotency), required for
        update/delete.
    required: true
    type: dict
  body:
    description:
      - Dictionary containing the EVPN Interconnect Domain details.
      - C(label) (string) - Human-readable name for the domain
        (required for create).
      - C(route_target) (string) - The Interconnect Route Target
        (iRT) shared by all gateways in the domain.  Format is
        typically C(<asn>:<nn>) (required for create).
      - C(esi_mac) (string) - Optional per-site ESI MAC address used
        to generate unique iESI values at the MAC-VRF level.
    required: false
    type: dict
  state:
    description:
      - Desired state of the interconnect domain.
    required: false
    type: str
    choices: ["present", "absent"]
    default: "present"
"""

EXAMPLES = """
# Create an EVPN Interconnect Domain
- name: Create interconnect domain
  juniper.apstra.interconnect_domain:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    body:
      label: "dci-domain-1"
      route_target: "65500:100"
    state: present
  register: icd

# Create with ESI MAC
- name: Create interconnect domain with ESI MAC
  juniper.apstra.interconnect_domain:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    body:
      label: "dci-domain-2"
      route_target: "65500:200"
      esi_mac: "02:00:00:00:00:01"
    state: present
  register: icd_esi

# Update an interconnect domain
- name: Update interconnect domain route_target
  juniper.apstra.interconnect_domain:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
      evpn_interconnect_group: "{{ icd.id.evpn_interconnect_group }}"
    body:
      label: "dci-domain-1"
      route_target: "65500:101"
    state: present

# Update by label lookup (idempotent)
- name: Update interconnect domain by label
  juniper.apstra.interconnect_domain:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    body:
      label: "dci-domain-1"
      route_target: "65500:102"
    state: present

# Delete an interconnect domain
- name: Delete interconnect domain
  juniper.apstra.interconnect_domain:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
      evpn_interconnect_group: "{{ icd.id.evpn_interconnect_group }}"
    state: absent
"""

RETURN = """
changed:
  description: Indicates whether the module has made any changes.
  type: bool
  returned: always
changes:
  description: Dictionary of updates that were applied.
  type: dict
  returned: on update
response:
  description: The interconnect domain object details.
  type: dict
  returned: when state is present and changes are made
id:
  description: The ID dictionary of the interconnect domain.
  returned: on create, or when object identified by label
  type: dict
  sample: {
      "blueprint": "5f2a77f6-1f33-4e11-8d59-6f9c26f16962",
      "evpn_interconnect_group": "aB3xYz12KgV2mbYopw"
  }
evpn_interconnect_group:
  description: The interconnect domain object details.
  type: dict
  returned: on create or update
  sample: {
      "id": "aB3xYz12KgV2mbYopw",
      "label": "dci-domain-1",
      "route_target": "65500:100",
      "esi_mac": null
  }
msg:
  description: The output message that the module generates.
  type: str
  returned: always
"""


def main():
    object_module_args = dict(
        id=dict(type="dict", required=True),
        body=dict(type="dict", required=False),
        state=dict(
            type="str",
            required=False,
            choices=["present", "absent"],
            default="present",
        ),
    )
    client_module_args = apstra_client_module_args()
    module_args = client_module_args | object_module_args

    result = dict(changed=False)

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    try:
        client_factory = ApstraClientFactory.from_params(module)

        leaf_object_type = "evpn_interconnect_group"

        id = module.params["id"]
        body = module.params.get("body", None)
        state = module.params["state"]

        # Resolve blueprint name to ID if needed
        if "blueprint" not in id:
            raise ValueError("'blueprint' is required in id")
        id["blueprint"] = client_factory.resolve_blueprint_id(id["blueprint"])
        blueprint_id = id["blueprint"]

        domain_id = id.get(leaf_object_type, None)

        # Look up existing object
        current_object = None
        if domain_id is not None:
            current_object = get_interconnect_domain(
                client_factory, blueprint_id, domain_id
            )
        elif body is not None and "label" in body:
            found = find_interconnect_domain_by_label(
                client_factory, blueprint_id, body["label"]
            )
            if found:
                domain_id = found["id"]
                id[leaf_object_type] = domain_id
                current_object = found

        # State machine
        if state == "present":
            if current_object:
                result["id"] = id
                if body:
                    changes = {}
                    if client_factory.compare_and_update(
                        dict(current_object), body, changes
                    ):
                        updated_object = update_interconnect_domain(
                            client_factory, blueprint_id, domain_id, body
                        )
                        result["changed"] = True
                        if updated_object:
                            result["response"] = updated_object
                        result["changes"] = changes
                        result["msg"] = f"{leaf_object_type} updated successfully"
                    else:
                        result["changed"] = False
                        result["msg"] = (
                            f"{leaf_object_type} already exists, no changes " f"needed"
                        )
                else:
                    result["changed"] = False
                    result["msg"] = f"No changes specified for {leaf_object_type}"
            else:
                if body is None:
                    raise ValueError(
                        f"Must specify 'body' to create a {leaf_object_type}"
                    )
                created = create_interconnect_domain(client_factory, blueprint_id, body)
                if isinstance(created, dict) and "id" in created:
                    domain_id = created["id"]
                    id[leaf_object_type] = domain_id
                result["id"] = id
                result["changed"] = True
                result["response"] = created
                result["msg"] = f"{leaf_object_type} created successfully"

            # Return the final object state
            if current_object is not None:
                result[leaf_object_type] = current_object
            elif domain_id:
                final_obj = get_interconnect_domain(
                    client_factory, blueprint_id, domain_id
                )
                if final_obj:
                    result[leaf_object_type] = final_obj

        elif state == "absent":
            if domain_id is None:
                raise ValueError(f"Must specify '{leaf_object_type}' in id to delete")
            delete_interconnect_domain(client_factory, blueprint_id, domain_id)
            result["changed"] = True
            result["msg"] = f"{leaf_object_type} deleted successfully"

    except Exception as e:
        tb = traceback.format_exc()
        module.debug(f"Exception occurred: {str(e)}\n\nStack trace:\n{tb}")
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
