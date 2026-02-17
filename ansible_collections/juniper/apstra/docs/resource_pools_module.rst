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
- Supported pool types are ASN, Integer, IP, IPv6, VLAN, and VNI.

Parameters
----------

**api_url** (string): The URL used to access the Apstra api. Default: APSTRA_API_URL environment variable

**auth_token** (string): The authentication token to use if already authenticated. Default: APSTRA_AUTH_TOKEN environment variable

**body** (dictionary): Dictionary containing the resource pool details. For ASN pools use ``ranges`` with ``first``/``last`` integer keys. For Integer pools use ``ranges`` with ``first``/``last`` integer keys. For IP pools use ``subnets`` with ``network`` (CIDR notation) keys. For IPv6 pools use ``subnets`` with ``network`` (IPv6 CIDR notation) keys. For VLAN pools use ``ranges`` with ``first``/``last`` integer keys. For VNI pools use ``ranges`` with ``first``/``last`` integer keys.

**id** (dictionary): Dictionary containing the resource pool ID.

**password** (string): The password for authentication. Default: APSTRA_PASSWORD environment variable

**state** (string): Desired state of the resource pool. Choices: present, absent. Default: present

**type** (string): The type of resource pool to manage. Choices: asn, integer, ip, ipv6, vlan, vni. Default: asn

**username** (string): The username for authentication. Default: APSTRA_USERNAME environment variable

**verify_certificates** (boolean): If set to false, SSL certificates will not be verified. Default: True

Examples
--------

Prerequisite: Discover Resource Groups
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before assigning pools to a blueprint, discover the available resource groups:

