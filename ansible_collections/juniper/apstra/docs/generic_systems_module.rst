.. Document meta

:orphan:

.. Title

juniper.apstra.generic_systems module -- Manage generic systems in Apstra blueprints
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

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

- This module allows you to create, update, and delete generic systems in Apstra blueprints.
- Generic systems represent servers, storage devices, or other endpoints connected to switches in a blueprint.
- Uses the switch-system-links API to create generic systems along with their links to switches.
- Supports updating generic system properties such as hostname, label, deploy mode, and link configuration.
- Supports deleting generic systems by removing all their switch-system links.
- Requires a blueprint to already exist before managing generic systems.

Parameters
----------

**api_url** (string): The URL used to access the Apstra api. Default: APSTRA_API_URL environment variable

**auth_token** (string): The authentication token to use if already authenticated. Default: APSTRA_AUTH_TOKEN environment variable

**body** (dictionary): Dictionary containing the generic system configuration.

  For creating systems, keys include:

  - ``links``: List of link definitions connecting switches to the generic system.
  - ``new_systems``: List of new generic system definitions to create.

  Each link contains:

  - ``lag_mode``: LAG mode (null, ``lacp_active``, ``lacp_passive``, ``static_lag``).
  - ``link_group_label``: Optional label for grouping links in a LAG.
  - ``switch``: Dictionary with ``system_id``, ``transformation_id``, ``if_name``, and optionally ``operation_state``.
  - ``system``: Dictionary with ``system_id`` (null for new systems, or an existing system ID).

  Each system in ``new_systems`` contains:

  - ``system_type``: Type of system (``server``, ``l2_server``, ``remote_evpn_gateway``).
  - ``hostname``: Hostname of the generic system.
  - ``label``: Display label for the generic system.
  - ``deploy_mode``: Deployment mode (``deploy``, ``ready``, ``drain``, ``undeploy``).
  - ``logical_device``: Dictionary describing the logical device (``id``, ``display_name``, ``panels``).
  - ``port_channel_id_min``: Minimum port-channel ID (0 to disable).
  - ``port_channel_id_max``: Maximum port-channel ID (0 to disable).

  For updating systems, top-level keys include ``hostname``, ``label``, ``deploy_mode``.

  For external generic systems, set ``external: true`` along with ``hostname`` and ``label``.

**id** (dictionary): Dictionary containing the IDs for the generic system.

  - ``blueprint`` (required): The blueprint ID.
  - ``generic_system`` (optional): The system node ID, required for update and delete operations.

**password** (string): The password for authentication. Default: APSTRA_PASSWORD environment variable

**state** (string): Desired state of the generic system. Choices: ``present``, ``absent``. Default: ``present``

**username** (string): The username for authentication. Default: APSTRA_USERNAME environment variable

**verify_certificates** (boolean): If set to false, SSL certificates will not be verified. Default: True

Examples
--------

Create a Generic System
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml+jinja

    - name: Create a generic system with a link to a switch
      juniper.apstra.generic_systems:
        id:
          blueprint: "{{ bp.id.blueprint }}"
        body:
          links:
            - lag_mode: null
              switch:
                system_id: "lG8FGoBGDFo2WFKiXw"
                transformation_id: 5
                if_name: "xe-0/0/7:0"
              system:
                system_id: null
          new_systems:
            - system_type: "server"
              hostname: "my-server-01"
              label: "my-server-01"
              deploy_mode: "deploy"
              logical_device:
                id: "AOS-1x10-1"
                display_name: "AOS-1x10-1"
                panels:
                  - port_groups:
                      - roles:
                          - "leaf"
                          - "access"
                        count: 1
                        speed:
                          value: 10
                          unit: "G"
                    port_indexing:
                      schema: "absolute"
                      order: "T-B, L-R"
                      start_index: 1
                    panel_layout:
                      row_count: 1
                      column_count: 1
              port_channel_id_min: 0
              port_channel_id_max: 0
        state: present
      register: gs_create

Create a Generic System with LAG
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml+jinja

    - name: Create a generic system with LAG (dual links)
      juniper.apstra.generic_systems:
        id:
          blueprint: "{{ bp.id.blueprint }}"
        body:
          links:
            - lag_mode: "lacp_active"
              link_group_label: "server-lag"
              switch:
                system_id: "lG8FGoBGDFo2WFKiXw"
                transformation_id: 5
                if_name: "xe-0/0/6:0"
              system:
                system_id: null
            - lag_mode: "lacp_active"
              link_group_label: "server-lag"
              switch:
                system_id: "lG8FGoBGDFo2WFKiXw"
                transformation_id: 5
                if_name: "xe-0/0/7:0"
              system:
                system_id: null
          new_systems:
            - system_type: "server"
              hostname: "my-lag-server"
              label: "my-lag-server"
              deploy_mode: "deploy"
              logical_device:
                id: "AOS-2x10-1"
                display_name: "AOS-2x10-1"
                panels:
                  - port_groups:
                      - roles:
                          - "leaf"
                          - "access"
                        count: 2
                        speed:
                          value: 10
                          unit: "G"
                    port_indexing:
                      schema: "absolute"
                      order: "T-B, L-R"
                      start_index: 1
                    panel_layout:
                      row_count: 1
                      column_count: 2
              port_channel_id_min: 0
              port_channel_id_max: 0
        state: present

