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

Import Catalog Configlet to Blueprint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After creating a catalog configlet, you can import it into a blueprint by
passing the catalog configlet UUID as ``body.configlet``. The module automatically
resolves the UUID to the full catalog configlet object required by the Apstra API
(``POST /api/blueprints/{id}/configlets``).

.. code-block:: yaml+jinja

    - name: Import catalog configlet to blueprint
      juniper.apstra.configlets:
        type: blueprint
        id:
          blueprint: "blueprint-uuid-here"
        body:
          configlet: "catalog-configlet-uuid-here"
          condition: 'role in ["spine", "leaf"]'
          label: "SNMP Config"
        state: present
      register: bp_import

    - name: Remove imported catalog configlet from blueprint
      juniper.apstra.configlets:
        type: blueprint
        id:
          blueprint: "blueprint-uuid-here"
          configlet: "{{ bp_import.id.configlet }}"
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

Template Configlet with Jinja2 Variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml+jinja

    - name: Create a catalog configlet with Jinja2 template variables (NTP)
      juniper.apstra.configlets:
        type: catalog
        body:
          display_name: "NTP Template Config"
          ref_archs:
            - "two_stage_l3clos"
          generators:
            - config_style: "junos"
              section: "system"
              template_text: |
                system {
                  ntp {
                    server {{ ntp_server }};
                    boot-server {{ ntp_server }};
                  }
                }
              negation_template_text: ""
              filename: ""
        state: present

Multi-Vendor Configlet
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml+jinja

    - name: Create a multi-vendor AAA catalog configlet (junos, nxos, eos)
      juniper.apstra.configlets:
        type: catalog
        body:
          display_name: "AAA Multi-Vendor Config"
          ref_archs:
            - "two_stage_l3clos"
          generators:
            - config_style: "junos"
              section: "system"
              template_text: |
                system {
                  authentication-order [ radius password ];
                  radius-server {
                    10.0.0.100 secret radpass;
                  }
                }
              negation_template_text: ""
              filename: ""
            - config_style: "nxos"
              section: "system"
              template_text: |
                radius-server host 10.0.0.100 key radpass
                aaa authentication login default group radius local
              negation_template_text: ""
              filename: ""
            - config_style: "eos"
              section: "system"
              template_text: |
                radius-server host 10.0.0.100 key radpass
                aaa authentication login default group radius local
              negation_template_text: ""
              filename: ""
        state: present

Blueprint Syslog Configlet
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml+jinja

    - name: Create a blueprint syslog configlet
      juniper.apstra.configlets:
        type: blueprint
        id:
          blueprint: "blueprint-uuid-here"
        body:
          label: "Syslog Config"
          condition: 'role in ["leaf", "spine"]'
          configlet:
            display_name: "Syslog Config"
            generators:
              - config_style: "junos"
                section: "system"
                template_text: |
                  system {
                    syslog {
                      host 10.0.0.1 {
                        any warning;
                      }
                    }
                  }
                negation_template_text: ""
                filename: ""
        state: present

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
