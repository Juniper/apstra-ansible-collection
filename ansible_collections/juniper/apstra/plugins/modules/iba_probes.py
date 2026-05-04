#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# Apache License, Version 2.0 (see https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: iba_probes

short_description: Manage IBA (Intent-Based Analytics) probes in Apstra

version_added: "0.1.0"

author:
  - "Prabhanjan KV (@kvp_jnpr)"

description:
  - This module allows you to create, update, delete, and query IBA probes in Apstra blueprints.
  - Supports instantiation of predefined (built-in) probes as well as custom probe definitions.
  - Also manages IBA dashboards for probe visualisation.
  - Predefined probes are instantiated from a catalog of 48+ built-in probe types including
    bgp_session, traffic, device_health, ecmp_imbalance, lag_imbalance, and many more.
  - Custom probes can be created with user-defined processors and stages.
  - Probes monitor fabric health, traffic patterns, anomalies, and more.

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
  type:
    description:
      - The type of IBA resource to manage.
      - C(predefined) instantiates a probe from the Apstra predefined probe catalog.
      - C(probe) manages custom (raw) probes directly.
      - C(dashboard) manages IBA dashboards.
    required: false
    type: str
    choices: ["predefined", "probe", "dashboard"]
    default: "predefined"
  id:
    description:
      - Dictionary containing resource identifiers.
      - Always requires C(blueprint) key with the blueprint UUID or label.
      - For existing probes, include C(probe) key with probe UUID or label.
      - For dashboards, include C(dashboard) key with dashboard UUID or label.
      - Name/label resolution is supported for C(blueprint), C(probe), and C(dashboard) keys.
    required: false
    type: dict
  body:
    description:
      - Dictionary containing the resource details.
      - For predefined probes, C(predefined_probe) is the probe name (e.g. C(bgp_session)),
        and additional keys are the schema parameters (C(label), C(duration), etc.).
      - For custom probes, keys include C(label), C(description), C(disabled), and C(processors).
      - For dashboards, keys include C(label) and C(description).
    required: false
    type: dict
  state:
    description:
      - Desired state of the resource.
      - C(present) creates or updates the resource.
      - C(absent) deletes the resource.
    required: false
    type: str
    choices: ["present", "absent"]
    default: "present"
"""

EXAMPLES = """
# ── Predefined Probes ───────────────────────────────────────────────

- name: Authenticate to Apstra
  juniper.apstra.authenticate:
    logout: false
  register: auth

- name: Create a BGP Session probe from predefined
  juniper.apstra.iba_probes:
    type: predefined
    id:
      blueprint: "my-blueprint"
    body:
      predefined_probe: bgp_session
      label: "BGP Monitoring"
      duration: 300
      threshold: 40
    auth_token: "{{ auth.token }}"
  register: bgp_probe

- name: Create a Device Traffic probe
  juniper.apstra.iba_probes:
    type: predefined
    id:
      blueprint: "my-blueprint"
    body:
      predefined_probe: traffic
      label: "Device Traffic"
    auth_token: "{{ auth.token }}"

- name: Create a Device System Health probe
  juniper.apstra.iba_probes:
    type: predefined
    id:
      blueprint: "my-blueprint"
    body:
      predefined_probe: device_health
      label: "Device System Health"
      raise_switch_anomaly: true
      raise_server_anomaly: true
      history_duration: 2592000
    auth_token: "{{ auth.token }}"

- name: Create an ECMP Imbalance probe (fabric)
  juniper.apstra.iba_probes:
    type: predefined
    id:
      blueprint: "my-blueprint"
    body:
      predefined_probe: fabric_ecmp_imbalance
      label: "ECMP Imbalance (Fabric Interfaces)"
    auth_token: "{{ auth.token }}"

- name: Create a LAG Imbalance probe
  juniper.apstra.iba_probes:
    type: predefined
    id:
      blueprint: "my-blueprint"
    body:
      predefined_probe: lag_imbalance
      label: "LAG Imbalance"
    auth_token: "{{ auth.token }}"

- name: Create a Control Plane Policing probe
  juniper.apstra.iba_probes:
    type: predefined
    id:
      blueprint: "my-blueprint"
    body:
      predefined_probe: copp
      label: "Control Plane Policing"
      aggregation_period: 300
      collection_interval: 120
      history_duration: 2592000
      drop_count_threshold: 1
    auth_token: "{{ auth.token }}"

