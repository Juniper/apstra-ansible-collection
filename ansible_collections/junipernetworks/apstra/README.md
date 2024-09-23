![Juniper Networks](https://juniper-prod.scene7.com/is/image/junipernetworks/juniper_black-rgb-header?wid=320&dpr=off)

# Juniper Apstra Ansible Collection

This repository contains the Juniper Apstra Ansible Collection, which provides a set of Ansible modules and roles for network management via the Juniper Apstra AOS platform.

## Installation

To install the Juniper Apstra Ansible Collection, you can use the following command:

```shell
ansible-galaxy collection install junipernetworks.apstra
```

## Usage

### Login

```yaml
- name: Connect to Apstra
  junipernetworks.apstra.authenticate:
    api_url: "https://my-apstra/api"
    username: "admin"
    password: "password"
    logout: false
  register: auth
```

### Create blueprint

```yaml
- name: Create blueprint
  junipernetworks.apstra.blueprint:
    body:
      label: "test_blueprint"
      design: "two_stage_l3clos"
    lock_state: "locked"
    auth_token: "{{ auth.token }}"
  register: bp
```

### Gather facts

```yaml
- name: Run apstra_facts module
  junipernetworks.apstra.apstra_facts:
    gather_network_facts: 'all'
    available_network_facts: true
    auth_token: "{{ auth.token }}"
  register: apstra_facts
```
