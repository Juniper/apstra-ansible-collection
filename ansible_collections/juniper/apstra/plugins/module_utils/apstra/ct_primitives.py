# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

"""
Connectivity Template — Primitive Type Definitions
===================================================

Centralised look-up tables that map user-friendly primitive names to the
internal ``policy_type_name`` values used by the Apstra API, and define
which primitives are allowed per CT type and which primitives can be
nested inside others.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

# ── Singular name → Apstra policy_type_name ──────────────────────────

PRIMITIVE_TYPES = {
    "ip_link": "AttachLogicalLink",
    "virtual_network_single": "AttachSingleVLAN",
    "virtual_network_multiple": "AttachMultipleVLAN",
    "bgp_peering_generic_system": "AttachBgpOverSubinterfacesOrSvi",
    "bgp_peering_ip_endpoint": "AttachIpEndpointWithBgpNsxt",
    "routing_policy": "AttachExistingRoutingPolicy",
    "static_route": "AttachStaticRoute",
    "custom_static_route": "AttachCustomStaticRoute",
    "dynamic_bgp_peering": "AttachBgpWithPrefixPeeringForSviOrSubinterface",
    "routing_zone_constraint": "AttachRoutingZoneConstraint",
}

# Reverse map: policy_type_name → singular name
REVERSE_TYPES = {v: k for k, v in PRIMITIVE_TYPES.items()}

# ── Plural ↔ Singular mappings ───────────────────────────────────────

PLURAL_TO_SINGULAR = {
    "ip_links": "ip_link",
    "virtual_network_singles": "virtual_network_single",
    "virtual_network_multiples": "virtual_network_multiple",
    "bgp_peering_generic_systems": "bgp_peering_generic_system",
    "bgp_peering_ip_endpoints": "bgp_peering_ip_endpoint",
    "routing_policies": "routing_policy",
    "static_routes": "static_route",
    "custom_static_routes": "custom_static_route",
    "dynamic_bgp_peerings": "dynamic_bgp_peering",
    "routing_zone_constraints": "routing_zone_constraint",
}

SINGULAR_TO_PLURAL = {v: k for k, v in PLURAL_TO_SINGULAR.items()}

# ── CT types ─────────────────────────────────────────────────────────

CT_TYPES = [
    "interface",
    "svi",
    "loopback",
    "protocol_endpoint",
    "system",
]

# ── Which top-level primitives are allowed per CT type ───────────────

ALLOWED_PRIMITIVES = {
    "interface": [
        "ip_link",
        "virtual_network_single",
        "virtual_network_multiple",
        "routing_zone_constraint",
        "custom_static_route",
    ],
    "svi": [
        "virtual_network_single",
        "bgp_peering_generic_system",
        "dynamic_bgp_peering",
        "routing_zone_constraint",
        "static_route",
    ],
    "loopback": [
        "bgp_peering_ip_endpoint",
        "routing_zone_constraint",
        "static_route",
    ],
    "protocol_endpoint": [
        "bgp_peering_ip_endpoint",
        "routing_zone_constraint",
    ],
    "system": [
        "custom_static_route",
    ],
}

# ── Which child primitives can be nested inside a given parent ───────

CHILD_PRIMITIVES = {
    "ip_link": [
        "bgp_peering_generic_system",
        "static_route",
        "routing_policy",
        "custom_static_route",
    ],
    "virtual_network_single": [],
    "virtual_network_multiple": [],
    "bgp_peering_generic_system": [
        "routing_policy",
    ],
    "bgp_peering_ip_endpoint": [
        "routing_policy",
    ],
    "routing_policy": [],
    "static_route": [
        "routing_policy",
    ],
    "custom_static_route": [
        "routing_policy",
    ],
    "dynamic_bgp_peering": [
        "routing_policy",
    ],
    "routing_zone_constraint": [],
}
