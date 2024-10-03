===============================================
Junipernetworks Apstra Collection Release Notes
===============================================

.. contents:: Topics

v0.1.11
=======

Major Changes
-------------

- Added the following apstra_facts:
    - asn_pools
    - device_pools
    - integer_pools
    - ip_pools
    - ipv6_pools
    - vlan_pools
    - vni_pools

v0.1.10
=======

Major Changes
-------------

- Moved the endpoint_policies_application_points module into the endpoint_policies module.
- Added the resource_groups module to support update and delete operations on resource groups.

Minor Changes
-------------

- Add support for blueprint.policy_types to apstra_facts.
- Add support for blueprint.resource_groups to apstra_facts.
- Return the object state on create or update for virtual_networks, security_zones, routing_policies, endpoint_policies and tags.

v0.1.9
======

Minor Changes
-------------

- Change paths for the doc links to point to internal site.

v0.1.8
======

Minor Changes
-------------

- Changed apstra_facts to return the apstra_facts object under the ansible_facts object. Also, rename version to apstra_version.

v0.1.7
======

Major Changes
-------------

- Add support for tags. CRUD operations for tags, and tag assignment to virtual networks, security zones, routing policies and endpoint policies.

Minor Changes
-------------

- Progress indication via debug logs while waiting for blueprint lock or commit.


Bug Fixes
---------

- When blueprint lock timeout takes place, log a clear message not a flattened stack trace.


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