.. code-block:: yaml+jinja

    - name: Get resource groups from blueprint
      ansible.builtin.uri:
        url: "{{ apstra_api_url }}/blueprints/{{ blueprint_id }}/resource_groups"
        method: GET
        headers:
          AuthToken: "{{ auth_token }}"
        validate_certs: false
        status_code: 200
      register: resource_groups

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
      register: asn_pool

    - name: Show ASN pool total and used_percentage
      ansible.builtin.debug:
        msg: "ASN Pool {{ item.key }} - total: {{ item.value.total }}, used_percentage: {{ item.value.used_percentage }}"
      loop: "{{ ansible_facts.apstra_facts.asn_pools | dict2items }}"
      loop_control:
        label: "{{ item.key }}"

    - name: Find ASN resource group in blueprint
      ansible.builtin.set_fact:
        asn_resource_group: >-
          {{ resource_groups.json.items
             | selectattr('resource_type', 'equalto', 'asn')
             | first }}

    - name: Assign ASN pool to blueprint
      ansible.builtin.uri:
        url: "{{ apstra_api_url }}/blueprints/{{ blueprint_id }}/resource_groups/asn/{{ asn_resource_group.group_name }}"
        method: PUT
        headers:
          AuthToken: "{{ auth_token }}"
          Content-Type: "application/json"
        body_format: json
        body:
          pool_ids:
            - "{{ asn_pool.id.asn_pool }}"
        validate_certs: false
        status_code: [200, 202, 204]

    - name: Verify ASN pool is assigned to blueprint
      ansible.builtin.uri:
        url: "{{ apstra_api_url }}/blueprints/{{ blueprint_id }}/resource_groups/asn/{{ asn_resource_group.group_name }}"
        method: GET
        headers:
          AuthToken: "{{ auth_token }}"
        validate_certs: false
        status_code: 200
      register: asn_assignment

    - name: Update an ASN pool
      juniper.apstra.resource_pools:
        type: asn
        id:
          asn_pool: "{{ asn_pool.id.asn_pool }}"
        body:
          display_name: "Updated-Production-ASN-Pool"
          ranges:
            - first: 65000
              last: 65200
        state: present

    - name: Unassign ASN pool from blueprint
      ansible.builtin.uri:
        url: "{{ apstra_api_url }}/blueprints/{{ blueprint_id }}/resource_groups/asn/{{ asn_resource_group.group_name }}"
        method: PUT
        headers:
          AuthToken: "{{ auth_token }}"
          Content-Type: "application/json"
        body_format: json
        body:
          pool_ids: []
        validate_certs: false
        status_code: [200, 202, 204]

    - name: Delete an ASN pool
      juniper.apstra.resource_pools:
        type: asn
        id:
          asn_pool: "{{ asn_pool.id.asn_pool }}"
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
      register: ip_pool

    - name: Show IP pool total and used_percentage
      ansible.builtin.debug:
        msg: "IP Pool {{ item.key }} - total: {{ item.value.total }}, used_percentage: {{ item.value.used_percentage }}"
      loop: "{{ ansible_facts.apstra_facts.ip_pools | dict2items }}"
      loop_control:
        label: "{{ item.key }}"

    - name: Find IP resource group in blueprint
      ansible.builtin.set_fact:
        ip_resource_group: >-
          {{ resource_groups.json.items
             | selectattr('resource_type', 'equalto', 'ip')
             | first }}

    - name: Assign IP pool to blueprint
      ansible.builtin.uri:
        url: "{{ apstra_api_url }}/blueprints/{{ blueprint_id }}/resource_groups/ip/{{ ip_resource_group.group_name }}"
        method: PUT
        headers:
          AuthToken: "{{ auth_token }}"
          Content-Type: "application/json"
        body_format: json
        body:
          pool_ids:
            - "{{ ip_pool.id.ip_pool }}"
        validate_certs: false
        status_code: [200, 202, 204]

    - name: Update an IP pool
      juniper.apstra.resource_pools:
        type: ip
        id:
          ip_pool: "{{ ip_pool.id.ip_pool }}"
        body:
          display_name: "Updated-Production-IP-Pool"
          subnets:
            - network: "10.100.0.0/16"
            - network: "10.200.0.0/16"
        state: present

    - name: Unassign IP pool from blueprint
      ansible.builtin.uri:
        url: "{{ apstra_api_url }}/blueprints/{{ blueprint_id }}/resource_groups/ip/{{ ip_resource_group.group_name }}"
        method: PUT
        headers:
          AuthToken: "{{ auth_token }}"
          Content-Type: "application/json"
        body_format: json
        body:
          pool_ids: []
        validate_certs: false
        status_code: [200, 202, 204]

    - name: Delete an IP pool
      juniper.apstra.resource_pools:
        type: ip
        id:
          ip_pool: "{{ ip_pool.id.ip_pool }}"
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
      register: vlan_pool

    - name: Show VLAN pool total and used_percentage
      ansible.builtin.debug:
        msg: "VLAN Pool {{ item.key }} - total: {{ item.value.total }}, used_percentage: {{ item.value.used_percentage }}"
      loop: "{{ ansible_facts.apstra_facts.vlan_pools | dict2items }}"
      loop_control:
        label: "{{ item.key }}"

    - name: Find VLAN resource group in blueprint
      ansible.builtin.set_fact:
        vlan_resource_group: >-
          {{ resource_groups.json.items
             | selectattr('resource_type', 'equalto', 'vlan')
             | first }}

    - name: Assign VLAN pool to blueprint
      ansible.builtin.uri:
        url: "{{ apstra_api_url }}/blueprints/{{ blueprint_id }}/resource_groups/vlan/{{ vlan_resource_group.group_name }}"
        method: PUT
        headers:
          AuthToken: "{{ auth_token }}"
          Content-Type: "application/json"
        body_format: json
        body:
          pool_ids:
            - "{{ vlan_pool.id.vlan_pool }}"
        validate_certs: false
        status_code: [200, 202, 204]

    - name: Update a VLAN pool
      juniper.apstra.resource_pools:
        type: vlan
        id:
          vlan_pool: "{{ vlan_pool.id.vlan_pool }}"
        body:
          display_name: "Updated-Production-VLAN-Pool"
          ranges:
            - first: 100
              last: 300
        state: present

    - name: Unassign VLAN pool from blueprint
      ansible.builtin.uri:
        url: "{{ apstra_api_url }}/blueprints/{{ blueprint_id }}/resource_groups/vlan/{{ vlan_resource_group.group_name }}"
        method: PUT
        headers:
          AuthToken: "{{ auth_token }}"
          Content-Type: "application/json"
        body_format: json
        body:
          pool_ids: []
        validate_certs: false
        status_code: [200, 202, 204]

    - name: Delete a VLAN pool
      juniper.apstra.resource_pools:
        type: vlan
        id:
          vlan_pool: "{{ vlan_pool.id.vlan_pool }}"
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
      register: ipv6_pool

    - name: Show IPv6 pool total and used_percentage
      ansible.builtin.debug:
        msg: "IPv6 Pool {{ item.key }} - total: {{ item.value.total }}, used_percentage: {{ item.value.used_percentage }}"
      loop: "{{ ansible_facts.apstra_facts.ipv6_pools | dict2items }}"
      loop_control:
        label: "{{ item.key }}"

    - name: Find IPv6 resource group in blueprint
      ansible.builtin.set_fact:
        ipv6_resource_group: >-
          {{ resource_groups.json.items
             | selectattr('resource_type', 'equalto', 'ipv6')
             | first }}

    - name: Assign IPv6 pool to blueprint
      ansible.builtin.uri:
        url: "{{ apstra_api_url }}/blueprints/{{ blueprint_id }}/resource_groups/ipv6/{{ ipv6_resource_group.group_name }}"
        method: PUT
        headers:
          AuthToken: "{{ auth_token }}"
          Content-Type: "application/json"
        body_format: json
        body:
          pool_ids:
            - "{{ ipv6_pool.id.ipv6_pool }}"
        validate_certs: false
        status_code: [200, 202, 204]

    - name: Update an IPv6 pool
      juniper.apstra.resource_pools:
        type: ipv6
        id:
          ipv6_pool: "{{ ipv6_pool.id.ipv6_pool }}"
        body:
          display_name: "Updated-Production-IPv6-Pool"
          subnets:
            - network: "fc01:a05:fab::/48"
            - network: "fc01:a05:fac::/48"
        state: present

    - name: Unassign IPv6 pool from blueprint
      ansible.builtin.uri:
        url: "{{ apstra_api_url }}/blueprints/{{ blueprint_id }}/resource_groups/ipv6/{{ ipv6_resource_group.group_name }}"
        method: PUT
        headers:
          AuthToken: "{{ auth_token }}"
          Content-Type: "application/json"
        body_format: json
        body:
          pool_ids: []
        validate_certs: false
        status_code: [200, 202, 204]

    - name: Delete an IPv6 pool
      juniper.apstra.resource_pools:
        type: ipv6
        id:
          ipv6_pool: "{{ ipv6_pool.id.ipv6_pool }}"
        state: absent