- name: Create a Device Telemetry Health probe
  juniper.apstra.iba_probes:
    type: predefined
    id:
      blueprint: "my-blueprint"
    body:
      predefined_probe: device_telemetry_health
      label: "Device Telemetry Health"
    auth_token: "{{ auth.token }}"

- name: Create an ESI Imbalance probe
  juniper.apstra.iba_probes:
    type: predefined
    id:
      blueprint: "my-blueprint"
    body:
      predefined_probe: esi_imbalance
      label: "ESI Imbalance"
    auth_token: "{{ auth.token }}"

- name: Create a MAC Monitor probe
  juniper.apstra.iba_probes:
    type: predefined
    id:
      blueprint: "my-blueprint"
    body:
      predefined_probe: mac_monitor
      label: "MAC Monitor"
    auth_token: "{{ auth.token }}"

- name: Create a Bandwidth Utilization probe
  juniper.apstra.iba_probes:
    type: predefined
    id:
      blueprint: "my-blueprint"
    body:
      predefined_probe: bandwidth_utilization
      label: "Bandwidth Utilization"
      first_summary_average_period: 120
      first_summary_total_duration: 3600
      second_summary_average_period: 3600
      second_summary_total_duration: 2592000
    auth_token: "{{ auth.token }}"

- name: Create a Spine Fault Tolerance probe
  juniper.apstra.iba_probes:
    type: predefined
    id:
      blueprint: "my-blueprint"
    body:
      predefined_probe: spine_fault_tolerance
      label: "Spine Fault Tolerance"
    auth_token: "{{ auth.token }}"

- name: Create an Optical Transceivers probe
  juniper.apstra.iba_probes:
    type: predefined
    id:
      blueprint: "my-blueprint"
    body:
      predefined_probe: optical_transceivers
      label: "Optical Transceivers"
    auth_token: "{{ auth.token }}"

- name: Create an Interface Flapping probe (fabric)
  juniper.apstra.iba_probes:
    type: predefined
    id:
      blueprint: "my-blueprint"
    body:
      predefined_probe: fabric_interface_flapping
      label: "Interface Flapping (Fabric)"
    auth_token: "{{ auth.token }}"

- name: Create an EVPN Host Flapping probe
  juniper.apstra.iba_probes:
    type: predefined
    id:
      blueprint: "my-blueprint"
    body:
      predefined_probe: evpn_host_flapping
      label: "EVPN Host Flapping"
    auth_token: "{{ auth.token }}"

- name: Create a Packet Discard Percentage probe
  juniper.apstra.iba_probes:
    type: predefined
    id:
      blueprint: "my-blueprint"
    body:
      predefined_probe: packet_discard_percentage
      label: "Packet Discard Percentage"
    auth_token: "{{ auth.token }}"

- name: Create an East-West Traffic probe
  juniper.apstra.iba_probes:
    type: predefined
    id:
      blueprint: "my-blueprint"
    body:
      predefined_probe: eastwest_traffic
      label: "East-West Traffic"
    auth_token: "{{ auth.token }}"

- name: Create an External Routes probe
  juniper.apstra.iba_probes:
    type: predefined
    id:
      blueprint: "my-blueprint"
    body:
      predefined_probe: external_routes
      label: "External Routes"
    auth_token: "{{ auth.token }}"

# ── Update / Delete Probes ──────────────────────────────────────────

- name: Update a probe's label (by current label lookup)
  juniper.apstra.iba_probes:
    type: probe
    id:
      blueprint: "my-blueprint"
    body:
      label: "BGP Monitoring"
      description: "Updated BGP probe description"
    state: present
    auth_token: "{{ auth.token }}"

- name: Delete a probe by ID
  juniper.apstra.iba_probes:
    type: probe
    id:
      blueprint: "my-blueprint"
      probe: "{{ bgp_probe.id.probe }}"
    state: absent
    auth_token: "{{ auth.token }}"

- name: Delete a probe by label (via id.probe)
  juniper.apstra.iba_probes:
    type: probe
    id:
      blueprint: "my-blueprint"
      probe: "BGP Monitoring"
    state: absent
    auth_token: "{{ auth.token }}"

- name: Read a probe by label (via id.probe)
  juniper.apstra.iba_probes:
    type: probe
    id:
      blueprint: "my-blueprint"
      probe: "BGP Monitoring"
    state: present
    auth_token: "{{ auth.token }}"

- name: Delete a probe by label (via body.label fallback)
  juniper.apstra.iba_probes:
    type: probe
    id:
      blueprint: "my-blueprint"
    body:
      label: "BGP Monitoring"
    state: absent
    auth_token: "{{ auth.token }}"

