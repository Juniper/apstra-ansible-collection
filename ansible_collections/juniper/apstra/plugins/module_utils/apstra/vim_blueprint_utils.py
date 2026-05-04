# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

"""
Direct-API utilities for blueprint-level virtual_infra sub-resources that
are not exposed by the Apstra SDK.

All functions follow the same raw_request pattern used in vim_vcenter.py:
  base = client_factory.get_base_client()
  resp = base.raw_request(url, method, data=...)

Covered endpoints:
  POST /blueprints/{id}/virtual_infra/predefined_probes/
           virtual_infra_vlan_match/anomaly_resolver
  POST /blueprints/{id}/virtual_infra/query/vm
  GET  /blueprints/{id}/virtual_infra/vnet/{vnet_id}
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

_BASE = "/blueprints"


def resolve_blueprint_virtual_infra_anomalies(client_factory, blueprint_id, body):
    """POST .../virtual_infra/predefined_probes/virtual_infra_vlan_match/anomaly_resolver

    Triggers Apstra's built-in resolver to auto-remediate virtual-infra
    VLAN-match anomalies in the blueprint.

    :param client_factory: ApstraClientFactory instance
    :param blueprint_id:   Blueprint UUID
    :param body:           Request body dict (e.g. {"anomaly_ids": []} to
                           resolve all, or specific IDs to target)
    :returns:              Parsed JSON response dict (may be empty for 204)
    :raises Exception:     On non-2xx HTTP status
    """
    base = client_factory.get_base_client()
    url = (
        f"{_BASE}/{blueprint_id}/virtual_infra"
        "/predefined_probes/virtual_infra_vlan_match/anomaly_resolver"
    )
    resp = base.raw_request(url, "POST", data=body or {})
    if resp.status_code not in (200, 201, 202, 204):
        raise Exception(
            f"anomaly_resolver POST failed [{resp.status_code}]: {resp.text}"
        )
    try:
        return resp.json()
    except Exception:
        return {}


def query_blueprint_vms(client_factory, blueprint_id, body):
    """POST .../virtual_infra/query/vm

    Queries the VM inventory visible to Apstra through the blueprint's
    virtual-infra layer.

    :param client_factory: ApstraClientFactory instance
    :param blueprint_id:   Blueprint UUID
    :param body:           Query/filter parameters dict
    :returns:              List of VM dicts
    :raises Exception:     On non-2xx HTTP status
    """
    base = client_factory.get_base_client()
    url = f"{_BASE}/{blueprint_id}/virtual_infra/query/vm"
    resp = base.raw_request(url, "POST", data=body or {})
    if resp.status_code not in (200, 201):
        raise Exception(f"query/vm POST failed [{resp.status_code}]: {resp.text}")
    payload = resp.json()
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and "items" in payload:
        return payload["items"]
    return [payload] if payload else []


def get_blueprint_vnet(client_factory, blueprint_id, vnet_id):
    """GET .../virtual_infra/vnet/{vnet_id}

    Retrieves virtual-network details from the virtual-infra layer of
    the blueprint.

    :param client_factory: ApstraClientFactory instance
    :param blueprint_id:   Blueprint UUID
    :param vnet_id:        Virtual network UUID
    :returns:              vnet dict, or None if 404
    :raises Exception:     On non-2xx (other than 404) HTTP status
    """
    base = client_factory.get_base_client()
    url = f"{_BASE}/{blueprint_id}/virtual_infra/vnet/{vnet_id}"
    resp = base.raw_request(url, "GET")
    if resp.status_code == 404:
        return None
    if resp.status_code != 200:
        raise Exception(f"vnet GET failed [{resp.status_code}]: {resp.text}")
    return resp.json()
