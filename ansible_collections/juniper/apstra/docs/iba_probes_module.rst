.. Document meta

:orphan:

.. Title

juniper.apstra.iba_probes module -- Manage IBA probes and dashboards in Apstra
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. Collection note

.. note::
    This module is part of the `juniper.apstra collection <https://galaxy.ansible.com/ui/repo/published/juniper/apstra/>`_.

.. version_added

.. rst-class:: ansible-version-added

New in juniper.apstra 0.1.0

.. contents::
   :local:
   :depth: 1

Synopsis
--------

- This module manages IBA (Intent-Based Analytics) probes and dashboards in Apstra blueprints.
- Supports instantiation of predefined (built-in) probes from a catalog of 48+ probe types.
- Supports CRUD operations on custom (raw) probes with user-defined processors and stages.
- Supports CRUD operations on IBA dashboards for probe visualisation.
- Probes and dashboards can be referenced by UUID or label for all operations (create, read, update, delete).
- The module uses the Apstra REST API directly via ``raw_request`` as the SDK does not expose a dedicated IBA probe interface.

Overview
--------

**Intent-Based Analytics (IBA)** is Apstra's real-time analytics framework that continuously monitors your data centre fabric and raises anomalies when the network deviates from its intended state. At the heart of IBA are **probes** — self-contained analytics pipelines that:

1. **Collect** telemetry from every managed device (counters, BGP state, LLDP, EVPN, etc.).
2. **Process** data through a chain of processors (aggregation, range checks, comparisons, match counts).
3. **Produce stages** — intermediate and final result tables that feed dashboards and anomaly detection.
4. **Raise anomalies** when values fall outside expected ranges.

Key Concepts
~~~~~~~~~~~~

- **Predefined Probe**: A built-in probe template shipped with Apstra. You instantiate it with parameters (label, thresholds, durations). Apstra auto-generates the full processor pipeline.
- **Custom Probe**: A probe you build from scratch, defining every processor, input, output, and graph query.
- **Dashboard**: A visual grouping of probe stages in the Apstra UI for at-a-glance monitoring.
- **Anomaly**: A deviation from expected state raised by a probe.

Parameters
----------

**api_url** (string): The URL used to access the Apstra api. Default: ``APSTRA_API_URL`` environment variable.

**verify_certificates** (boolean): If set to false, SSL certificates will not be verified. Default: ``True``.

**username** (string): The username for authentication. Default: ``APSTRA_USERNAME`` environment variable.

**password** (string): The password for authentication. Default: ``APSTRA_PASSWORD`` environment variable.

**auth_token** (string): The authentication token to use if already authenticated. Default: ``APSTRA_AUTH_TOKEN`` environment variable.

**type** (string): The type of IBA resource to manage. Choices: ``predefined``, ``probe``, ``dashboard``. Default: ``predefined``.

  - ``predefined`` — Instantiates a probe from the Apstra predefined probe catalog (48+ types).
  - ``probe`` — Manages custom (raw) probes directly.
  - ``dashboard`` — Manages IBA dashboards.

**id** (dictionary): Dictionary containing resource identifiers.

  - Always requires ``blueprint`` key with the blueprint UUID or label.
  - For existing probes, include ``probe`` key with probe UUID or label.
  - For dashboards, include ``dashboard`` key with dashboard UUID or label.
  - Name/label resolution is supported for ``blueprint``, ``probe``, and ``dashboard`` keys.

**body** (dictionary): Dictionary containing the resource details.

  - For predefined probes: ``predefined_probe`` is the probe name (e.g. ``bgp_session``), and additional keys are the schema parameters (``label``, ``duration``, ``threshold``, etc.).
  - For custom probes: keys include ``label``, ``description``, ``disabled``, and ``processors``.
  - For dashboards: keys include ``label`` and ``description``.

**state** (string): Desired state of the resource. Choices: ``present``, ``absent``. Default: ``present``.

Return Values
-------------

**changed** (boolean): Indicates whether the module has made any changes. Returned: always.

**id** (dictionary): Dictionary of resource identifiers (``blueprint``, ``probe`` or ``dashboard``). Returned: on create or when found by label.

**probe** (dictionary): The full probe object details. Returned: when type is ``predefined`` or ``probe`` with state ``present``.

**dashboard** (dictionary): The full dashboard object details. Returned: when type is ``dashboard`` with state ``present``.

**changes** (dictionary): Dictionary of updates that were applied. Returned: on update.

**msg** (string): The output message that the module generates. Returned: always.

**predefined_probes** (list): List of available predefined probe names. Returned: when type is ``predefined`` with state ``present`` and no ``body`` specified.

Available Predefined Probes (48 Types)
--------------------------------------

Traffic & Bandwidth
~~~~~~~~~~~~~~~~~~~

