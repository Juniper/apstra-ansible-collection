.. Document meta

:orphan:

.. |antsibull-internal-nbsp| unicode:: 0xA0
    :trim:

.. Anchors

.. _ansible_collections.juniper.apstra.connectivity_template_assignment_module:

.. Anchors: short name for ansible.builtin

.. Title

juniper.apstra.connectivity_template_assignment module -- Assign or unassign Connectivity Templates to application points
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. Collection note

.. note::
    This module is part of the `juniper.apstra collection <https://galaxy.ansible.com/ui/repo/published/juniper/apstra/>`_ (version 1.0.5).

    It is not included in ``ansible-core``.
    To check whether it is installed, run :code:`ansible-galaxy collection list`.

    To install it, use: :code:`ansible\-galaxy collection install juniper.apstra`.

    To use it in a playbook, specify: :code:`juniper.apstra.connectivity_template_assignment`.

.. version_added

.. rst-class:: ansible-version-added

New in juniper.apstra 0.1.0

.. contents::
   :local:
   :depth: 1

.. Deprecated


Synopsis
--------

.. Description

- This module assigns or unassigns Connectivity Templates (CTs) to application points (interfaces) within an Apstra blueprint.
- Application points are identified by their node IDs (interface IDs from the blueprint graph).
- Uses the :literal:`obj\-policy\-batch\-apply` API for efficient bulk assignment operations.
- The module is idempotent — it reads the current assignment state and only makes changes when the desired state differs.
- Use the :literal:`connectivity\_template` module to create CTs before assigning them.


.. Aliases


.. Requirements






.. Options

Parameters
----------

.. tabularcolumns:: \X{1}{3}\X{2}{3}

.. list-table::
  :width: 100%
  :widths: auto
  :header-rows: 1
  :class: longtable ansible-option-table

  * - Parameter
    - Comments

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-api_url"></div>

      .. _ansible_collections.juniper.apstra.connectivity_template_assignment_module__parameter-api_url:

      .. rst-class:: ansible-option-title

      **api_url**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-api_url" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The URL used to access the Apstra api.


      .. rst-class:: ansible-option-line

      :ansible-option-default-bold:`Default:` :ansible-option-default:`"APSTRA\_API\_URL environment variable"`

      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-application_point_ids"></div>

      .. _ansible_collections.juniper.apstra.connectivity_template_assignment_module__parameter-application_point_ids:

      .. rst-class:: ansible-option-title

      **application_point_ids**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-application_point_ids" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`list` / :ansible-option-elements:`elements=string` / :ansible-option-required:`required`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      A list of interface node IDs to assign the CT to (when state is present) or unassign from (when state is absent).

      These are the graph node IDs of interfaces in the blueprint, obtainable from the application\-points API or from graph queries.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-auth_token"></div>

      .. _ansible_collections.juniper.apstra.connectivity_template_assignment_module__parameter-auth_token:

      .. rst-class:: ansible-option-title

      **auth_token**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-auth_token" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The authentication token to use if already authenticated.


      .. rst-class:: ansible-option-line

      :ansible-option-default-bold:`Default:` :ansible-option-default:`"APSTRA\_AUTH\_TOKEN environment variable"`

      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-blueprint_id"></div>

      .. _ansible_collections.juniper.apstra.connectivity_template_assignment_module__parameter-blueprint_id:

      .. rst-class:: ansible-option-title

      **blueprint_id**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-blueprint_id" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string` / :ansible-option-required:`required`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The ID of the Apstra blueprint.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-ct_id"></div>

      .. _ansible_collections.juniper.apstra.connectivity_template_assignment_module__parameter-ct_id:

      .. rst-class:: ansible-option-title

      **ct_id**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-ct_id" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The UUID of the Connectivity Template to assign.

      Either :literal:`ct\_id` or :literal:`ct\_name` must be provided.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-ct_name"></div>

      .. _ansible_collections.juniper.apstra.connectivity_template_assignment_module__parameter-ct_name:

      .. rst-class:: ansible-option-title

      **ct_name**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-ct_name" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The name (label) of the Connectivity Template to assign.

      Used to look up the CT when :literal:`ct\_id` is not provided.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-password"></div>

      .. _ansible_collections.juniper.apstra.connectivity_template_assignment_module__parameter-password:

      .. rst-class:: ansible-option-title

      **password**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-password" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The password for authentication.


      .. rst-class:: ansible-option-line

      :ansible-option-default-bold:`Default:` :ansible-option-default:`"APSTRA\_PASSWORD environment variable"`

      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-state"></div>

      .. _ansible_collections.juniper.apstra.connectivity_template_assignment_module__parameter-state:

      .. rst-class:: ansible-option-title

      **state**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-state" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      Desired state of the CT assignments.

      :literal:`present` assigns the CT to the listed application points.

      :literal:`absent` unassigns the CT from the listed application points.


      .. rst-class:: ansible-option-line

      :ansible-option-choices:`Choices:`

      - :ansible-option-choices-entry-default:`"present"` :ansible-option-choices-default-mark:`← (default)`
      - :ansible-option-choices-entry:`"absent"`


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-username"></div>

      .. _ansible_collections.juniper.apstra.connectivity_template_assignment_module__parameter-username:

      .. rst-class:: ansible-option-title

      **username**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-username" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The username for authentication.


      .. rst-class:: ansible-option-line

      :ansible-option-default-bold:`Default:` :ansible-option-default:`"APSTRA\_USERNAME environment variable"`

      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-verify_certificates"></div>

      .. _ansible_collections.juniper.apstra.connectivity_template_assignment_module__parameter-verify_certificates:

      .. rst-class:: ansible-option-title

      **verify_certificates**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-verify_certificates" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`boolean`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      If set to false, SSL certificates will not be verified.


      .. rst-class:: ansible-option-line

      :ansible-option-choices:`Choices:`

      - :ansible-option-choices-entry:`false`
      - :ansible-option-choices-entry-default:`true` :ansible-option-choices-default-mark:`← (default)`


      .. raw:: html

        </div>