# ── IBA Dashboards ──────────────────────────────────────────────────

- name: Create an IBA dashboard
  juniper.apstra.iba_probes:
    type: dashboard
    id:
      blueprint: "my-blueprint"
    body:
      label: "Fabric Health Dashboard"
      description: "Overview of fabric health probes"
    state: present
    auth_token: "{{ auth.token }}"
  register: dash

- name: Delete an IBA dashboard by ID
  juniper.apstra.iba_probes:
    type: dashboard
    id:
      blueprint: "my-blueprint"
      dashboard: "{{ dash.id.dashboard }}"
    state: absent
    auth_token: "{{ auth.token }}"

- name: Delete an IBA dashboard by label
  juniper.apstra.iba_probes:
    type: dashboard
    id:
      blueprint: "my-blueprint"
      dashboard: "Fabric Health Dashboard"
    state: absent
    auth_token: "{{ auth.token }}"

- name: Read an IBA dashboard by label
  juniper.apstra.iba_probes:
    type: dashboard
    id:
      blueprint: "my-blueprint"
      dashboard: "Fabric Health Dashboard"
    state: present
    auth_token: "{{ auth.token }}"
"""

RETURN = """
changed:
  description: Indicates whether the module has made any changes.
  type: bool
  returned: always
id:
  description: Dictionary of resource identifiers.
  returned: on create or when found by label
  type: dict
  sample: {
      "blueprint": "54bd9839-275e-4444-8ef2-5093f49e08b7",
      "probe": "99a47423-c172-4006-b55a-da37102f73e4"
  }
probe:
  description: The full probe object details.
  returned: when type is predefined or probe with state present
  type: dict
dashboard:
  description: The full dashboard object details.
  returned: when type is dashboard with state present
  type: dict
changes:
  description: Dictionary of updates that were applied.
  type: dict
  returned: on update
msg:
  description: The output message that the module generates.
  type: str
  returned: always
predefined_probes:
  description: List of available predefined probe names (when listing).
  type: list
  returned: when state is present and type is predefined with no body