- ``traffic`` — Monitors interface traffic counters (RX/TX utilization, errors, broadcasts).
- ``bandwidth_utilization`` — Calculates bandwidth utilization history at varying aggregation levels.
- ``eastwest_traffic`` — Tracks east-west traffic patterns across the fabric.
- ``stripe_traffic`` — Monitors traffic distribution across fabric stripes.

BGP & Routing
~~~~~~~~~~~~~

- ``bgp_session`` — Monitors BGP session status; raises anomalies for flapping sessions.
- ``external_routes`` — Tracks external routes received by the fabric.
- ``evpn_vxlan_type3`` — Validates EVPN VXLAN Type-3 routes.
- ``evpn_vxlan_type5`` — Validates EVPN VXLAN Type-5 routes.

Load Balancing & ECMP
~~~~~~~~~~~~~~~~~~~~~

- ``fabric_ecmp_imbalance`` — Detects ECMP imbalance across fabric interfaces.
- ``external_ecmp_imbalance`` — Detects ECMP imbalance on external links.
- ``spine_superspine_ecmp_imbalance`` — ECMP imbalance between spine and superspine layers.
- ``lag_imbalance`` — Detects traffic imbalance across LAG member interfaces.
- ``mlag_imbalance`` — Detects traffic imbalance across MLAG pairs.
- ``esi_imbalance`` — Detects traffic imbalance across ESI-LAG member interfaces.

Device Health & Telemetry
~~~~~~~~~~~~~~~~~~~~~~~~~

- ``device_health`` — Alerts when CPU, memory, or disk usage exceeds thresholds.
- ``device_telemetry_health`` — Monitors telemetry streaming health.
- ``environmental_data`` — Monitors temperature, fan speed, and power supply status.
- ``npu_utilization`` — Monitors NPU (Network Processing Unit) utilization.
- ``pfe_usage`` — Monitors Packet Forwarding Engine memory and filter utilisation.

Interface & Fabric Monitoring
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ``fabric_interface_flapping`` — Detects interface flapping on fabric links.
- ``specific_interface_flapping`` — Monitors flapping on specific named interfaces.
- ``spine_superspine_interface_flapping`` — Interface flapping on spine-superspine links.
- ``fabric_hotcold_ifcounter`` — Identifies hot/cold fabric interfaces by counter values.
- ``specific_hotcold_ifcounter`` — Hot/cold analysis on specific interfaces.
- ``spine_superspine_hotcold_ifcounter`` — Hot/cold counters on spine-superspine interfaces.
- ``optical_transceivers`` — Monitors optical transceiver power levels.
- ``packet_discard_percentage`` — Tracks packet discard rates across interfaces.

Security & Policy
~~~~~~~~~~~~~~~~~

- ``copp`` — Validates Control Plane Policing output; alerts on excessive policer drops.
- ``interface_policy_dot1x`` — Monitors 802.1X interface policy compliance.

Fault Tolerance
~~~~~~~~~~~~~~~

- ``spine_fault_tolerance`` — Validates that the fabric can tolerate spine failures.
- ``lag_fault_tolerance`` — Validates LAG fault tolerance across member links.

EVPN & VXLAN
~~~~~~~~~~~~~

- ``evpn_host_flapping`` — Detects hosts flapping between EVPN endpoints.
- ``vxlan_floodlist`` — Validates VXLAN flood list consistency.
- ``shared_tunnel_mode`` — Monitors shared tunnel mode operation.

MAC & ARP
~~~~~~~~~

- ``mac_monitor`` — Monitors MAC address table entries.

Server & Compute
~~~~~~~~~~~~~~~~

- ``server_sla_a`` — Server SLA monitoring (type A).
- ``server_sla_b`` — Server SLA monitoring (type B).
- ``compute_agent_hw_counters`` — Analyses hardware counters from compute agents.
- ``multiagent_detector`` — Detects multiple telemetry agents on a single device.

Virtual Infrastructure
~~~~~~~~~~~~~~~~~~~~~~

- ``hypervisor_mtu_checks`` — Validates MTU settings across hypervisor environments.
- ``hypervisor_mtu_mismatch`` — Detects MTU mismatches between hypervisors.
- ``missing_vlan_vms`` — Identifies VMs with missing VLAN configurations.
- ``virtual_infra_hypervisor_redundancy_checks`` — Validates hypervisor network redundancy.
- ``virtual_infra_lag_match`` — Checks LAG configuration consistency for virtual infrastructure.
- ``virtual_infra_missing_lldp`` — Detects missing LLDP on virtual infrastructure ports.
- ``virtual_infra_vlan_match`` — Validates VLAN configuration matching for virtual infrastructure.

Drain Operations
~~~~~~~~~~~~~~~~

