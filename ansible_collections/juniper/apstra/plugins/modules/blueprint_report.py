#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# Apache License, Version 2.0 (see https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: blueprint_report

short_description: Generate reports from Apstra blueprint data

version_added: "1.0.9"

author:
  - "Juniper Networks"

description:
  - This module generates reports from Apstra blueprint data by aggregating
    information from multiple sources including anomalies, build errors,
    IBA probes, device inventory, and configuration drift.
  - Supports different report types — health, inventory, compliance, and full.
  - Reports are returned as structured data and can optionally be saved to file.

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
      - Must include C(blueprint) key with a blueprint UUID or label.
    required: true
    type: dict
  report_type:
    description:
      - The type of report to generate.
      - C(health) — anomalies, build errors, and IBA probe status.
      - C(inventory) — device nodes and system information.
      - C(compliance) — configuration drift and anomaly details.
      - C(full) — all of the above combined.
    required: false
    type: str
    choices: ["health", "inventory", "compliance", "full"]
    default: "full"
  output_file:
    description:
      - Optional file path to save the report.
      - Parent directories must already exist.
    required: false
    type: str
  output_format:
    description:
      - Format for the output file.
      - Only used when C(output_file) is specified.
    required: false
    type: str
    choices: ["json", "csv"]
    default: "json"
"""

EXAMPLES = """
# Generate a full report for a blueprint
- name: Generate full blueprint report
  juniper.apstra.blueprint_report:
    id:
      blueprint: "my-blueprint"
    report_type: full
  register: report

- name: Display report summary
  ansible.builtin.debug:
    var: report.report.summary

# Generate a health report and save to file
- name: Generate health report
  juniper.apstra.blueprint_report:
    id:
      blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
    report_type: health
    output_file: "/tmp/health_report.json"
    output_format: json
    auth_token: "{{ auth.token }}"

# Generate an inventory report
- name: Generate inventory report
  juniper.apstra.blueprint_report:
    id:
      blueprint: "my-blueprint"
    report_type: inventory
    auth_token: "{{ auth.token }}"
  register: inventory

- name: Show device count
  ansible.builtin.debug:
    msg: "Found {{ inventory.report.inventory.nodes | length }} nodes"

# Generate a compliance report and export as CSV
- name: Generate compliance report
  juniper.apstra.blueprint_report:
    id:
      blueprint: "my-blueprint"
    report_type: compliance
    output_file: "/tmp/compliance_report.csv"
    output_format: csv
    auth_token: "{{ auth.token }}"
"""

RETURN = """
changed:
  description: Always false — this module is read-only.
  type: bool
  returned: always
  sample: false
report:
  description: The generated report data.
  type: dict
  returned: always
  contains:
    blueprint_id:
      description: The blueprint UUID.
      type: str
    blueprint_label:
      description: The blueprint label/name.
      type: str
    report_type:
      description: The type of report generated.
      type: str
    generated_at:
      description: ISO 8601 timestamp of report generation.
      type: str
    summary:
      description: High-level summary counts.
      type: dict
    health:
      description: Health data (anomalies, errors, IBA). Present for health and full reports.
      type: dict
    inventory:
      description: Inventory data (nodes). Present for inventory and full reports.
      type: dict
    compliance:
      description: Compliance data (config drift, anomaly details). Present for compliance and full reports.
      type: dict
output_file:
  description: Path to the saved report file, if output_file was specified.
  type: str
  returned: when output_file is specified
msg:
  description: The output message that the module generates.
  type: str
  returned: always