Update a Generic System
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml+jinja

    - name: Update generic system hostname and deploy mode
      juniper.apstra.generic_systems:
        id:
          blueprint: "{{ bp.id.blueprint }}"
          generic_system: "{{ gs_create.id.generic_system }}"
        body:
          hostname: "my-server-01-updated"
          label: "my-server-01-updated"
          deploy_mode: "ready"
        state: present

Add a Link to Existing Generic System
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml+jinja

    - name: Add another link to existing generic system
      juniper.apstra.generic_systems:
        id:
          blueprint: "{{ bp.id.blueprint }}"
        body:
          links:
            - lag_mode: null
              switch:
                system_id: "lG8FGoBGDFo2WFKiXw"
                transformation_id: 5
                if_name: "xe-0/0/8:0"
              system:
                system_id: "{{ gs_create.id.generic_system }}"
          new_systems: []
        state: present

Delete a Generic System
~~~~~~~~~~~~~~~~~~~~~~~

Removing all links to a generic system will remove the system itself.

.. code-block:: yaml+jinja

    - name: Delete a generic system
      juniper.apstra.generic_systems:
        id:
          blueprint: "{{ bp.id.blueprint }}"
          generic_system: "{{ gs_create.id.generic_system }}"
        state: absent

External Generic System
~~~~~~~~~~~~~~~~~~~~~~~

External generic systems are systems that exist outside of racks.

.. code-block:: yaml+jinja

    - name: Create external generic system
      juniper.apstra.generic_systems:
        id:
          blueprint: "{{ bp.id.blueprint }}"
        body:
          external: true
          hostname: "external-server-01"
          label: "external-server-01"
        state: present

    - name: Delete external generic system
      juniper.apstra.generic_systems:
        id:
          blueprint: "{{ bp.id.blueprint }}"
          generic_system: "ext-system-id"
        body:
          external: true
        state: absent

Link Fields
~~~~~~~~~~~

Each link in the ``links`` list supports the following fields:

- ``lag_mode``: LAG mode for the link. Values: ``null`` (no LAG), ``lacp_active``, ``lacp_passive``, ``static_lag``.
- ``link_group_label``: Label used to group multiple links into a LAG.
- ``switch``: Dictionary describing the switch side of the link.

  - ``system_id``: The switch node ID in the blueprint.
  - ``transformation_id``: The interface transformation ID.
  - ``if_name``: The interface name on the switch (e.g., ``xe-0/0/7:0``).
  - ``operation_state``: Optional operational state (``up``, ``down``).

- ``system``: Dictionary describing the generic system side of the link.

  - ``system_id``: The generic system node ID (``null`` for new systems being created).

New System Fields
~~~~~~~~~~~~~~~~~

Each system in the ``new_systems`` list supports the following fields:

- ``system_type``: Type of the system. Values: ``server``, ``l2_server``, ``remote_evpn_gateway``.
- ``hostname``: The hostname for the new generic system.
- ``label``: The display label for the new generic system.
- ``deploy_mode``: Deployment mode. Values: ``deploy``, ``ready``, ``drain``, ``undeploy``.
- ``logical_device``: Dictionary describing the logical device profile.

  - ``id``: Logical device ID (e.g., ``AOS-1x10-1``).
  - ``display_name``: Display name for the logical device.
  - ``panels``: List of panel definitions with ``port_groups``, ``port_indexing``, and ``panel_layout``.

- ``port_channel_id_min``: Minimum port-channel ID (0 to disable).
- ``port_channel_id_max``: Maximum port-channel ID (0 to disable).

Return Values
-------------

**changed** (boolean): Indicates whether the module has made any changes. Returned: always.

**id** (dictionary): The IDs of the generic system (``blueprint``, ``generic_system``). Returned: on create or when identified.

**response** (dictionary): The API response from the create or update operation. Returned: when state is present and changes are made.

**generic_system** (dictionary): The final generic system object details. Returned: on create or update.

**links** (list): List of link IDs associated with the generic system. Returned: on create.

**msg** (string): The output message that the module generates. Returned: always.