- ``drain_node_traffic_anomaly`` — Monitors traffic during node drain operations.

Examples
--------

Predefined Probes
~~~~~~~~~~~~~~~~~

.. code-block:: yaml+jinja

    - name: Authenticate to Apstra
      juniper.apstra.authenticate:
        logout: false
      register: auth

    - name: List all available predefined probes
      juniper.apstra.iba_probes:
        type: predefined
        id:
          blueprint: "my-blueprint"
        state: present
        auth_token: "{{ auth.token }}"
      register: predefined_list

    - name: Create a BGP Session probe
      juniper.apstra.iba_probes:
        type: predefined
        id:
          blueprint: "my-blueprint"
        body:
          predefined_probe: bgp_session
          label: "BGP Monitoring"
          duration: 300
          threshold: 40
        auth_token: "{{ auth.token }}"
      register: bgp_probe

    - name: Create a Bandwidth Utilization probe
      juniper.apstra.iba_probes:
        type: predefined
        id:
          blueprint: "my-blueprint"
        body:
          predefined_probe: bandwidth_utilization
          label: "Bandwidth Utilization"
          first_summary_average_period: 120
          first_summary_total_duration: 3600
          second_summary_average_period: 3600
          second_summary_total_duration: 2592000
        auth_token: "{{ auth.token }}"

    - name: Create a Device System Health probe
      juniper.apstra.iba_probes:
        type: predefined
        id:
          blueprint: "my-blueprint"
        body:
          predefined_probe: device_health
          label: "Device System Health"
          raise_switch_anomaly: true
          raise_server_anomaly: true
          history_duration: 2592000
        auth_token: "{{ auth.token }}"

    - name: Create a Control Plane Policing probe
      juniper.apstra.iba_probes:
        type: predefined
        id:
          blueprint: "my-blueprint"
        body:
          predefined_probe: copp
          label: "Control Plane Policing"
          aggregation_period: 300
          collection_interval: 120
          history_duration: 2592000
          drop_count_threshold: 1
        auth_token: "{{ auth.token }}"

    - name: Create a Device Telemetry Health probe
      juniper.apstra.iba_probes:
        type: predefined
        id:
          blueprint: "my-blueprint"
        body:
          predefined_probe: device_telemetry_health
          label: "Device Telemetry Health"
        auth_token: "{{ auth.token }}"

    - name: Create a LAG Imbalance probe
      juniper.apstra.iba_probes:
        type: predefined
        id:
          blueprint: "my-blueprint"
        body:
          predefined_probe: lag_imbalance
          label: "LAG Imbalance"
        auth_token: "{{ auth.token }}"

    - name: Create a Fabric ECMP Imbalance probe
      juniper.apstra.iba_probes:
        type: predefined
        id:
          blueprint: "my-blueprint"
        body:
          predefined_probe: fabric_ecmp_imbalance
          label: "ECMP Imbalance (Fabric)"
        auth_token: "{{ auth.token }}"

    - name: Create an ESI Imbalance probe
      juniper.apstra.iba_probes:
        type: predefined
        id:
          blueprint: "my-blueprint"
        body:
          predefined_probe: esi_imbalance
          label: "ESI Imbalance"
        auth_token: "{{ auth.token }}"

    - name: Create a MAC Monitor probe
      juniper.apstra.iba_probes:
        type: predefined
        id:
          blueprint: "my-blueprint"
        body:
          predefined_probe: mac_monitor
          label: "MAC Monitor"
        auth_token: "{{ auth.token }}"

Read & Update Probes
~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml+jinja

    - name: Read a probe by ID
      juniper.apstra.iba_probes:
        type: probe
        id:
          blueprint: "my-blueprint"
          probe: "{{ bgp_probe.id.probe }}"
        state: present
        auth_token: "{{ auth.token }}"

    - name: Read a probe by label (name resolution)
      juniper.apstra.iba_probes:
        type: probe
        id:
          blueprint: "my-blueprint"
          probe: "BGP Monitoring"
        state: present
        auth_token: "{{ auth.token }}"

    - name: Update a probe description (find by label in body)
      juniper.apstra.iba_probes:
        type: probe
        id:
          blueprint: "my-blueprint"
        body:
          label: "BGP Monitoring"
          description: "Updated BGP probe description"
        state: present
        auth_token: "{{ auth.token }}"

    - name: Disable a probe
      juniper.apstra.iba_probes:
        type: probe
        id:
          blueprint: "my-blueprint"
        body:
          label: "BGP Monitoring"
          disabled: true
        state: present
        auth_token: "{{ auth.token }}"

Delete Probes
~~~~~~~~~~~~~