"""

import csv
import io
import json
import os
import traceback
from datetime import datetime, timezone

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.juniper.apstra.plugins.module_utils.apstra.client import (
    apstra_client_module_args,
    ApstraClientFactory,
)


def _safe_api_get(base_client, path):
    """Make a GET request and return parsed JSON, or an empty dict on error."""
    try:
        resp = base_client.raw_request(path)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return {}


def _collect_health(base_client, blueprint_id):
    """Collect health-related data: anomalies, errors, IBA dashboards."""
    anomalies_data = _safe_api_get(base_client, f"/blueprints/{blueprint_id}/anomalies")
    errors_data = _safe_api_get(base_client, f"/blueprints/{blueprint_id}/errors")
    iba_data = _safe_api_get(base_client, f"/blueprints/{blueprint_id}/iba/dashboards")

    # Normalise anomalies
    anomaly_items = anomalies_data.get("items", [])
    if isinstance(anomalies_data, list):
        anomaly_items = anomalies_data

    # Normalise errors
    error_items = errors_data.get("items", [])
    if isinstance(errors_data, list):
        error_items = errors_data

    # Normalise IBA dashboards
    iba_items = iba_data.get("items", [])
    if isinstance(iba_data, list):
        iba_items = iba_data

    return {
        "anomalies": {
            "count": len(anomaly_items),
            "items": anomaly_items,
        },
        "errors": {
            "count": len(error_items),
            "items": error_items,
        },
        "iba_dashboards": {
            "count": len(iba_items),
            "items": iba_items,
        },
    }


def _collect_inventory(base_client, blueprint_id):
    """Collect inventory data: nodes."""
    nodes_data = _safe_api_get(
        base_client, f"/blueprints/{blueprint_id}/nodes?node_type=system"
    )

    node_items = nodes_data.get("nodes", {})
    if isinstance(node_items, dict):
        node_list = list(node_items.values())
    elif isinstance(node_items, list):
        node_list = node_items
    else:
        node_list = []

    return {
        "nodes": node_list,
        "node_count": len(node_list),
    }


def _collect_compliance(base_client, blueprint_id):
    """Collect compliance data: config drift and anomaly details."""
    diff_data = _safe_api_get(base_client, f"/blueprints/{blueprint_id}/diff")
    anomalies_data = _safe_api_get(base_client, f"/blueprints/{blueprint_id}/anomalies")

    anomaly_items = anomalies_data.get("items", [])
    if isinstance(anomalies_data, list):
        anomaly_items = anomalies_data

    return {
        "config_drift": diff_data if diff_data else {"status": "no_drift_detected"},
        "anomalies": {
            "count": len(anomaly_items),
            "items": anomaly_items,
        },
    }


def _build_summary(report_data):
    """Build a high-level summary from collected report sections."""
    summary = {}

    if "health" in report_data:
        health = report_data["health"]
        summary["anomaly_count"] = health["anomalies"]["count"]
        summary["error_count"] = health["errors"]["count"]
        summary["iba_dashboard_count"] = health["iba_dashboards"]["count"]

    if "inventory" in report_data:
        summary["node_count"] = report_data["inventory"]["node_count"]

    if "compliance" in report_data:
        compliance = report_data["compliance"]
        summary["compliance_anomaly_count"] = compliance["anomalies"]["count"]
        has_drift = compliance["config_drift"].get("status") != "no_drift_detected"
        summary["config_drift_detected"] = has_drift

    return summary


def _flatten_for_csv(report_data):
    """Flatten report data into a list of rows suitable for CSV export."""
    rows = []

    if "health" in report_data:
        health = report_data["health"]
        for anomaly in health["anomalies"]["items"]:
            row = {"section": "anomaly"}
            row.update(
                {
                    k: json.dumps(v) if isinstance(v, (dict, list)) else v
                    for k, v in anomaly.items()
                }
            )
            rows.append(row)
        for error in health["errors"]["items"]:
            row = {"section": "error"}
            row.update(
                {
                    k: json.dumps(v) if isinstance(v, (dict, list)) else v
                    for k, v in error.items()
                }
            )
            rows.append(row)

    if "inventory" in report_data:
        for node in report_data["inventory"]["nodes"]:
            row = {"section": "node"}
            row.update(
                {
                    k: json.dumps(v) if isinstance(v, (dict, list)) else v
                    for k, v in node.items()
                }
            )
            rows.append(row)

    if "compliance" in report_data:
        compliance = report_data["compliance"]
        for anomaly in compliance["anomalies"]["items"]:
            row = {"section": "compliance_anomaly"}
            row.update(
                {
                    k: json.dumps(v) if isinstance(v, (dict, list)) else v
                    for k, v in anomaly.items()
                }
            )
            rows.append(row)

    return rows


def _save_report(report, output_file, output_format):
    """Save the report to a file in the requested format."""
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.isdir(output_dir):
        raise ValueError(f"Output directory does not exist: {output_dir}")

    if output_format == "json":
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)
    elif output_format == "csv":
        rows = _flatten_for_csv(report)
        if not rows:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("")
            return
        # Gather all unique field names across rows
        fieldnames = []
        seen = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    fieldnames.append(key)
                    seen.add(key)
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(buf.getvalue())


def main():
    object_module_args = dict(
        id=dict(type="dict", required=True),
        report_type=dict(
            type="str",
            required=False,
            choices=["health", "inventory", "compliance", "full"],
            default="full",
        ),
        output_file=dict(type="str", required=False, default=None),
        output_format=dict(
            type="str",
            required=False,
            choices=["json", "csv"],
            default="json",
        ),
    )
    client_module_args = apstra_client_module_args()
    module_args = client_module_args | object_module_args

    # This module never makes changes — it is read-only
    result = dict(changed=False)

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    try:
        client_factory = ApstraClientFactory.from_params(module)
        base_client = client_factory.get_base_client()

        id_param = module.params["id"]
        report_type = module.params["report_type"]
        output_file = module.params.get("output_file")
        output_format = module.params.get("output_format", "json")

        # Resolve blueprint
        blueprint_ref = id_param.get("blueprint")
        if not blueprint_ref:
            raise ValueError("'id.blueprint' is required")
        blueprint_id = client_factory.resolve_blueprint_id(blueprint_ref)

        # Fetch blueprint label
        bp_info = _safe_api_get(base_client, f"/blueprints/{blueprint_id}")
        blueprint_label = bp_info.get("label", blueprint_ref)

        # Build report
        report = {
            "blueprint_id": blueprint_id,
            "blueprint_label": blueprint_label,
            "report_type": report_type,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        if report_type in ("health", "full"):
            report["health"] = _collect_health(base_client, blueprint_id)

        if report_type in ("inventory", "full"):
            report["inventory"] = _collect_inventory(base_client, blueprint_id)

        if report_type in ("compliance", "full"):
            report["compliance"] = _collect_compliance(base_client, blueprint_id)

        report["summary"] = _build_summary(report)

        result["report"] = report
        result["msg"] = f"{report_type} report generated successfully"

        # Optionally save to file
        if output_file:
            _save_report(report, output_file, output_format)
            result["output_file"] = output_file
            result["msg"] += f" and saved to {output_file}"

    except Exception as e:
        tb = traceback.format_exc()
        module.debug(f"Exception occurred: {str(e)}\n\nStack trace:\n{tb}")
        result.pop("msg", None)
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
