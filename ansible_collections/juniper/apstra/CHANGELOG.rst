=======================================
Juniper Apstra Collection Release Notes
=======================================

.. contents:: Topics

v1.0.3
======

Minor Changes
-------------
- updated galaxy yaml for all licenses

v1.0.2
======

Minor Changes
-------------
- removed community.general dependency
- added fqdn to command output
- resolved missing:metaclass error
- updated license to Apache-2.0
- upadted document for IRC link

v1.0.1
======

Minor Changes
-------------
- removed duplicate support readme

v1.0.0
======

Minor Changes
-------------
- Upgrading version for uploading to redhat automation hub

v0.1.34
=======

Major Changes
-------------
- Add required field remote_host for updating application point.

v0.1.33
=======

Minor Changes
-------------

- Changed the namespace of the collection.
- Add image file build.

v0.1.32
=======

Minor Changes
-------------

- Add debug logging of retry attempts.

v0.1.31
=======

Minor Changes
-------------

- Add retry logic to improve reliability.

v0.1.30
=======

Minor Changes
-------------

- Upgraded to AOS SDK 5.1

v0.1.29
=======

Minor Changes
-------------

- Report stack trace when debug is enabled and an exception is raised.

v0.1.28
=======

Major Changes
-------------

- Add execution environment image build.

v0.1.27
=======

Minor Changes
-------------

- Update documentation links to github.com.

v0.1.26
=======

Minor Changes
-------------

- Limit dependency specification.

v0.1.24
=======

Minor Changes
-------------

- Add ability to delete by label for virtual networks, security zones, routing policies, endpoint policies, and tags.

v0.1.23
=======

Bug Fixes
---------

- Creating tags was not idempotent. Fixed.

v0.1.22
=======

Bug Fixes
---------

- Use proper API from SDK to ensure blueprint commit works.

v0.1.21
=======

Minor Changes
-------------

- Remove dependency on kubernetes.core (not needed yet).

v0.1.20
=======

Bug Fixes
---------

- Blueprint commit reports failure if commit is not successful.

v0.1.19
=======

Bug Fixes
---------

- Blueprint commit was never working. Happy-path works now.

v0.1.18
=======

Bug Fixes
---------

- Fix various documentation issues (spelling, links, etc.)

v0.1.17
=======

Minor Changes
-------------

- Only update the application points if needed.

v0.1.16
=======

Minor Changes
-------------

- Add dependencies to community.general and kuberentes.core.

v0.1.15
=======

Major Changes
-------------

- Update application points by label instead of ID.

Minor Changes
-------------

- Find objects by label with the graph API.
- Look up endpoint policies by virtual network label.

v0.1.14
=======

Minor Changes
-------------

- Replace node_type parameter in apstra_facts with more generic filter parameter. Default behavior is unchanged for nodes.

v0.1.13
=======

Bug Fixes
---------

- Delete operation was not working for security zones and virtual networks. Resolved.

v0.1.12
=======

Major Changes
-------------

- Fixed the update of application-points by always patching the application-point object if data is supplied in the application_points field of the endpoint_policy module body field.
- Added apstra_facts support for "blueprints.systems", "devices" and "nodes".

Bug Fixes
---------

- Application point changes were not processed if the endpoints were not changed. Resolved.


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