.. code-block:: yaml+jinja

    - name: Delete a probe by ID
      juniper.apstra.iba_probes:
        type: probe
        id:
          blueprint: "my-blueprint"
          probe: "{{ bgp_probe.id.probe }}"
        state: absent
        auth_token: "{{ auth.token }}"

    - name: Delete a probe by label (via id.probe name resolution)
      juniper.apstra.iba_probes:
        type: probe
        id:
          blueprint: "my-blueprint"
          probe: "BGP Monitoring"
        state: absent
        auth_token: "{{ auth.token }}"

    - name: Delete a probe by label (via body.label fallback)
      juniper.apstra.iba_probes:
        type: probe
        id:
          blueprint: "my-blueprint"
        body:
          label: "BGP Monitoring"
        state: absent
        auth_token: "{{ auth.token }}"

IBA Dashboards
~~~~~~~~~~~~~~

.. code-block:: yaml+jinja

    - name: Create an IBA dashboard
      juniper.apstra.iba_probes:
        type: dashboard
        id:
          blueprint: "my-blueprint"
        body:
          label: "Fabric Health Dashboard"
          description: "Overview of fabric health probes"
        state: present
        auth_token: "{{ auth.token }}"
      register: dash

    - name: Read a dashboard by label (name resolution)
      juniper.apstra.iba_probes:
        type: dashboard
        id:
          blueprint: "my-blueprint"
          dashboard: "Fabric Health Dashboard"
        state: present
        auth_token: "{{ auth.token }}"

    - name: Update a dashboard description
      juniper.apstra.iba_probes:
        type: dashboard
        id:
          blueprint: "my-blueprint"
        body:
          label: "Fabric Health Dashboard"
          description: "Updated description"
        state: present
        auth_token: "{{ auth.token }}"

    - name: Delete a dashboard by ID
      juniper.apstra.iba_probes:
        type: dashboard
        id:
          blueprint: "my-blueprint"
          dashboard: "{{ dash.id.dashboard }}"
        state: absent
        auth_token: "{{ auth.token }}"

    - name: Delete a dashboard by label (name resolution)
      juniper.apstra.iba_probes:
        type: dashboard
        id:
          blueprint: "my-blueprint"
          dashboard: "Fabric Health Dashboard"
        state: absent
        auth_token: "{{ auth.token }}"

Name / Label Resolution
~~~~~~~~~~~~~~~~~~~~~~~

All ID fields (``blueprint``, ``probe``, ``dashboard``) support name/label resolution.
You can pass either a UUID or a human-readable label, and the module resolves it automatically.

.. code-block:: yaml+jinja

    # Using UUIDs
    - name: Read probe by UUID
      juniper.apstra.iba_probes:
        type: probe
        id:
          blueprint: "54bd9839-275e-4444-8ef2-5093f49e08b7"
          probe: "99a47423-c172-4006-b55a-da37102f73e4"
        state: present
        auth_token: "{{ auth.token }}"

    # Using labels (equivalent to above)
    - name: Read probe by label
      juniper.apstra.iba_probes:
        type: probe
        id:
          blueprint: "my-blueprint-label"
          probe: "BGP Monitoring"
        state: present
        auth_token: "{{ auth.token }}"

API Endpoints
-------------

The module uses these Apstra REST API endpoints:

.. list-table::
  :width: 100%
  :widths: 10 50 40
  :header-rows: 1

  * - Method
    - Endpoint
    - Description
  * - ``GET``
    - ``/api/blueprints/{bp_id}/probes``
    - List all probes
  * - ``POST``
    - ``/api/blueprints/{bp_id}/probes``
    - Create a custom probe
  * - ``GET``
    - ``/api/blueprints/{bp_id}/probes/{probe_id}``
    - Get a probe
  * - ``PUT``
    - ``/api/blueprints/{bp_id}/probes/{probe_id}``
    - Update a probe
  * - ``DELETE``
    - ``/api/blueprints/{bp_id}/probes/{probe_id}``
    - Delete a probe
  * - ``GET``
    - ``/api/blueprints/{bp_id}/iba/predefined-probes``
    - List predefined probes
  * - ``POST``
    - ``/api/blueprints/{bp_id}/iba/predefined-probes/{name}``
    - Instantiate predefined probe
  * - ``GET``
    - ``/api/blueprints/{bp_id}/iba/dashboards``
    - List dashboards
  * - ``POST``
    - ``/api/blueprints/{bp_id}/iba/dashboards``
    - Create a dashboard
  * - ``GET``
    - ``/api/blueprints/{bp_id}/iba/dashboards/{id}``
    - Get a dashboard
  * - ``PUT``
    - ``/api/blueprints/{bp_id}/iba/dashboards/{id}``
    - Update a dashboard
  * - ``DELETE``
    - ``/api/blueprints/{bp_id}/iba/dashboards/{id}``
    - Delete a dashboard
