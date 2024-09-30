===============================================
Junipernetworks Apstra Collection Release Notes
===============================================

.. contents:: Topics

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