"""

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.client import (
    apstra_client_module_args,
    ApstraClientFactory,
)
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.iba_probes import (
    get_probe,
    create_probe,
    create_predefined_probe,
    update_probe,
    delete_probe,
    find_probe_by_label,
    list_predefined_probes,
    get_predefined_probe,
    get_dashboard,
    create_dashboard,
    update_dashboard,
    delete_dashboard,
    find_dashboard_by_label,
)
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.name_resolution import (
    resolve_probe_id,
    resolve_dashboard_id,
)


# Read-only fields returned by the API but not part of the create/update body
PROBE_READ_ONLY_FIELDS = (
    "id",
    "stages",
    "state",
    "probe_state",
    "last_error",
    "config_started_at",
    "config_completed_at",
    "anomaly_count",
    "version",
    "iba_unit",
    "host_node",
    "task_state",
    "task_error",
    "predefined_probe",
    "referencing_dashboards",
    "updated_at",
    "created_by",
    "updated_by",
)

DASHBOARD_READ_ONLY_FIELDS = (
    "id",
    "created_at",
    "updated_at",
    "created_by",
    "updated_by",
    "default",
    "predefined_dashboard",
    "predefined_parameters",
)


def _manage_predefined_probe(module, client_factory):
    """Manage a predefined (built-in) probe."""
    result = dict(changed=False)

    id_param = module.params.get("id")
    if id_param is None:
        id_param = {}
    body = module.params.get("body", None)
    state = module.params["state"]

    blueprint_id = id_param.get("blueprint")
    if not blueprint_id:
        raise ValueError("Must specify 'blueprint' in id")
    blueprint_id = client_factory.resolve_blueprint_id(blueprint_id)
    id_param["blueprint"] = blueprint_id

    if state == "present":
        if body is None:
            # List available predefined probes
            predefined = list_predefined_probes(client_factory, blueprint_id)
            result["predefined_probes"] = [p.get("name") for p in predefined]
            result["msg"] = f"Found {len(predefined)} predefined probes"
            return result

        predefined_probe_name = body.get("predefined_probe")
        if not predefined_probe_name:
            raise ValueError(
                "Must specify 'predefined_probe' in body for predefined type "
                "(e.g. bgp_session, traffic, device_health)"
            )

        label = body.get("label")

        # Check if a probe with this label already exists
        if label:
            existing = find_probe_by_label(client_factory, blueprint_id, label)
            if existing:
                probe_id = existing["id"]
                id_param["probe"] = probe_id
                result["id"] = id_param
                result["changed"] = False
                result["probe"] = existing
                result["msg"] = f"Probe '{label}' already exists"
                return result

        # Build the params for instantiation (everything except predefined_probe)
        params = {k: v for k, v in body.items() if k != "predefined_probe"}

        # Validate the predefined probe exists
        predef = get_predefined_probe(
            client_factory, blueprint_id, predefined_probe_name
        )
        if predef is None:
            available = list_predefined_probes(client_factory, blueprint_id)
            available_names = [p.get("name") for p in available]
            raise ValueError(
                f"Predefined probe '{predefined_probe_name}' not found. "
                f"Available: {available_names}"
            )

        created = create_predefined_probe(
            client_factory, blueprint_id, predefined_probe_name, params
        )
        probe_id = created.get("id")
        if not probe_id:
            raise ValueError(
                f"Unexpected response from predefined probe creation: {created}"
            )

        id_param["probe"] = probe_id
        result["id"] = id_param
        result["changed"] = True
        result["msg"] = (
            f"Predefined probe '{predefined_probe_name}' instantiated successfully"
        )

        # Fetch the full probe
        import time

        for _attempt in range(10):
            probe = get_probe(client_factory, blueprint_id, probe_id)
            if probe is not None:
                break
            time.sleep(2)
        result["probe"] = probe

    elif state == "absent":
        probe_id = id_param.get("probe")
        label = body.get("label") if body else None

        # Resolve probe ref (UUID or label) via name_resolution
        if probe_id:
            probe_id = resolve_probe_id(client_factory, blueprint_id, probe_id)
            id_param["probe"] = probe_id
        elif label:
            existing = find_probe_by_label(client_factory, blueprint_id, label)
            if existing:
                probe_id = existing["id"]
                id_param["probe"] = probe_id

        if not probe_id:
            result["changed"] = False
            result["msg"] = "Probe not found, nothing to delete"
            return result

        delete_probe(client_factory, blueprint_id, probe_id)
        result["changed"] = True
        result["msg"] = "Probe deleted successfully"

    return result


def _manage_custom_probe(module, client_factory):
    """Manage a custom (raw) probe."""
    result = dict(changed=False)

    id_param = module.params.get("id")
    if id_param is None:
        id_param = {}
    body = module.params.get("body", None)
    state = module.params["state"]

    blueprint_id = id_param.get("blueprint")
    if not blueprint_id:
        raise ValueError("Must specify 'blueprint' in id")
    blueprint_id = client_factory.resolve_blueprint_id(blueprint_id)
    id_param["blueprint"] = blueprint_id

    probe_id = id_param.get("probe")

    # Resolve probe ref (UUID or label) via name_resolution
    if probe_id:
        probe_id = resolve_probe_id(client_factory, blueprint_id, probe_id)
        id_param["probe"] = probe_id

    # Try to find by label if no probe ID given
    current_object = None
    if probe_id is None:
        label = body.get("label") if body else None
        if label:
            found = find_probe_by_label(client_factory, blueprint_id, label)
            if found:
                probe_id = found["id"]
                id_param["probe"] = probe_id
                current_object = found
    else:
        current_object = get_probe(client_factory, blueprint_id, probe_id)

    if state == "present":
        if current_object:
            result["id"] = id_param
            if body:
                # Compare updatable fields
                compare_current = {
                    k: v
                    for k, v in current_object.items()
                    if k not in PROBE_READ_ONLY_FIELDS
                }
                changes = {}
                if client_factory.compare_and_update(compare_current, body, changes):
                    update_probe(
                        client_factory, blueprint_id, probe_id, compare_current
                    )
                    result["changed"] = True
                    result["changes"] = changes
                    result["msg"] = "Probe updated successfully"
                else:
                    result["changed"] = False
                    result["msg"] = "No changes needed for probe"
            else:
                result["changed"] = False
                result["msg"] = "No changes specified for probe"

            # Return final state
            if result["changed"]:
                import time

                for _attempt in range(10):
                    probe = get_probe(client_factory, blueprint_id, probe_id)
                    if probe is not None:
                        break
                    time.sleep(2)
                result["probe"] = probe
            else:
                result["probe"] = current_object
        else:
            # Create custom probe
            if body is None:
                raise ValueError("Must specify 'body' to create a probe")
            created = create_probe(client_factory, blueprint_id, body)
            probe_id = created.get("id")
            if not probe_id:
                raise ValueError(f"Unexpected response creating probe: {created}")
            id_param["probe"] = probe_id
            result["id"] = id_param
            result["changed"] = True
            result["msg"] = "Probe created successfully"

            import time

            for _attempt in range(10):
                probe = get_probe(client_factory, blueprint_id, probe_id)
                if probe is not None:
                    break
                time.sleep(2)
            result["probe"] = probe

    elif state == "absent":
        if current_object is None:
            result["changed"] = False
            result["msg"] = "Probe does not exist"
        else:
            if not probe_id:
                raise ValueError("Cannot delete a probe without a probe id")
            delete_probe(client_factory, blueprint_id, probe_id)
            result["changed"] = True
            result["msg"] = "Probe deleted successfully"

    return result


def _manage_dashboard(module, client_factory):
    """Manage an IBA dashboard."""
    result = dict(changed=False)

    id_param = module.params.get("id")
    if id_param is None:
        id_param = {}
    body = module.params.get("body", None)
    state = module.params["state"]

    blueprint_id = id_param.get("blueprint")
    if not blueprint_id:
        raise ValueError("Must specify 'blueprint' in id")
    blueprint_id = client_factory.resolve_blueprint_id(blueprint_id)
    id_param["blueprint"] = blueprint_id

    dashboard_id = id_param.get("dashboard")

    # Resolve dashboard ref (UUID or label) via name_resolution
    if dashboard_id:
        dashboard_id = resolve_dashboard_id(client_factory, blueprint_id, dashboard_id)
        id_param["dashboard"] = dashboard_id

    # Try to find by label if no dashboard ID given
    current_object = None
    if dashboard_id is None:
        label = body.get("label") if body else None
        if label:
            found = find_dashboard_by_label(client_factory, blueprint_id, label)
            if found:
                dashboard_id = found["id"]
                id_param["dashboard"] = dashboard_id
                current_object = found
    else:
        current_object = get_dashboard(client_factory, blueprint_id, dashboard_id)

    if state == "present":
        if current_object:
            result["id"] = id_param
            if body:
                compare_current = {
                    k: v
                    for k, v in current_object.items()
                    if k not in DASHBOARD_READ_ONLY_FIELDS
                }
                changes = {}
                if client_factory.compare_and_update(compare_current, body, changes):
                    update_dashboard(
                        client_factory, blueprint_id, dashboard_id, compare_current
                    )
                    result["changed"] = True
                    result["changes"] = changes
                    result["msg"] = "Dashboard updated successfully"
                else:
                    result["changed"] = False
                    result["msg"] = "No changes needed for dashboard"
            else:
                result["changed"] = False
                result["msg"] = "No changes specified for dashboard"

            result["dashboard"] = current_object

        else:
            if body is None:
                raise ValueError("Must specify 'body' to create a dashboard")
            # The API requires 'grid' with at least one row; default to one empty row
            if "grid" not in body:
                body["grid"] = [[]]
            created = create_dashboard(client_factory, blueprint_id, body)
            dashboard_id = created.get("id")
            if not dashboard_id:
                raise ValueError(f"Unexpected response creating dashboard: {created}")
            id_param["dashboard"] = dashboard_id
            result["id"] = id_param
            result["changed"] = True
            result["msg"] = "Dashboard created successfully"

            import time

            for _attempt in range(10):
                dash = get_dashboard(client_factory, blueprint_id, dashboard_id)
                if dash is not None:
                    break
                time.sleep(2)
            result["dashboard"] = dash

    elif state == "absent":
        if current_object is None:
            result["changed"] = False
            result["msg"] = "Dashboard does not exist"
        else:
            if not dashboard_id:
                raise ValueError("Cannot delete a dashboard without a dashboard id")
            delete_dashboard(client_factory, blueprint_id, dashboard_id)
            result["changed"] = True
            result["msg"] = "Dashboard deleted successfully"

    return result


def main():
    object_module_args = dict(
        type=dict(
            type="str",
            required=False,
            choices=["predefined", "probe", "dashboard"],
            default="predefined",
        ),
        id=dict(type="dict", required=False, default=None),
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

        resource_type = module.params["type"]

        if resource_type == "predefined":
            result = _manage_predefined_probe(module, client_factory)
        elif resource_type == "probe":
            result = _manage_custom_probe(module, client_factory)
        elif resource_type == "dashboard":
            result = _manage_dashboard(module, client_factory)
        else:
            raise ValueError(f"Unsupported type: {resource_type}")

    except Exception as e:
        tb = traceback.format_exc()
        module.debug(f"Exception occurred: {str(e)}\n\nStack trace:\n{tb}")
        result.pop("msg", None)
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
