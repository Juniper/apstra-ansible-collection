# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

"""
Connectivity Template — Parser
================================

Converts the flat policy list returned by ``GET /obj-policy-export/{id}``
back into the user-friendly dict-of-named-dicts format, suitable for
idempotency comparison.

The export format is a flat list of policies with ID-based references::

    [
      { "id": "A", "policy_type_name": "batch",   "visible": true,
        "attributes": {"subpolicies": ["B"]}},
      { "id": "B", "policy_type_name": "pipeline",
        "attributes": {"first_subpolicy": "C", "second_subpolicy": "D"}},
      { "id": "C", "policy_type_name": "AttachLogicalLink",
        "attributes": {...}},
      { "id": "D", "policy_type_name": "batch",
        "attributes": {"subpolicies": ["E"]}},
      ...
    ]

This module walks the batch → pipeline → primitive hierarchy and
produces::

    {
        "name": "ct-label",
        "description": "...",
        "tags": [...],
        "primitives": {
            "ip_links": {
                "test-link": {
                    "security_zone": "...",
                    "bgp_peering_generic_systems": {
                        "test-bgp": { ... }
                    }
                }
            }
        }
    }
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

from ansible_collections.juniper.apstra.plugins.module_utils.apstra.ct_primitives import (
    REVERSE_TYPES,
    SINGULAR_TO_PLURAL,
)


def parse_ct_export(export_data):
    """
    Parse the flat policy list from ``obj-policy-export`` into a
    structured dict.

    Parameters
    ----------
    export_data : list[dict]
        The list of policy dicts returned by the API.

    Returns
    -------
    dict
        ``{"name": str, "description": str, "tags": list,
           "ct_id": str, "primitives": dict}``
    """
    if not export_data:
        return None

    # Build an ID → policy lookup
    policy_map = {p["id"]: p for p in export_data}

    # Find the visible batch (top-level CT)
    batch = None
    for p in export_data:
        if p.get("visible") and p.get("policy_type_name") == "batch":
            batch = p
            break

    if batch is None:
        return None

    primitives = _parse_batch_children(batch, policy_map)

    return {
        "name": batch.get("label", ""),
        "description": batch.get("description", ""),
        "tags": batch.get("tags", []),
        "ct_id": batch["id"],
        "primitives": primitives,
    }


def normalize_for_compare(primitives):
    """
    Produce a JSON-serializable, order-stable, null-stripped
    representation of a primitives dict for comparison.

    Parameters
    ----------
    primitives : dict
        Dict-of-named-dicts (either from the user or from
        :func:`parse_ct_export`).

    Returns
    -------
    str
        Deterministic JSON string.
    """
    cleaned = _strip_and_sort(primitives)
    return json.dumps(cleaned, sort_keys=True)


# ── Internal helpers ──────────────────────────────────────────────────


def _parse_batch_children(batch, policy_map):
    """
    Walk the subpolicies of a *batch* node and return a primitives
    dict-of-named-dicts.
    """
    primitives = {}

    for pipeline_id in batch.get("attributes", {}).get("subpolicies", []):
        pipeline = policy_map.get(pipeline_id)
        if not pipeline or pipeline.get("policy_type_name") != "pipeline":
            continue

        first_id = pipeline["attributes"].get("first_subpolicy")
        second_id = pipeline["attributes"].get("second_subpolicy")

        prim_policy = policy_map.get(first_id)
        if not prim_policy:
            continue

        # Map policy_type_name → singular name → plural key
        type_name = prim_policy.get("policy_type_name", "")
        singular = REVERSE_TYPES.get(type_name)
        if singular is None:
            continue  # batch/pipeline — skip
        plural = SINGULAR_TO_PLURAL.get(singular, singular)

        # Extract attributes (strip nulls and internal keys)
        attrs = _clean_attributes(prim_policy.get("attributes", {}))

        # Recurse into children (second_subpolicy is a child batch)
        if second_id:
            child_batch = policy_map.get(second_id)
            if child_batch and child_batch.get("policy_type_name") == "batch":
                child_prims = _parse_batch_children(child_batch, policy_map)
                attrs.update(child_prims)

        # Use the label as the instance key
        inst_name = prim_policy.get("label", "unnamed")

        if plural not in primitives:
            primitives[plural] = {}
        primitives[plural][inst_name] = attrs

    return primitives


def _clean_attributes(attrs):
    """Strip null values and internal keys from attributes."""
    internal_keys = {"subpolicies", "first_subpolicy", "second_subpolicy", "resolver"}
    return {k: v for k, v in attrs.items() if v is not None and k not in internal_keys}


def _strip_and_sort(obj):
    """Recursively strip nulls, sort dicts, for stable comparison."""
    if isinstance(obj, dict):
        return {k: _strip_and_sort(v) for k, v in sorted(obj.items()) if v is not None}
    if isinstance(obj, list):
        return [_strip_and_sort(item) for item in obj]
    return obj
