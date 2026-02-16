.. Document meta

:orphan:

.. Title

juniper.apstra.resource_pools module -- Manage resource pools in Apstra
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

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

- This module allows you to create, update, and delete resource pools in Apstra.
- Supported pool types are ASN, IP, IPv6, VLAN, and VNI.

Parameters
----------

**api_url** (string): The URL used to access the Apstra api. Default: APSTRA_API_URL environment variable

**auth_token** (string): The authentication token to use if already authenticated. Default: APSTRA_AUTH_TOKEN environment variable

**body** (dictionary): Dictionary containing the resource pool details. For ASN pools use ``ranges`` with ``first``/``last`` integer keys. For IP pools use ``subnets`` with ``network`` (CIDR notation) keys. For IPv6 pools use ``subnets`` with ``network`` (IPv6 CIDR notation) keys. For VLAN pools use ``ranges`` with ``first``/``last`` integer keys. For VNI pools use ``ranges`` with ``first``/``last`` integer keys.

**id** (dictionary): Dictionary containing the resource pool ID.

**password** (string): The password for authentication. Default: APSTRA_PASSWORD environment variable

**state** (string): Desired state of the resource pool. Choices: present, absent. Default: present

**type** (string): The type of resource pool to manage. Choices: asn, ip, ipv6, vlan, vni. Default: asn

**username** (string): The username for authentication. Default: APSTRA_USERNAME environment variable

**verify_certificates** (boolean): If set to false, SSL certificates will not be verified. Default: True

Examples
--------

ASN Pool
~~~~~~~~

.. code-block:: yaml+jinja

    - name: Create an ASN pool
      juniper.apstra.resource_pools:
        type: asn
        body:
          display_name: "Production-ASN-Pool"
          ranges:
            - first: 65000
              last: 65100
        state: present

    - name: Update an ASN pool
      juniper.apstra.resource_pools:
        type: asn
        id:
          asn_pool: "pool-uuid-here"
        body:
          display_name: "Updated-Production-ASN-Pool"
          ranges:
            - first: 65000
              last: 65200
        state: present

    - name: Delete an ASN pool
      juniper.apstra.resource_pools:
        type: asn
        id:
          asn_pool: "pool-uuid-here"
        state: absent

IP Pool
~~~~~~~

.. code-block:: yaml+jinja

    - name: Create an IP pool
      juniper.apstra.resource_pools:
        type: ip
        body:
          display_name: "Production-IP-Pool"
          subnets:
            - network: "10.100.0.0/16"
        state: present

    - name: Update an IP pool
      juniper.apstra.resource_pools:
        type: ip
        id:
          ip_pool: "pool-uuid-here"
        body:
          display_name: "Updated-Production-IP-Pool"
          subnets:
            - network: "10.100.0.0/16"
            - network: "10.200.0.0/16"
        state: present

    - name: Delete an IP pool
      juniper.apstra.resource_pools:
        type: ip
        id:
          ip_pool: "pool-uuid-here"
        state: absent

VLAN Pool
~~~~~~~~~

.. code-block:: yaml+jinja

    - name: Create a VLAN pool
      juniper.apstra.resource_pools:
        type: vlan
        body:
          display_name: "Production-VLAN-Pool"
          ranges:
            - first: 100
              last: 200
        state: present

    - name: Update a VLAN pool
      juniper.apstra.resource_pools:
        type: vlan
        id:
          vlan_pool: "pool-uuid-here"
        body:
          display_name: "Updated-Production-VLAN-Pool"
          ranges:
            - first: 100
              last: 300
        state: present

    - name: Delete a VLAN pool
      juniper.apstra.resource_pools:
        type: vlan
        id:
          vlan_pool: "pool-uuid-here"
        state: absent

IPv6 Pool
~~~~~~~~~

.. code-block:: yaml+jinja

    - name: Create an IPv6 pool
      juniper.apstra.resource_pools:
        type: ipv6
        body:
          display_name: "Production-IPv6-Pool"
          subnets:
            - network: "fc01:a05:fab::/48"
        state: present

    - name: Update an IPv6 pool
      juniper.apstra.resource_pools:
        type: ipv6
        id:
          ipv6_pool: "pool-uuid-here"
        body:
          display_name: "Updated-Production-IPv6-Pool"
          subnets:
            - network: "fc01:a05:fab::/48"
            - network: "fc01:a05:fac::/48"
        state: present

    - name: Delete an IPv6 pool
      juniper.apstra.resource_pools:
        type: ipv6
        id:
          ipv6_pool: "pool-uuid-here"
        state: absent

VNI Pool
~~~~~~~~

.. code-block:: yaml+jinja

    - name: Create a VNI pool
      juniper.apstra.resource_pools:
        type: vni
        body:
          display_name: "Production-VNI-Pool"
          ranges:
            - first: 5000
              last: 6000
        state: present

    - name: Update a VNI pool
      juniper.apstra.resource_pools:
        type: vni
        id:
          vni_pool: "pool-uuid-here"
        body:
          display_name: "Updated-Production-VNI-Pool"
          ranges:
            - first: 5000
              last: 7000
        state: present

    - name: Delete a VNI pool
      juniper.apstra.resource_pools:
        type: vni
        id:
          vni_pool: "pool-uuid-here"
        state: absent

Return Values
-------------

**changed** (boolean): Indicates whether the module made changes. Returned: always

**changes** (dictionary): Dictionary of applied updates. Returned: on update

**response** (dictionary): The resource pool details. Returned: when state is present and changes are made

**id** (dictionary): The ID of the resource pool. Returned: on create or when identified by display_name

**msg** (string): Output message from the module. Returned: always

Authors
~~~~~~~

- Prabhanjan KV (@kvp_jnpr)
