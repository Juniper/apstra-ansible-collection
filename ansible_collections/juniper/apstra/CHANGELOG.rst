=======================================
Juniper Apstra Collection Release Notes
=======================================

.. contents:: Topics

v1.0.8
======

Major Changes
-------------
- Added ``floating_ip`` module: Create, update, and delete floating IP addresses in an Apstra blueprint.
- Added ``upgrade_management`` module: Manage device OS upgrades in Apstra, including upgrade group creation, OS image assignment, and upgrade execution.

Minor Changes
-------------
- ``blueprint``: Added ``commit_description`` parameter to supply a description when committing a blueprint.
- ``blueprint``: Added rack renaming feature to rename racks within a blueprint.
- ``virtual_network``: Added ``vim_ip`` shorthand and ``vlan_remediation_policy`` support.
- ``security_zone``: Added tag support for security zones.
- ``cabling_map``: Added create-or-update support and LLDP nodes-and-links retrieval.
- ``generic_systems``: Added ``node_id`` and ``node_label`` aliases for easier node identification.
- ``design``: Improved logical device lookup with ``display_name`` fallback and clear error messaging.
- ``design``: Improved idempotency logic for design templates.
- Added default ``ref_archs`` for ``two_stage_l3clos`` blueprint design.
- Added IPv4 on physical interface support.
- VRF name and label shorthand support.
- Updated EE builder SDK wheel.

Bug Fixes
---------
- ``cabling_map``: Fixed ``state=lldp`` to return both LLDP nodes and links.
- ``design``: Fixed logical device lookup to fall back to listing all devices and matching by ``display_name``.
- Fixed port ID resolution issue.
- Fixed ``KeyError`` in exception handlers by removing duplicate ``msg`` key.
- Removed hardcoded blueprint name from test utilities.
- Resolved non-existent VRF bug.
- Fixed ``validate-modules`` invalid-documentation errors for Author field.
- Fixed documentation typos (``connectivity_template_assignment``, README).

v1.0.7
======

Major Changes
-------------
- Added ``interconnect_gateway`` module: Create, update, and delete interconnect (DCI) gateways in an Apstra blueprint with name-to-ID resolution for domain labels and node labels.
- Added ``iba_probes`` module: Create, update, and delete Intent-Based Analytics (IBA) probes with full CRUD and name/label resolution.
- Added ``cabling_map`` module: View and manage the cabling map (cable-state) of an Apstra blueprint.
- Added ``virtual_infra_manager`` module: Manage virtual infrastructure managers (e.g., VMware vCenter) in Apstra.
- Added name-to-ID resolution across all modules for improved usability.

Minor Changes
-------------
- ``connectivity_template_assignment``: Resolve interface names to application point IDs; support ``system_label:if_name`` shorthand strings.
- ``virtual_network``: Added support for global ``vlan_id`` and ESI Pair Auto-Expansion.
- ``fabric_settings``: Module updates for additional fabric-wide settings.
- ``blueprint``: Added template name support and single device acknowledgment functionality.
- Device assignment optimization for faster blueprint operations.
- Added IBA probes RST documentation and updated docs index.
- Added DCI end-to-end test configurations.
- Upgraded EE builder to aos-sdk 6.1.0.
- Added integration tests for ``configlets``, ``property_set``, and ``resource_pools`` modules.
- Fixed installation guide and example playbook documentation.

Bug Fixes
---------
- ``system_agents``: Require ``platform`` on create and carry over ``username`` on update.
- ``interface_map``: Replaced non-existent SDK methods with ``raw_request``.
- ``resource_group``: Resolve VRF-scoped group names and handle non-existent resource groups gracefully.
- ``resource_pools``: Validate resource pool existence before blueprint assignment.
- ``configlets``/``property_set``: Fixed nested dict key handling and YAML semantic comparison.
- ``generic_systems``: Fixed test playbook issues.
- Fixed pylint errors blocking Galaxy upload.
- Fixed two customer-reported bugs in endpoint policy and virtual network modules.

v1.0.6
======

Major Changes
-------------
- Added ``ztp_device`` module: Create, delete, and check ZTP (Zero Touch Provisioning) device status. Supports ``state: present`` (list all or create), ``state: absent`` (delete by IP), and ``state: status`` (lookup by IP address or system ID).
- Added ``rollback`` module: Roll back a blueprint to a specific revision (``state: rolledback``), revert to the latest backup (``state: reverted``), or list available revisions (``state: listed``).
- Added ``connectivity_template`` module: Create, update, and delete Connectivity Templates in an Apstra blueprint composed of network primitives (IP Link, BGP Peering, Routing Policy, etc.).
- Added ``connectivity_template_assignment`` module: Assign or unassign Connectivity Templates to application point nodes (interfaces) within an Apstra blueprint.
- Added ``external_gateway`` module: Create, update, and delete external EVPN remote gateways in an Apstra blueprint for inter-DC or WAN BGP/L2VPN peering.
- Added ``generic_systems`` module: Create, update, and delete generic systems in an Apstra blueprint, including links to fabric switches, loopback configuration, and ASN assignment via graph mutation.
- Added ``configlets`` module: Create, update, and delete configlets in Apstra. Supports global catalog and blueprint-scoped configlets with role-based targeting conditions.
- Added ``property_set`` module: Create, update, and delete property sets (key-value stores) at global and blueprint scope.
- Added ``resource_pools`` module: Create, update, and delete global resource pools. Supported types: ASN, Integer, IP, IPv6, VLAN, and VNI.
- Refactored blueprint module utilities: extracted blueprint API helpers into dedicated ``bp_*.py`` modules under ``module_utils/apstra`` for better maintainability and reuse.
- Moved raw API graph-mutation helpers to ``module_utils/apstra`` for shared use across modules.

Minor Changes
-------------
- Standardized ``id``/``body``/``state`` parameter structure across all modules for consistency.
- Added phase tags to integration test playbooks to support phased execution.
- Added Installation Documentation and Getting Started section to README.
- Updated README with detailed module descriptions and doc links for all new modules.

Bug Fixes
---------
- ``generic_systems``: Fixed ``_list_agents`` SDK response unwrap, platform field carry-through on update, and ASN coercion to integer.
- ``connectivity_template``: Fixed ``neighbor_asn_type`` static setting and ASN domain node PATCH handling.
- ``external_gateway``: Fixed blueprint commit after applying external gateway configuration.
- ``endpoint_policy``: Fixed VN endpoint policy to use pipeline EP ID; restored correct idempotency behavior.
- Restored ``id``/``body``/``state`` param structure and ``external`` field handling in ``_handle_update``.

v1.0.5
======

Minor Changes
-------------
- updated config.yml for supported python version

v1.0.4
======

Minor Changes
-------------
- updated virtual_networks module to support no-changed-when

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
