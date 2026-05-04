#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# Apache License, Version 2.0 (see https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: design
short_description: Manage Apstra design elements (logical devices, rack types, templates)
description:
  - Create or ensure existence of Apstra design elements required before
    blueprint creation.
  - Supports logical devices, rack types, rack-based templates, and
    interface maps.
  - Uses the AOS SDK generator functions to build proper API payloads
    from simplified YAML definitions (same format as aos_models/).
  - Idempotent — skips creation if the element already exists.
version_added: "0.1.0"
author:
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
      - Identifies the design element.
      - Must contain C(design_type) and C(name).
    type: dict
    required: true
    suboptions:
      design_type:
        description:
          - The type of design element to manage.
        type: str
        required: true
        choices:
          - logical_device
          - rack_type
          - template
          - interface_map
      name:
        description:
          - The name/id of the design element.
        type: str
        required: true
  body:
    description:
      - The specification dict for the design element.
      - For logical_device — must contain C(panels) list.
      - For rack_type — must contain C(leafs) and optionally C(generics), C(access).
      - For template — must contain C(spine), C(racks), and optionally
        C(overlay_control_protocol), C(asn_allocation_policy).
      - For interface_map — must contain C(logical_device) and C(device_profile).
        Optionally C(dp_usage) (list of [port_id, transform_id] pairs); if omitted,
        auto-generated from the device profile's default transformations.
    type: dict
    required: false
  state:
    description:
      - Desired state of the design element.
      - C(present) creates the element if it does not exist.
      - C(absent) deletes the element.
      - C(queried) lists elements of the given C(design_type).
        When C(id.name) is provided, returns that single element.
        When C(id.name) is C('*') or C('all'), returns all elements
        of the type.
    type: str
    required: false
    default: present
    choices:
      - present
      - absent
      - queried
"""

EXAMPLES = """
- name: Create logical device
  juniper.apstra.design:
    api_url: "https://apstra:443/api"
    auth_token: "{{ token }}"
    id:
      design_type: logical_device
      name: simple_dc_vjunos_switch_96x1
    body:
      panels:
        - panel1:
            portgroups:
              - portgroup1:
                  ports: 96
                  speed: 1
                  connects_to:
                    - superspine
                    - spine
                    - leaf
                    - access
                    - peer
                    - unused
                    - generic
    state: present

- name: Create rack type
  juniper.apstra.design:
    api_url: "https://apstra:443/api"
    auth_token: "{{ token }}"
    id:
      design_type: rack_type
      name: connectorops_vjunos-rack
    body:
      leafs:
        - leaf1:
            label: leaf-1
            link_per_spine_count: 1
            link_per_spine_speed: 1
            logical_device: simple_dc_vjunos_switch_96x1
            redundancy_protocol: esi
      generics:
        - host1:
            label: host-1
            logical_device: AOS-2x1-1
            links:
              - link1:
                  link_speed: 1
                  target_switch_label: leaf-1
                  link_per_switch_count: 1
                  label: host1_leaf1_link
                  lag_mode: lacp_active
                  attachment_type: dualAttached
    state: present

- name: Create template
  juniper.apstra.design:
    api_url: "https://apstra:443/api"
    auth_token: "{{ token }}"
    id:
      design_type: template
      name: connectorops_2spine4leaf
    body:
      spine:
        logical_device: simple_dc_vjunos_switch_96x1
        count: 2
      racks:
        connectorops_vjunos-rack: 1
      overlay_control_protocol: evpn
      asn_allocation_policy: distinct
    state: present

- name: Delete a design element
  juniper.apstra.design:
    api_url: "https://apstra:443/api"
    auth_token: "{{ token }}"
    id:
      design_type: template
      name: connectorops_2spine4leaf
    state: absent

- name: Create interface map (auto-generates port mappings from device profile)
  juniper.apstra.design:
    api_url: "https://apstra:443/api"
    auth_token: "{{ token }}"
    id:
      design_type: interface_map
      name: simple_dc_vjunos_ifmap
    body:
      logical_device: simple_dc_vjunos_switch_96x1
      device_profile: vJunos-switch
    state: present

- name: List all interface maps
  juniper.apstra.design:
    api_url: "https://apstra:443/api"
    auth_token: "{{ token }}"
    id:
      design_type: interface_map
      name: all
    state: queried
  register: all_imaps

- name: Use queried interface maps
  ansible.builtin.debug:
    msg: "Found {{ all_imaps.design_items | length }} interface maps"