.. Attributes


.. Notes


.. Seealso


.. Examples

Examples
--------

.. code-block:: yaml+jinja

    # ── Assign by CT ID ──────────────────────────────────────────────────

    # Assign a CT to a single interface by CT ID
    - name: Assign CT to one interface
      juniper.apstra.connectivity_template_assignment:
        blueprint_id: "{{ blueprint_id }}"
        ct_id: "{{ ct_id }}"
        application_point_ids:
          - "{{ interface_id }}"
        state: present

    # Assign a CT to multiple interfaces at once (bulk)
    - name: Assign CT to multiple interfaces
      juniper.apstra.connectivity_template_assignment:
        blueprint_id: "{{ blueprint_id }}"
        ct_id: "{{ ct_id }}"
        application_point_ids:
          - "G31G9dCSVcDS9PoeYg"
          - "x2LgjvQJTCNdPBQL9A"
          - "Hk9PqW3mTfNcRbYx1Z"
        state: present

    # ── Assign by CT name ────────────────────────────────────────────────

    # Assign a CT by name lookup (no need to know the CT UUID)
    - name: Assign BGP-2-SRX CT to interfaces
      juniper.apstra.connectivity_template_assignment:
        blueprint_id: "{{ blueprint_id }}"
        ct_name: "BGP-2-SRX"
        application_point_ids:
          - "{{ interface_id }}"
        state: present

    # ── Using registered output from connectivity_template ───────────────

    # First create the CT, then assign it in a follow-up task
    - name: Create the CT
      juniper.apstra.connectivity_template:
        blueprint_id: "{{ blueprint_id }}"
        name: "VLAN-100-Access"
        type: interface
        primitives:
          virtual_network_singles:
            vlan100:
              vn_node_id: "{{ virtual_network_id }}"
        state: present
      register: ct_result

    - name: Assign the CT using registered output
      juniper.apstra.connectivity_template_assignment:
        blueprint_id: "{{ blueprint_id }}"
        ct_id: "{{ ct_result.ct_id }}"
        application_point_ids:
          - "{{ interface_id_1 }}"
          - "{{ interface_id_2 }}"
        state: present

    # ── Unassign (remove) CT from interfaces ─────────────────────────────

    # Unassign a CT from specific interfaces by CT ID
    - name: Unassign CT from interfaces
      juniper.apstra.connectivity_template_assignment:
        blueprint_id: "{{ blueprint_id }}"
        ct_id: "{{ ct_id }}"
        application_point_ids:
          - "G31G9dCSVcDS9PoeYg"
        state: absent

    # Unassign a CT by name
    - name: Unassign CT from interfaces by name
      juniper.apstra.connectivity_template_assignment:
        blueprint_id: "{{ blueprint_id }}"
        ct_name: "BGP-2-SRX"
        application_point_ids:
          - "{{ interface_id }}"
        state: absent

    # ── Idempotent re-run ────────────────────────────────────────────────

    # Running the same assign again produces changed=false
    - name: Assign CT (idempotent — no change on second run)
      juniper.apstra.connectivity_template_assignment:
        blueprint_id: "{{ blueprint_id }}"
        ct_name: "VLAN-100-Access"
        application_point_ids:
          - "{{ interface_id }}"
        state: present