Integer Pool
~~~~~~~~~~~~

.. code-block:: yaml+jinja

    - name: Create an Integer pool
      juniper.apstra.resource_pools:
        type: integer
        body:
          display_name: "Production-Integer-Pool"
          ranges:
            - first: 1000
              last: 2000
        state: present
      register: integer_pool

    - name: Show Integer pool total and used_percentage
      ansible.builtin.debug:
        msg: "Integer Pool {{ item.key }} - total: {{ item.value.total }}, used_percentage: {{ item.value.used_percentage }}"
      loop: "{{ ansible_facts.apstra_facts.integer_pools | dict2items }}"
      loop_control:
        label: "{{ item.key }}"

    - name: Update an Integer pool
      juniper.apstra.resource_pools:
        type: integer
        id:
          integer_pool: "{{ integer_pool.id.integer_pool }}"
        body:
          display_name: "Updated-Production-Integer-Pool"
          ranges:
            - first: 1000
              last: 2000
            - first: 3000
              last: 4000
        state: present

    - name: Delete an Integer pool
      juniper.apstra.resource_pools:
        type: integer
        id:
          integer_pool: "{{ integer_pool.id.integer_pool }}"
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
      register: vni_pool

    - name: Show VNI pool total and used_percentage
      ansible.builtin.debug:
        msg: "VNI Pool {{ item.key }} - total: {{ item.value.total }}, used_percentage: {{ item.value.used_percentage }}"
      loop: "{{ ansible_facts.apstra_facts.vni_pools | dict2items }}"
      loop_control:
        label: "{{ item.key }}"

    - name: Find VNI resource group in blueprint
      ansible.builtin.set_fact:
        vni_resource_group: >-
          {{ resource_groups.json.items
             | selectattr('resource_type', 'equalto', 'vni')
             | first }}

    - name: Assign VNI pool to blueprint
      ansible.builtin.uri:
        url: "{{ apstra_api_url }}/blueprints/{{ blueprint_id }}/resource_groups/vni/{{ vni_resource_group.group_name }}"
        method: PUT
        headers:
          AuthToken: "{{ auth_token }}"
          Content-Type: "application/json"
        body_format: json
        body:
          pool_ids:
            - "{{ vni_pool.id.vni_pool }}"
        validate_certs: false
        status_code: [200, 202, 204]

    - name: Update a VNI pool
      juniper.apstra.resource_pools:
        type: vni
        id:
          vni_pool: "{{ vni_pool.id.vni_pool }}"
        body:
          display_name: "Updated-Production-VNI-Pool"
          ranges:
            - first: 5000
              last: 7000
        state: present

    - name: Unassign VNI pool from blueprint
      ansible.builtin.uri:
        url: "{{ apstra_api_url }}/blueprints/{{ blueprint_id }}/resource_groups/vni/{{ vni_resource_group.group_name }}"
        method: PUT
        headers:
          AuthToken: "{{ auth_token }}"
          Content-Type: "application/json"
        body_format: json
        body:
          pool_ids: []
        validate_certs: false
        status_code: [200, 202, 204]

    - name: Delete a VNI pool
      juniper.apstra.resource_pools:
        type: vni
        id:
          vni_pool: "{{ vni_pool.id.vni_pool }}"
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
