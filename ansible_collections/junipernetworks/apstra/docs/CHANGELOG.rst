===============================================
Junipernetworks Apstra Collection Release Notes
===============================================

.. contents:: Topics

v0.1.5
======

Release Summary
---------------

Initial release candidate for a minimal set of modules required for configuring pods on an SRIOV network.

Major Changes
-------------

- Authentication with cached token is supported for all modules.
- apstra_facts module with support for:
    - blueprints
    - virtual_networks
    - security_zones
    - routing_policies
    - endpoint_policies
    - endpoint_policies_application_points
- Locking blueprints by convention via well-known tag.
- Publish generated documentation.
