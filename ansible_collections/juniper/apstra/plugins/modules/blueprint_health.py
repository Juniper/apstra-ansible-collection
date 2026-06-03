#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# Apache License, Version 2.0 (see https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: blueprint_health
short_description: Collect anomalies and build errors from an Apstra blueprint
version_added: "1.0.9"
author:
  - "Prabhanjan KV (@kvp_jnpr)"
description:
  - This module collects anomalies and build errors/warnings from an Apstra
    blueprint as structured data for monitoring, alerting, and reporting.
  - Anomalies are retrieved via C(GET /api/blueprints/{id}/anomalies).
  - Build errors are retrieved via C(GET /api/blueprints/{id}/errors).
  - Results can be filtered by scope, severity, anomaly type, and node.
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
  id:
    description:
      - Dictionary containing the blueprint identifier.
      - Must include a C(blueprint) key with the blueprint ID or label.
    required: true
    type: dict
  scope:
    description:
      - The type of health data to collect.
      - C(anomalies) collects blueprint anomalies only.
      - C(errors) collects build errors and warnings only.
      - C(all) collects both anomalies and build errors.
    required: false
    type: str
    choices: ["anomalies", "errors", "all"]
    default: "all"
  severity:
    description:
      - Filter results by severity level.
      - Only applies to anomalies.
    required: false
    type: str
    choices: ["critical", "warning", "info"]
  node_filter:
    description:
      - Filter anomalies by system/node name or ID.
    required: false
    type: str
  anomaly_type:
    description:
      - Filter anomalies by anomaly type (e.g. C(cabling), C(config),
        C(interface), C(bgp), C(route), C(arp), C(mac), C(series),
        C(streaming), C(hostname), C(liveness), C(deployment)).
    required: false
    type: str
"""

EXAMPLES = """
- name: Collect all health data from a blueprint
  juniper.apstra.blueprint_health:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
  register: health

- name: Collect anomalies only
  juniper.apstra.blueprint_health:
    id:
      blueprint: "my-blueprint-label"
    scope: anomalies
  register: anomalies

- name: Collect only critical anomalies
  juniper.apstra.blueprint_health:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    scope: anomalies
    severity: critical
  register: critical_anomalies

- name: Collect anomalies for a specific node
  juniper.apstra.blueprint_health:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    scope: anomalies
    node_filter: "leaf1"
  register: node_anomalies

- name: Collect build errors only
  juniper.apstra.blueprint_health:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    scope: errors
  register: build_errors

- name: Filter anomalies by type
  juniper.apstra.blueprint_health:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    scope: anomalies
    anomaly_type: "cabling"
  register: cabling_anomalies

- name: Filter anomalies by type for a specific node
  juniper.apstra.blueprint_health:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    scope: anomalies
    node_filter: "leaf1"
    anomaly_type: "cabling"
  register: leaf1_cabling_anomalies
"""

RETURN = """
changed:
  description: Always false since this is a read-only module.
  type: bool
  returned: always
  sample: false
anomalies:
  description: Anomaly data from the blueprint.
  type: dict
  returned: when scope is 'anomalies' or 'all'
  sample:
    count: 5
    items:
      - type: "cabling"
        severity: "error"
        node: "leaf1"
        message: "Interface mismatch detected"
errors:
  description: Build errors and warnings from the blueprint.
  type: dict
  returned: when scope is 'errors' or 'all'
  sample:
    errors_count: 2
    warnings_count: 1
msg:
  description: The output message that the module generates.
  type: str
  returned: always