.. Facts


.. Return values

Return Values
-------------
Common return values are documented :ref:`here <common_return_values>`, the following are the fields unique to this module:

.. tabularcolumns:: \X{1}{3}\X{2}{3}

.. list-table::
  :width: 100%
  :widths: auto
  :header-rows: 1
  :class: longtable ansible-option-table

  * - Key
    - Description

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="return-applied"></div>

      .. _ansible_collections.juniper.apstra.connectivity_template_assignment_module__return-applied:

      .. rst-class:: ansible-option-title

      **applied**

      .. raw:: html

        <a class="ansibleOptionLink" href="#return-applied" title="Permalink to this return value"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`list` / :ansible-option-elements:`elements=string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      List of interface IDs that were newly assigned.


      .. rst-class:: ansible-option-line

      :ansible-option-returned-bold:`Returned:` when state is present and changes are made


      .. raw:: html

        </div>


  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="return-changed"></div>

      .. _ansible_collections.juniper.apstra.connectivity_template_assignment_module__return-changed:

      .. rst-class:: ansible-option-title

      **changed**

      .. raw:: html

        <a class="ansibleOptionLink" href="#return-changed" title="Permalink to this return value"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`boolean`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      Indicates whether the module has made any changes.


      .. rst-class:: ansible-option-line

      :ansible-option-returned-bold:`Returned:` always


      .. raw:: html

        </div>


  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="return-msg"></div>

      .. _ansible_collections.juniper.apstra.connectivity_template_assignment_module__return-msg:

      .. rst-class:: ansible-option-title

      **msg**

      .. raw:: html

        <a class="ansibleOptionLink" href="#return-msg" title="Permalink to this return value"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The output message that the module generates.


      .. rst-class:: ansible-option-line

      :ansible-option-returned-bold:`Returned:` always


      .. raw:: html

        </div>


  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="return-unapplied"></div>

      .. _ansible_collections.juniper.apstra.connectivity_template_assignment_module__return-unapplied:

      .. rst-class:: ansible-option-title

      **unapplied**

      .. raw:: html

        <a class="ansibleOptionLink" href="#return-unapplied" title="Permalink to this return value"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`list` / :ansible-option-elements:`elements=string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      List of interface IDs that were newly unassigned.


      .. rst-class:: ansible-option-line

      :ansible-option-returned-bold:`Returned:` when state is absent and changes are made


      .. raw:: html

        </div>



..  Status (Presently only deprecated)


.. Authors

Authors
~~~~~~~

- Juniper Networks


.. Extra links

Collection links
~~~~~~~~~~~~~~~~

.. ansible-links::

  - title: "Issue Tracker"
    url: "https://github.com/Juniper/apstra-ansible-collection/issues"
    external: true
  - title: "Homepage"
    url: "https://www.juniper.net/us/en/products/network-automation/apstra.html"
    external: true
  - title: "Repository (Sources)"
    url: "https://github.com/Juniper/apstra-ansible-collection"
    external: true


.. Parsing errors
