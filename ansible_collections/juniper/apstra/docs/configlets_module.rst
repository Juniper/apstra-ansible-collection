.. Document meta

:orphan:

.. Title

juniper.apstra.configlets module -- Manage configlets in Apstra
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

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

- This module allows you to create, update, and delete configlets in Apstra.
- Supports both catalog (design) configlets and blueprint configlets.
- Catalog configlets are stored in the global design catalog.
- Blueprint configlets are applied to a specific blueprint and include a condition for role-based targeting.
- Configlets contain one or more generators, each specifying the config style, section, template text, negation template text, and optional filename.

Parameters
----------

**api_url** (string): The URL used to access the Apstra api. Default: APSTRA_API_URL environment variable

**auth_token** (string): The authentication token to use if already authenticated. Default: APSTRA_AUTH_TOKEN environment variable

**body** (dictionary): Dictionary containing the configlet details. For catalog configlets, keys include ``display_name``, ``ref_archs``, and ``generators``. For blueprint configlets, keys include ``label``, ``condition``, and ``configlet`` (which contains ``display_name`` and ``generators``).

**id** (dictionary): Dictionary containing the configlet ID. For catalog configlets, use ``configlet`` key. For blueprint configlets, use ``blueprint`` and optionally ``configlet`` keys.

**password** (string): The password for authentication. Default: APSTRA_PASSWORD environment variable

**state** (string): Desired state of the configlet. Choices: present, absent. Default: present

**type** (string): The type of configlet to manage. Choices: catalog, blueprint. Default: catalog

**username** (string): The username for authentication. Default: APSTRA_USERNAME environment variable

**verify_certificates** (boolean): If set to false, SSL certificates will not be verified. Default: True

Examples
--------

Catalog Configlet
~~~~~~~~~~~~~~~~~

.. code-block:: yaml+jinja

    - name: Create a catalog configlet
      juniper.apstra.configlets:
        type: catalog
        body:
          display_name: "SNMP Config"
          ref_archs:
            - "two_stage_l3clos"
          generators:
            - config_style: "junos"
              section: "system"
              template_text: |
                snmp {
                  community public;
                }
              negation_template_text: ""
              filename: ""
        state: present

    - name: Update a catalog configlet
      juniper.apstra.configlets:
        type: catalog
        id:
          configlet: "configlet-uuid-here"
        body:
          display_name: "SNMP Config Updated"
          ref_archs:
            - "two_stage_l3clos"
          generators:
            - config_style: "junos"
              section: "system"
              template_text: |
                snmp {
                  community private;
                }
              negation_template_text: ""
              filename: ""
        state: present

    - name: Delete a catalog configlet
      juniper.apstra.configlets:
        type: catalog
        id:
          configlet: "configlet-uuid-here"
        state: absent

Blueprint Configlet
~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml+jinja

    - name: Create a blueprint configlet
      juniper.apstra.configlets:
        type: blueprint
        id:
          blueprint: "blueprint-uuid-here"
        body:
          label: "Leaf SNMP Config"
          condition: 'role in ["leaf"]'
          configlet:
            display_name: "Leaf SNMP Config"
            generators:
              - config_style: "junos"
                section: "system"
                template_text: |
                  snmp {
                    community public;
                  }
                negation_template_text: ""
                filename: ""
        state: present

    - name: Update a blueprint configlet
      juniper.apstra.configlets:
        type: blueprint
        id:
          blueprint: "blueprint-uuid-here"
          configlet: "configlet-id-here"
        body:
          label: "Leaf SNMP Config"
          condition: 'role in ["leaf", "spine"]'
          configlet:
            display_name: "Leaf SNMP Config"
            generators:
              - config_style: "junos"
                section: "system"
                template_text: |
                  snmp {
                    community private;
                  }
                negation_template_text: ""
                filename: ""
        state: present

    - name: Delete a blueprint configlet
      juniper.apstra.configlets:
        type: blueprint
        id:
          blueprint: "blueprint-uuid-here"
          configlet: "configlet-id-here"
        state: absent

Generator Fields
~~~~~~~~~~~~~~~~

Each generator in the ``generators`` list supports the following fields:

- ``config_style``: The NOS config style. Values: ``junos``, ``eos``, ``nxos``, ``sonic``.
- ``section``: Where in the config the template is applied. Values: ``system``, ``set_based_system``, ``interface``, ``set_based_interface``, ``file``, ``ospf``, etc.
- ``template_text``: The Jinja2 template text for the configuration.
- ``negation_template_text``: Template text for removing the configuration.
- ``filename``: Optional filename (used with ``file`` section type).

Return Values
-------------

**changed** (boolean): Indicates whether the module has made any changes. Returned: always.

**changes** (dictionary): Dictionary of updates that were applied. Returned: on update.

**response** (dictionary): The configlet object details. Returned: when state is present and changes are made.

**id** (dictionary): The ID of the configlet. Returned: on create, or when object identified by display_name/label.

**configlet** (dictionary): The final configlet object details. Returned: on create or update.

**msg** (string): The output message that the module generates. Returned: always.