"""

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.client import (
    apstra_client_module_args,
    ApstraClientFactory,
)
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.bp_dci import (
    get_blueprint_errors,
)


def _get_anomalies(client_factory, blueprint_id):
    """Retrieve anomalies for a blueprint via raw API call.

    Calls GET /api/blueprints/{bp_id}/anomalies.

    Args:
        client_factory: An ApstraClientFactory instance.
        blueprint_id: The blueprint UUID.

    Returns:
        dict: The anomalies payload with 'items' list and 'count'.
    """
    base = client_factory.get_base_client()
    resp = base.raw_request(f"/blueprints/{blueprint_id}/anomalies")
    if resp.status_code == 200:
        return resp.json()
    return {"items": [], "count": 0}


def _filter_anomalies(
    anomalies_data, severity=None, node_filter=None, anomaly_type=None
):
    """Filter anomalies by severity, node, and/or type.

    Args:
        anomalies_data: Raw anomalies response dict.
        severity: Optional severity filter.
        node_filter: Optional node name/ID filter.
        anomaly_type: Optional anomaly type filter.

    Returns:
        dict: Filtered anomalies with updated count.
    """
    items = anomalies_data.get("items", [])

    if severity:
        items = [a for a in items if a.get("severity", "").lower() == severity.lower()]

    if node_filter:
        node_lower = node_filter.lower()

        def _node_matches(anomaly):
            identity = anomaly.get("identity") or {}
            node_candidates = [
                identity.get("system_id", ""),
                identity.get("hostname", ""),
                identity.get("label", ""),
                anomaly.get("node", ""),
                anomaly.get("node_id", ""),
                anomaly.get("node_label", ""),
                anomaly.get("role", ""),
            ]

            return any(
                node_lower in str(value).lower() for value in node_candidates
            ) or (
                node_lower in str(anomaly.get("expected", "")).lower()
                or node_lower in str(anomaly.get("actual", "")).lower()
            )

        items = [a for a in items if _node_matches(a)]

    if anomaly_type:
        type_lower = anomaly_type.lower()

        def _type_matches(anomaly):
            type_candidates = [
                anomaly.get("anomaly_type", ""),
                anomaly.get("type", ""),
                anomaly.get("anomaly_kind", ""),
                anomaly.get("kind", ""),
                anomaly.get("category", ""),
            ]
            anomaly_types = anomaly.get("anomaly_types", [])

            return any(
                type_lower in str(value).lower() for value in type_candidates
            ) or any(type_lower in str(value).lower() for value in anomaly_types)

        items = [a for a in items if _type_matches(a)]

    return {
        "count": len(items),
        "items": items,
    }


def main():
    object_module_args = dict(
        id=dict(type="dict", required=True),
        scope=dict(
            type="str",
            required=False,
            choices=["anomalies", "errors", "all"],
            default="all",
        ),
        severity=dict(
            type="str",
            required=False,
            choices=["critical", "warning", "info"],
        ),
        node_filter=dict(type="str", required=False),
        anomaly_type=dict(type="str", required=False),
    )
    client_module_args = apstra_client_module_args()
    module_args = client_module_args | object_module_args

    result = dict(changed=False)

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    try:
        client_factory = ApstraClientFactory.from_params(module)

        id_param = module.params["id"]
        scope = module.params["scope"]
        severity = module.params.get("severity")
        node_filter = module.params.get("node_filter")
        anomaly_type = module.params.get("anomaly_type")

        if "blueprint" not in id_param:
            raise ValueError("The 'id' parameter must include a 'blueprint' key.")

        blueprint_id = client_factory.resolve_blueprint_id(id_param["blueprint"])

        # Collect anomalies
        if scope in ("anomalies", "all"):
            raw_anomalies = _get_anomalies(client_factory, blueprint_id)
            result["anomalies"] = _filter_anomalies(
                raw_anomalies,
                severity=severity,
                node_filter=node_filter,
                anomaly_type=anomaly_type,
            )

        # Collect build errors
        if scope in ("errors", "all"):
            result["errors"] = get_blueprint_errors(client_factory, blueprint_id)

        # Build summary message
        parts = []
        if "anomalies" in result:
            parts.append(f"{result['anomalies']['count']} anomalies")
        if "errors" in result:
            ec = result["errors"].get("errors_count", 0)
            wc = result["errors"].get("warnings_count", 0)
            parts.append(f"{ec} errors, {wc} warnings")
        result["msg"] = f"Blueprint health: {'; '.join(parts)}"

    except Exception as e:
        tb = traceback.format_exc()
        module.debug(f"Exception occurred: {str(e)}\n\nStack trace:\n{tb}")
        result.pop("msg", None)
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
