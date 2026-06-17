.. Document meta

:orphan:

.. |antsibull-internal-nbsp| unicode:: 0xA0
    :trim:

.. Anchors

.. _ansible_collections.juniper.apstra.blueprint_report_module:

.. Title

juniper.apstra.blueprint_report module -- Generate reports from Apstra blueprint data
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. Collection note

.. note::
    This module is part of the `juniper.apstra collection <https://galaxy.ansible.com/ui/repo/published/juniper/apstra/>`_.

    It is not included in ``ansible-core``.
    To check whether it is installed, run :code:`ansible-galaxy collection list`.

    To install it, use: :code:`ansible\-galaxy collection install juniper.apstra`.

    To use it in a playbook, specify: :code:`juniper.apstra.blueprint_report`.

.. version_added

.. rst-class:: ansible-version-added

New in juniper.apstra 1.0.9

.. contents::
   :local:
   :depth: 1


Synopsis
--------

.. Description

- This module generates reports from Apstra blueprint data by aggregating information from multiple sources including anomalies, build errors, IBA probes, device inventory, and configuration drift.
- Supports different report types — health, inventory, compliance, and full.
- Reports are returned as structured data and can optionally be saved to file.


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

      .. rst-class:: ansible-option-title

      **api_url**

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The URL used to access the Apstra api.

      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">

      .. rst-class:: ansible-option-title

      **auth_token**

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The authentication token to use if already authenticated.

      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">

      .. rst-class:: ansible-option-title

      **id**

      .. ansible-option-type-line::

        :ansible-option-type:`dictionary` / :ansible-option-required:`required`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      Dictionary containing the blueprint identifier. Must include ``blueprint`` key with a blueprint UUID or label.

      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">

      .. rst-class:: ansible-option-title

      **output_file**

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      Optional file path to save the report. Parent directories must already exist.

      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">

      .. rst-class:: ansible-option-title

      **output_format**

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      Format for the output file. Only used when ``output_file`` is specified.

      :Choices:

        - :ansible-option-choices-entry:`"json"` :ansible-option-choices-default-mark:`(default)`
        - :ansible-option-choices-entry:`"csv"`

      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">

      .. rst-class:: ansible-option-title

      **report_type**

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The type of report to generate.

      :Choices:

        - :ansible-option-choices-entry:`"health"` — anomalies, build errors, and IBA probe status
        - :ansible-option-choices-entry:`"inventory"` — device nodes and system information
        - :ansible-option-choices-entry:`"compliance"` — configuration drift and anomaly details
        - :ansible-option-choices-entry:`"full"` :ansible-option-choices-default-mark:`(default)` — all of the above combined

      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">

      .. rst-class:: ansible-option-title

      **username**

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The username for authentication.

      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">

      .. rst-class:: ansible-option-title

      **password**

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The password for authentication.

      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">

      .. rst-class:: ansible-option-title

      **verify_certificates**

      .. ansible-option-type-line::

        :ansible-option-type:`boolean`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      If set to false, SSL certificates will not be verified.

      :Default: ``true``

      .. raw:: html

        </div>


Examples
--------

.. code-block:: yaml+jinja

    # Generate a full report for a blueprint
    - name: Generate full blueprint report
      juniper.apstra.blueprint_report:
        id:
          blueprint: "my-blueprint"
        report_type: full
      register: report

    - name: Display report summary
      ansible.builtin.debug:
        var: report.report.summary

    # Generate a health report and save to file
    - name: Generate health report
      juniper.apstra.blueprint_report:
        id:
          blueprint: "5f2a77f6-1f33-4e11-8d59-6f9c26f16962"
        report_type: health
        output_file: "/tmp/health_report.json"
        output_format: json
        auth_token: "{{ auth.token }}"

    # Generate an inventory report
    - name: Generate inventory report
      juniper.apstra.blueprint_report:
        id:
          blueprint: "my-blueprint"
        report_type: inventory
        auth_token: "{{ auth.token }}"
      register: inventory

    - name: Show device count
      ansible.builtin.debug:
        msg: "Found {{ inventory.report.inventory.nodes | length }} nodes"

    # Generate a compliance report and export as CSV
    - name: Generate compliance report
      juniper.apstra.blueprint_report:
        id:
          blueprint: "my-blueprint"
        report_type: compliance
        output_file: "/tmp/compliance_report.csv"
        output_format: csv
        auth_token: "{{ auth.token }}"


Return Values
-------------

.. list-table::
  :width: 100%
  :widths: auto
  :header-rows: 1

  * - Key
    - Description

  * - .. raw:: html

        <div class="ansible-option-cell">

      .. rst-class:: ansible-option-title

      **changed**

      .. ansible-option-type-line::

        :ansible-option-type:`boolean`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      Always false — this module is read-only.

      :Returned: always

      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">

      .. rst-class:: ansible-option-title

      **report**

      .. ansible-option-type-line::

        :ansible-option-type:`dictionary`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The generated report data containing blueprint_id, blueprint_label, report_type, generated_at, summary, and section-specific data (health, inventory, compliance).

      :Returned: always

      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">

      .. rst-class:: ansible-option-title

      **output_file**

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      Path to the saved report file, if output_file was specified.

      :Returned: when output_file is specified

      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-cell">

      .. rst-class:: ansible-option-title

      **msg**

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The output message that the module generates.

      :Returned: always

      .. raw:: html

        </div>
