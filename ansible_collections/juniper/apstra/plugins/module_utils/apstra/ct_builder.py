# -*- coding: utf-8 -*-

# Copyright (c) 2024, Juniper Networks
# BSD 3-Clause License

"""
Connectivity Template — Builder
=================================

Converts the user-friendly dict-of-named-dicts primitive format into
the flat policy array expected by ``PUT /obj-policy-import`` and then
wraps it with the SDK generator helper.

Input format (Ansible YAML)::

    primitives:
      ip_links:
        link1:
          routing_zone_id: "Fim56-lMI9JwA5idYQ"
          interface_type: tagged
          vlan_id: 100
          bgp_peering_generic_systems:
            peer1:
              bfd: false
              ipv4_safi: true

Output: a ``{"policies": [...]}`` dict ready for
``ep_client.blueprints[bp].obj_policy_import.put(payload)``.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.juniper.apstra.plugins.module_utils.apstra.ct_primitives import (
    PRIMITIVE_TYPES,
    PLURAL_TO_SINGULAR,
)


def build_ct_payload(name, primitives, description="", tags=None):
    """
    Build the full ``obj-policy-import`` payload from user primitives.

    Parameters
    ----------
    name : str
        CT display name (``label`` in the API).
    primitives : dict
        Dict-of-named-dicts keyed by plural primitive type. Already
        validated by :func:`ct_validator.validate_primitives`.
    description : str, optional
        CT description.
    tags : list[str], optional
        Tags to attach to the CT.

    Returns
    -------
    tuple(dict, list)
        ``(payload, hierarchy)`` — *payload* is ready for
        ``obj_policy_import.put()``, *hierarchy* is the raw list
        of policy dicts (useful for extracting the CT ID).
    """
    # Lazy import to avoid hard failure when aos_sdk is missing
    from aos.sdk.reference_design.extension.endpoint_policy import (
        generator as ct_gen,
    )

    sdk_policies = _primitives_dict_to_sdk(primitives)
    hierarchy = ct_gen.create_ct_with_hierarchy(sdk_policies, name)

    # Stamp description + tags on the visible batch node
    for pol in hierarchy:
        if pol.get("visible"):
            pol["description"] = description or ""
            pol["tags"] = tags or []

    payload = ct_gen.wrap_policies(hierarchy)
    return payload, hierarchy


def get_ct_id_from_hierarchy(hierarchy):
    """Return the ID of the visible (top-level batch) policy."""
    for pol in hierarchy:
        if pol.get("visible"):
            return pol["id"]
    return None


# ── Internal helpers ──────────────────────────────────────────────────


def _primitives_dict_to_sdk(primitives):
    """
    Convert the Ansible dict-of-named-dicts format to the nested list
    that ``ct_gen.create_ct_with_hierarchy()`` expects::

        [
            {
                "policy_type_name": "AttachLogicalLink",
                "label": "link1",
                "attributes": {"security_zone": "...", ...},
                "subpolicies": [ ... ]
            },
            ...
        ]
    """
    sdk_list = []
    for plural_key, instances in primitives.items():
        singular = PLURAL_TO_SINGULAR[plural_key]
        policy_type_name = PRIMITIVE_TYPES[singular]

        for inst_name, inst_config in instances.items():
            attributes, children = _separate_attrs_and_children(inst_config)
            sdk_list.append(
                {
                    "policy_type_name": policy_type_name,
                    "label": inst_name,
                    "attributes": attributes,
                    "subpolicies": _primitives_dict_to_sdk(children),
                }
            )
    return sdk_list


def _separate_attrs_and_children(config):
    """
    Split a primitive config dict into (attributes, children).

    Keys that match a known plural primitive type name are treated as
    child primitive groups; everything else is an attribute.

    Returns
    -------
    tuple(dict, dict)
        ``(attributes, children_dict)``
    """
    attributes = {}
    children = {}
    for key, value in config.items():
        if key in PLURAL_TO_SINGULAR:
            children[key] = value
        else:
            attributes[key] = value
    return attributes, children