- name: Query a specific logical device by name
  juniper.apstra.design:
    api_url: "https://apstra:443/api"
    auth_token: "{{ token }}"
    id:
      design_type: logical_device
      name: AOS-7x10-Leaf
    state: queried
  register: ld_result

- name: Show queried logical device
  ansible.builtin.debug:
    msg: "Logical device: {{ ld_result.data }}"
"""

RETURN = """
id:
  description: The ID of the design element.
  type: str
  returned: always
data:
  description: The full design element data from the server.
  type: dict
  returned: when state is present, absent, or queried with a specific name
design_items:
  description:
    - List of design elements returned by C(state=queried).
    - When querying all (C(name=all) or C(name=*)), contains every element
      of the given C(design_type).
    - When querying a specific name, contains a single-element list.
  type: list
  elements: dict
  returned: when state is queried
changed:
  description: Whether the element was created or already existed.
  type: bool
  returned: always
"""

import traceback

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.juniper.apstra.plugins.module_utils.apstra.client import (
    apstra_client_module_args,
    ApstraClientFactory,
)

try:
    import aos.sdk.generator as g
except ImportError:
    g = None

try:
    from aos.sdk.interface_map.interface_map_generator import (
        gen_interface_map as _sdk_gen_interface_map,
    )
except ImportError:
    _sdk_gen_interface_map = None


# ── Logical Device Helpers ───────────────────────────────────────────────────


def _parse_logical_device_panels(spec):
    """
    Convert YAML-format panels to the raw_data format expected by
    gen_logical_device: list of lists of tuples (count, speed, roles).
    """
    panels = []
    for panel_item in spec.get("panels", []):
        if isinstance(panel_item, dict):
            for _panel_name, panel_config in panel_item.items():
                portgroups = []
                for pg_item in panel_config.get("portgroups", []):
                    if isinstance(pg_item, dict):
                        for _pg_name, pg_config in pg_item.items():
                            portgroups.append(
                                (
                                    pg_config["ports"],
                                    pg_config["speed"],
                                    pg_config.get("connects_to", []),
                                )
                            )
                panels.append(portgroups)
    return panels


def _create_logical_device(client, name, spec):
    """Create a logical device via the AOS SDK generator + API."""
    panels = _parse_logical_device_panels(spec)
    payload = g.gen_logical_device(name, panels)
    client.logical_devices.create(payload)
    return client.logical_devices[name].get()


def _get_logical_device(client, name):
    """Try to get an existing logical device by name or ID. Returns None if not found."""
    # Try direct lookup (works when name is an ID or server resolves display names)
    try:
        result = client.logical_devices[name].get()
        if result:
            return result
    except Exception:
        pass
    # Fallback: list all logical devices and match by display_name
    try:
        all_lds = client.logical_devices.list()
        items = all_lds.get("items", []) if isinstance(all_lds, dict) else all_lds
        for ld in items:
            if isinstance(ld, dict) and ld.get("display_name") == name:
                return ld
    except Exception:
        pass
    return None


# ── Rack Type Helpers ────────────────────────────────────────────────────────


def _parse_rack_type_leafs(spec):
    """Parse leaf definitions from YAML spec into gen_rack_type_leaf() calls."""
    leafs = []
    for leaf_item in spec.get("leafs", []):
        if isinstance(leaf_item, dict):
            for _leaf_name, lc in leaf_item.items():
                leafs.append(
                    g.gen_rack_type_leaf(
                        label=lc["label"],
                        logical_device=lc["logical_device"],
                        link_per_spine_count=lc.get("link_per_spine_count", 1),
                        link_per_spine_speed=lc.get("link_per_spine_speed", 1),
                        redundancy_protocol=lc.get("redundancy_protocol"),
                        leaf_leaf_link_count=lc.get("leaf_leaf_link_count", 0),
                        leaf_leaf_link_speed=lc.get("leaf_leaf_link_speed", 40),
                        leaf_leaf_l3_link_count=lc.get("leaf_leaf_l3_link_count", 0),
                        leaf_leaf_l3_link_speed=lc.get("leaf_leaf_l3_link_speed", 40),
                        leaf_leaf_link_port_channel_id=lc.get(
                            "leaf_leaf_link_port_channel_id", 0
                        ),
                        leaf_leaf_l3_link_port_channel_id=lc.get(
                            "leaf_leaf_l3_link_port_channel_id", 0
                        ),
                        mlag_vlan_id=lc.get("mlag_vlan_id", 0),
                    )
                )
    return leafs


def _parse_rack_type_links(link_list):
    """Parse link definitions from YAML into gen_rack_type_server_link() calls."""
    links = []
    for link_item in link_list:
        if isinstance(link_item, dict):
            for _link_name, lk in link_item.items():
                links.append(
                    g.gen_rack_type_server_link(
                        label=lk.get("label", "link"),
                        target_switch_label=lk.get("target_switch_label", "leaf"),
                        link_per_switch_count=lk.get("link_per_switch_count", 1),
                        link_speed=lk.get("link_speed", 1),
                        attachment_type=lk.get("attachment_type", "singleAttached"),
                        switch_peer=lk.get("switch_peer"),
                        lag_mode=lk.get("lag_mode"),
                    )
                )
    return links


def _parse_rack_type_generics(spec):
    """Parse generic system definitions from YAML spec."""
    generics = []
    for gen_item in spec.get("generics", []):
        if isinstance(gen_item, dict):
            for _gen_name, gc in gen_item.items():
                links = _parse_rack_type_links(gc.get("links", []))
                generics.append(
                    g.gen_rack_type_generic_system(
                        label=gc["label"],
                        logical_device=gc["logical_device"],
                        links=links,
                        tags=gc.get("tags", []),
                    )
                )
    return generics


def _parse_rack_type_access(spec):
    """Parse access switch definitions from YAML spec."""
    access_switches = []
    for acc_item in spec.get("access", []):
        if isinstance(acc_item, dict):
            for _acc_name, ac in acc_item.items():
                links = _parse_rack_type_links(ac.get("links", []))
                access_switches.append(
                    g.gen_rack_type_access_switch(
                        label=ac["label"],
                        logical_device=ac["logical_device"],
                        links=links,
                        redundancy_protocol=ac.get("redundancy_protocol"),
                        access_access_link_count=ac.get("access_access_link_count", 0),
                        access_access_link_speed=ac.get("access_access_link_speed", 1),
                    )
                )
    return access_switches


def _create_rack_type(client, name, spec):
    """Create a rack type via the AOS SDK generator + API."""
    leafs = _parse_rack_type_leafs(spec)
    generics = _parse_rack_type_generics(spec)
    access_switches = _parse_rack_type_access(spec)

    # Resolve logical device objects — the generator needs full LD objects
    # in the leafs/generics to collect them into the rack_type.logical_devices[]
    ld_cache = {}
    for system_list in [leafs, generics, access_switches]:
        for system in system_list:
            ld_name = system["logical_device"]
            if isinstance(ld_name, str) and ld_name not in ld_cache:
                ld_obj = _get_logical_device(client, ld_name)
                if ld_obj:
                    ld_cache[ld_name] = ld_obj
                else:
                    raise Exception(
                        f"Logical device '{ld_name}' not found. "
                        "Verify the name matches the display name in "
                        "Design > Logical Devices."
                    )
            if isinstance(ld_name, str) and ld_name in ld_cache:
                system["logical_device"] = ld_cache[ld_name]

    payload = g.gen_rack_type(
        name=name,
        leafs=leafs,
        generic_systems=generics,
        access_switches=access_switches if access_switches else None,
        fabric_connectivity_design=spec.get("fabric_connectivity_design", "l3clos"),
    )
    client.rack_types.create(payload)
    return client.rack_types[name].get()


def _get_rack_type(client, name):
    """Try to get an existing rack type by name or ID. Returns None if not found."""
    # Try direct lookup (works when name is an ID or server resolves display names)
    try:
        result = client.rack_types[name].get()
        if result:
            return result
    except Exception:
        pass
    # Fallback: list all rack types and match by display_name
    try:
        all_rts = client.rack_types.list()
        items = all_rts.get("items", []) if isinstance(all_rts, dict) else all_rts
        for rt in items:
            if isinstance(rt, dict) and rt.get("display_name") == name:
                return rt
    except Exception:
        pass
    return None


# ── Template Helpers ─────────────────────────────────────────────────────────


def _create_template(client, name, spec):
    """Create a rack-based template via the AOS SDK generator + API."""
    # Resolve spine logical device
    spine_ld_name = spec["spine"]["logical_device"]
    spine_ld = _get_logical_device(client, spine_ld_name)
    if not spine_ld:
        raise Exception(
            f"Spine logical device '{spine_ld_name}' not found. "
            "Create it first with design_type=logical_device."
        )

    superspine_config = spec.get("superspine")
    spine = g.gen_spine_type(
        logical_device=spine_ld,
        count=spec["spine"]["count"],
        link_per_superspine_count=(
            superspine_config["link_per_superspine_count"] if superspine_config else 0
        ),
        link_per_superspine_speed=(
            superspine_config["link_per_superspine_speed"] if superspine_config else 0
        ),
    )

    # Resolve rack types
    rack_types = []
    rack_type_counts = {}
    for rt_name, rt_count in spec.get("racks", {}).items():
        rt = _get_rack_type(client, rt_name)
        if not rt:
            raise Exception(
                f"Rack type '{rt_name}' not found. "
                "Create it first with design_type=rack_type."
            )
        rack_types.append(rt)
        rack_type_counts[rt["id"]] = rt_count

    overlay = spec.get("overlay_control_protocol")
    asn_policy = spec.get("asn_allocation_policy", "distinct")

    payload = g.gen_rack_based_template(
        name=name,
        spine=spine,
        rack_types=rack_types,
        rack_type_counts=rack_type_counts,
        virtual_network_policy=g.gen_virtual_network_policy(
            overlay_control_protocol=overlay,
        ),
        asn_allocation_policy=g.gen_asn_allocation_policy(
            spine_asn_scheme=asn_policy,
        ),
    )
    client.templates.create(payload)
    return client.templates[name].get()


def _get_template(client, name):
    """Try to get an existing template by name or ID. Returns None if not found."""
    # Try direct lookup (works when name is an ID or server resolves display names)
    try:
        result = client.templates[name].get()
        if result:
            return result
    except Exception:
        pass
    # Fallback: list all templates and match by display_name
    try:
        all_templates = client.templates.list()
        items = (
            all_templates.get("items", [])
            if isinstance(all_templates, dict)
            else all_templates
        )
        for tmpl in items:
            if isinstance(tmpl, dict) and tmpl.get("display_name") == name:
                return tmpl
    except Exception:
        pass
    return None


# ── Interface Map Helpers ────────────────────────────────────────────────────


def _list_interface_maps(client):
    """List all design interface maps. Returns a list of dicts."""
    result = client.request("/design/interface-maps", method="GET")
    if not result:
        return []
    return result.get("items", [])


def _get_interface_map(client, label):
    """List design interface maps and return the one matching label. Returns None if not found."""
    for item in _list_interface_maps(client):
        if item.get("label") == label:
            return item
    return None


def _create_interface_map(client, label, spec):
    """Create a design interface map via the AOS SDK generator + API.

    spec keys:
      logical_device  — existing LD name (e.g. "simple_dc_vjunos_switch_96x1")
      device_profile  — device profile ID (e.g. "vJunos-switch")
      dp_usage        — optional list of [port_id, transform_id] pairs;
                        auto-generated from default transforms if omitted
    """
    if _sdk_gen_interface_map is None:
        raise Exception(
            "The 'aos.sdk.interface_map' package is required for interface_map creation."
        )

    dp_id = spec.get("device_profile")
    ld_id = spec.get("logical_device")

    dp = client.device_profiles[dp_id].get()
    if dp is None:
        raise Exception(f"Device profile '{dp_id}' not found.")

    ld = client.logical_devices[ld_id].get()
    if ld is None:
        raise Exception(f"Logical device '{ld_id}' not found.")

    if spec.get("dp_usage"):
        dp_usage = [tuple(u) for u in spec["dp_usage"]]
    else:
        # Auto-generate: use each port's default transformation
        dp_usage = []
        for port in dp["ports"]:
            for transform in port["transformations"]:
                if transform["is_default"]:
                    dp_usage.append((port["port_id"], transform["transformation_id"]))
                    break

    payload = _sdk_gen_interface_map(dp, ld, dp_usage, label=label)
    client.request("/design/interface-maps", method="POST", data=payload)
    return _get_interface_map(client, label)


def _delete_interface_map(client, label):
    """Delete a design interface map by label. Returns True if deleted, False if not found."""
    existing = _get_interface_map(client, label)
    if not existing:
        return False
    imap_id = existing["id"]
    client.request(f"/design/interface-maps/{imap_id}", method="DELETE")
    return True


# ── Delete Helpers ───────────────────────────────────────────────────────────


def _delete_design_element(client, design_type, name):
    """Delete a design element by type and name."""
    if design_type == "interface_map":
        return _delete_interface_map(client, name)

    resource_map = {
        "logical_device": client.logical_devices,
        "rack_type": client.rack_types,
        "template": client.templates,
    }
    resource = resource_map.get(design_type)
    if resource is None:
        raise Exception(f"Unsupported design_type: {design_type}")
    try:
        resource[name].delete()
        return True
    except Exception:
        return False


def _list_design_elements(client, design_type):
    """List all design elements of a given type. Returns a list of dicts."""
    if design_type == "interface_map":
        return _list_interface_maps(client)

    resource_map = {
        "logical_device": client.logical_devices,
        "rack_type": client.rack_types,
        "template": client.templates,
    }
    resource = resource_map.get(design_type)
    if resource is None:
        raise Exception(f"Unsupported design_type: {design_type}")
    try:
        result = resource.get()
        if isinstance(result, dict) and "items" in result:
            return result["items"]
        if isinstance(result, list):
            return result
        return [result] if result else []
    except Exception:
        return []


# ── Main ─────────────────────────────────────────────────────────────────────


def main():
    argument_spec = apstra_client_module_args()
    argument_spec.update(
        id=dict(type="dict", required=True),
        body=dict(type="dict", required=False),
        state=dict(
            type="str",
            default="present",
            choices=["present", "absent", "queried"],
        ),
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    if g is None:
        module.fail_json(msg="The 'aos' SDK package is required but not installed.")

    id_param = module.params["id"] or {}
    design_type = id_param.get("design_type")
    name = id_param.get("name")
    spec = module.params.get("body")
    state = module.params["state"]

    if (
        design_type == "interface_map"
        and state != "queried"
        and _sdk_gen_interface_map is None
    ):
        module.fail_json(
            msg="The 'aos.sdk.interface_map' package is required for interface_map operations but not installed."
        )

    if not design_type or design_type not in (
        "logical_device",
        "rack_type",
        "template",
        "interface_map",
    ):
        module.fail_json(
            msg="id.design_type is required and must be one of: logical_device, rack_type, template, interface_map"
        )
    if not name and state != "queried":
        module.fail_json(msg="id.name is required when state is 'present' or 'absent'")

    try:
        client_factory = ApstraClientFactory.from_params(module)
        client = client_factory.get_base_client()

        if state == "queried":
            # List or fetch design elements
            if name and name not in ("*", "all"):
                get_fn_map = {
                    "logical_device": _get_logical_device,
                    "rack_type": _get_rack_type,
                    "template": _get_template,
                    "interface_map": _get_interface_map,
                }
                existing = get_fn_map[design_type](client, name)
                if existing:
                    module.exit_json(
                        changed=False,
                        id=id_param,
                        data=existing,
                        design_items=[existing],
                        msg=f"{design_type} '{name}' found.",
                    )
                else:
                    module.exit_json(
                        changed=False,
                        id=id_param,
                        data={},
                        design_items=[],
                        msg=f"{design_type} '{name}' not found.",
                    )
            else:
                items = _list_design_elements(client, design_type)
                module.exit_json(
                    changed=False,
                    id=id_param,
                    design_items=items,
                    msg=f"Found {len(items)} {design_type}(s).",
                )
            return

        if state == "absent":
            deleted = _delete_design_element(client, design_type, name)
            module.exit_json(changed=deleted, id=id_param, data={})
            return

        # state == "present" — idempotent create
        if not spec:
            module.fail_json(msg="body is required when state is 'present'")
        get_fn_map = {
            "logical_device": _get_logical_device,
            "rack_type": _get_rack_type,
            "template": _get_template,
            "interface_map": _get_interface_map,
        }
        create_fn_map = {
            "logical_device": _create_logical_device,
            "rack_type": _create_rack_type,
            "template": _create_template,
            "interface_map": _create_interface_map,
        }

        existing = get_fn_map[design_type](client, name)
        if existing:
            module.exit_json(
                changed=False,
                id=id_param,
                data=existing,
                msg=f"{design_type} '{name}' already exists.",
            )
            return

        created = create_fn_map[design_type](client, name, spec)
        module.exit_json(
            changed=True,
            id=id_param,
            data=created or {},
            msg=f"{design_type} '{name}' created successfully.",
        )

    except Exception as e:
        tb = traceback.format_exc()
        module.fail_json(
            msg=f"Failed to manage {design_type} '{name}': {str(e)}",
            exception=tb,
        )


if __name__ == "__main__":
    main()
