![Juniper Networks](https://juniper-prod.scene7.com/is/image/junipernetworks/juniper_black-rgb-header?wid=320&dpr=off)

# Juniper Networks Apstra Ansible Collection

This repository contains the Juniper Apstra Ansible Collection, which provides a set of Ansible modules and roles for network management via the Juniper Apstra platform.

This collection has been validated on Juniper Apstra version 5.0 and later (SDK 6.1.0).

## Support

As a Red Hat Ansible [Certified Content](https://catalog.redhat.com/software/search?target_platforms=Red%20Hat%20Ansible%20Automation%20Platform), this collection is entitled to [support](https://access.redhat.com/support/) through [Ansible Automation Platform](https://www.redhat.com/en/technologies/management/ansible) (AAP).

If a support case cannot be opened with Red Hat and the collection has been obtained either from [Galaxy](https://galaxy.ansible.com/ui/) or [GitHub](https://github.com/Juniper/apstra-ansible-collection/issues), there is community support available at no charge.

You can join us on [#network:ansible.com](https://matrix.to/#/#network:ansible.com) room or the [Ansible Forum Network Working Group](https://forum.ansible.com/g/network-wg).

For more information you can check the communication section below.

## Communication

* Join the Ansible forum:
  * [Get Help](https://forum.ansible.com/c/help/6): get help or help others.
  * [Posts tagged with 'juniper'](https://forum.ansible.com/tag/juniper): subscribe to participate in collection-related conversations.
  * [Ansible Network Automation Working Group](https://forum.ansible.com/g/network-wg/): by joining the team you will automatically get subscribed to the posts tagged with [network](https://forum.ansible.com/tags/network).
  * [Social Spaces](https://forum.ansible.com/c/chat/4): gather and interact with fellow enthusiasts.
  * [News & Announcements](https://forum.ansible.com/c/news/5): track project-wide announcements including social events.

* The Ansible [Bullhorn newsletter](https://docs.ansible.com/ansible/devel/community/communication.html#the-bullhorn): used to announce releases and important changes.

For more information about communication, see the [Ansible communication guide](https://docs.ansible.com/ansible/devel/community/communication.html).

## Ansible version compatibility

This collection has been tested against following Ansible versions: **>=2.16.14**.

## Included Content

### Modules
Name | Description
--- | ---
[juniper.apstra.apstra_facts](https://github.com/Juniper/apstra-ansible-collection/blob/main/ansible_collections/juniper/apstra/docs/apstra_facts_module.rst) | Gather facts from Apstra (blueprints, virtual networks, security zones, endpoint policies, resource pools, and more). Use `gather_network_facts: all` or pass a filtered list of object types.
[juniper.apstra.authenticate](https://github.com/Juniper/apstra-ansible-collection/blob/main/ansible_collections/juniper/apstra/docs/authenticate_module.rst) | Log in to Apstra and retrieve a session token for use by subsequent modules. Also supports explicit logout.
[juniper.apstra.blueprint](https://github.com/Juniper/apstra-ansible-collection/blob/main/ansible_collections/juniper/apstra/docs/blueprint_module.rst) | Full lifecycle management of Apstra blueprints — create, commit, lock/unlock, and delete. Supports graph queries (`state: queried`) and per-node property patches (`state: node_updated`). Uses a tag-based mutex to prevent concurrent modifications.
[juniper.apstra.configlets](https://github.com/Juniper/apstra-ansible-collection/blob/main/ansible_collections/juniper/apstra/docs/configlets_module.rst) | Create, update, and delete configlets in Apstra. Supports global catalog configlets and blueprint-scoped configlets with role-based targeting conditions.
[juniper.apstra.connectivity_template](https://github.com/Juniper/apstra-ansible-collection/blob/main/ansible_collections/juniper/apstra/docs/connectivity_template_module.rst) | Create, update, and delete Connectivity Templates (CTs) in an Apstra blueprint. CTs are composed of network primitives (IP Link, BGP Peering, Routing Policy, etc.) and target an application point type (`interface`, `svi`, `loopback`, etc.). Idempotent by name.
[juniper.apstra.connectivity_template_assignment](https://github.com/Juniper/apstra-ansible-collection/blob/main/ansible_collections/juniper/apstra/docs/connectivity_template_assignment_module.rst) | Assign or unassign Connectivity Templates to application point nodes (interfaces) within an Apstra blueprint.
[juniper.apstra.design](https://github.com/Juniper/apstra-ansible-collection/blob/main/ansible_collections/juniper/apstra/docs/blueprint_module.rst) | Create and manage design-layer objects (logical devices, rack types, templates) required before blueprint creation.
[juniper.apstra.endpoint_policy](https://github.com/Juniper/apstra-ansible-collection/blob/main/ansible_collections/juniper/apstra/docs/endpoint_policy_module.rst) | Create, update, and delete endpoint policies and their application points within an Apstra blueprint.
[juniper.apstra.external_gateway](https://github.com/Juniper/apstra-ansible-collection/blob/main/ansible_collections/juniper/apstra/docs/external_gateway_module.rst) | Create, update, and delete external EVPN remote gateways in an Apstra blueprint for inter-DC or WAN BGP/L2VPN peering.
[juniper.apstra.fabric_settings](https://github.com/Juniper/apstra-ansible-collection/blob/main/ansible_collections/juniper/apstra/docs/blueprint_module.rst) | Manage fabric-wide settings in an Apstra blueprint (MTU, EVPN parameters, overlay protocol, anti-affinity, SVI/anycast defaults).
[juniper.apstra.generic_systems](https://github.com/Juniper/apstra-ansible-collection/blob/main/ansible_collections/juniper/apstra/docs/generic_systems_module.rst) | Create, update, and delete generic (external) systems in an Apstra blueprint, including their links to fabric switches (LAG mode, speed, port assignments).
[juniper.apstra.interface_map](https://github.com/Juniper/apstra-ansible-collection/blob/main/ansible_collections/juniper/apstra/docs/blueprint_module.rst) | Assign interface maps to blueprint switch nodes, linking them to device profiles that define physical port layout and naming.
[juniper.apstra.property_set](https://github.com/Juniper/apstra-ansible-collection/blob/main/ansible_collections/juniper/apstra/docs/property_set_module.rst) | Create, update, and delete property sets (key-value stores). Supports both global catalog scope and blueprint scope.
[juniper.apstra.resource_group](https://github.com/Juniper/apstra-ansible-collection/blob/main/ansible_collections/juniper/apstra/docs/resource_group_module.rst) | Assign global resource pools (ASN, IP, IPv6, VLAN, VNI) to named resource groups within an Apstra blueprint.
[juniper.apstra.resource_pools](https://github.com/Juniper/apstra-ansible-collection/blob/main/ansible_collections/juniper/apstra/docs/resource_pools_module.rst) | Create, update, and delete global resource pools in Apstra. Supported types: ASN, Integer, IP, IPv6, VLAN, and VNI.
[juniper.apstra.routing_policy](https://github.com/Juniper/apstra-ansible-collection/blob/main/ansible_collections/juniper/apstra/docs/routing_policy_module.rst) | Create, update, and delete routing policies in an Apstra blueprint (BGP import/export filters, aggregate prefixes, extra routes).
[juniper.apstra.security_zone](https://github.com/Juniper/apstra-ansible-collection/blob/main/ansible_collections/juniper/apstra/docs/security_zone_module.rst) | Create, update, and delete security zones (VRFs) in an Apstra blueprint, including VNI ID, DHCP relay, and routing policy association.
[juniper.apstra.system_agents](https://github.com/Juniper/apstra-ansible-collection/blob/main/ansible_collections/juniper/apstra/docs/blueprint_module.rst) | Onboard, update, and delete NOS system agents in Apstra to connect physical devices to the management plane.
[juniper.apstra.tag](https://github.com/Juniper/apstra-ansible-collection/blob/main/ansible_collections/juniper/apstra/docs/tag_module.rst) | Create, update, and delete tags in Apstra. Tags can be applied to blueprint objects and used as configlet targeting selectors.
[juniper.apstra.virtual_network](https://github.com/Juniper/apstra-ansible-collection/blob/main/ansible_collections/juniper/apstra/docs/virtual_network_module.rst) | Create, update, and delete virtual networks (VXLAN/VLAN) in an Apstra blueprint. Configures VN type, VNI ID, IPv4/IPv6 gateways, DHCP, and security zone binding. Supports lookup by label.

Click the `Content` button to see the list of content included in this collection.

## Installation

You can install the Juniper Networks Apstra collection with the Ansible Galaxy CLI:

```shell
ansible-galaxy collection install juniper.apstra
```

You can also include it in a `requirements.yml` file and install it with `ansible-galaxy collection install -r requirements.yml`, using the format:

```yaml
---
collections:
  - name: juniper.apstra
```

You can ensure that the [required packages](https://github.com/Juniper/apstra-ansible-collection/blob/main/ansible_collections/juniper/apstra/requirements.txt) are installed via pip. For example, if your collection is installed in the default location:

```shell
pip install -r ~/.ansible/collections/ansible_collections/juniper/apstra/requirements.txt
```

## Usage

You can call modules by their Fully Qualified Collection Namespace (FQCN), such as `juniper.apstra.authenticate`.
The following example plays show how to log in to Apstra, create a blueprint and gather facts.

The collection is simply an Ansible interface to specific Apstra API. This is why

### Login

```yaml
- name: Connect to Apstra
  juniper.apstra.authenticate:
    api_url: "https://my-apstra/api"
    username: "admin"
    password: "password"
    logout: false
  register: auth
```

### Gather facts

```yaml
- name: Run apstra_facts module
  juniper.apstra.apstra_facts:
    gather_network_facts: 'all'
    available_network_facts: true
    auth_token: "{{ auth.token }}"
  register: apstra_facts
```

### Create blueprint

```yaml
- name: Create/get blueprint
  juniper.apstra.blueprint:
    body:
      label: "test_blueprint"
      design: "two_stage_l3clos"
    lock_state: "locked"
    auth_token: "{{ auth.token }}"
  register: bp
```


## Contributing to this collection

We welcome community contributions to this collection. If you find problems, please open an issue or create a PR against the [Juniper Networks Apstra collection repository](https://github.com/Juniper/apstra-ansible-collection). See [Contributing to Ansible-maintained collections](https://docs.ansible.com/ansible/devel/community/contributing_maintained_collections.html#contributing-maintained-collections) for complete details.

You can also join us on:

- IRC - the `#ansible-network` [irc.libera.chat](https://libera.chat/) channel
- Slack - https://ansiblenetwork.slack.com

See the [Ansible Community Guide](https://docs.ansible.com/ansible/latest/community/index.html) for details on contributing to Ansible.

### Code of Conduct

This collection follows the Ansible project's
[Code of Conduct](https://docs.ansible.com/ansible/devel/community/code_of_conduct.html).
Please read and familiarize yourself with this document.

## Release Notes

Release notes are available [here](https://github.com/Juniper/apstra-ansible-collection/blob/main/ansible_collections/juniper/apstra/CHANGELOG.rst).

## Roadmap

- Expand coverage of Apstra freeform blueprint resources.
- Add support for additional design-level objects (rack types, interface groups).
- Provide idempotent management of system agent profiles.
- Improve diff output to surface per-field change details for all modules.
- Publish dedicated documentation pages for `design`, `fabric_settings`, `interface_map`, and `system_agents` modules.

## More Information

- [Ansible network resources](https://docs.ansible.com/ansible/latest/network/getting_started/network_resources.html)
- [Ansible Collection overview](https://github.com/ansible-collections/overview)
- [Ansible User guide](https://docs.ansible.com/ansible/latest/user_guide/index.html)
- [Ansible Developer guide](https://docs.ansible.com/ansible/latest/dev_guide/index.html)
- [Ansible Community code of conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html)

## Licensing

This collection is available under multiple licenses depending on the component. See [LICENSE](https://github.com/Juniper/apstra-ansible-collection/blob/main/LICENSE) for the full text.

Primary license: **Apache-2.0**. Additional licenses used in this project: MIT, GPL-3.0-or-later, BSD-3-Clause.
