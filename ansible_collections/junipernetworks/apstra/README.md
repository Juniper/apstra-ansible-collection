![Juniper Networks](https://juniper-prod.scene7.com/is/image/junipernetworks/juniper_black-rgb-header?wid=320&dpr=off)

# Juniper Networks Apstra Ansible Collection

This repository contains the Juniper Apstra Ansible Collection, which provides a set of Ansible modules and roles for network management via the Juniper Apstra platform.

This collection has been validated on Juniper Apstra version 5.0.

## Support

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

This collection has been tested against following Ansible versions: **>=2.15**.

## Included Content

### Modules
Name | Description
--- | ---
[junipernetworks.apstra.apstra_facts](https://github.com/Juniper/apstra-ansible-collection/blob/main/ansible_collections/junipernetworks/apstra/docs/apstra_facts_module.rst) | Collect network facts from Apstra
[junipernetworks.apstra.authenticate](https://github.com/Juniper/apstra-ansible-collection/blob/main/ansible_collections/junipernetworks/apstra/docs/authenticate_module.rst) | Authenticate to Apstra API
[junipernetworks.apstra.blueprint](https://github.com/Juniper/apstra-ansible-collection/blob/main/ansible_collections/junipernetworks/apstra/docs/blueprint_module.rst) | Manage blueprints
[junipernetworks.apstra.endpoint_policy](https://github.com/Juniper/apstra-ansible-collection/blob/main/ansible_collections/junipernetworks/apstra/docs/endpoint_policy_module.rst) | Manage endpoint policies
[junipernetworks.apstra.resource_group](https://github.com/Juniper/apstra-ansible-collection/blob/main/ansible_collections/junipernetworks/apstra/docs/resource_group_module.rst) | Manage resource groups
[junipernetworks.apstra.routing_policy](https://github.com/Juniper/apstra-ansible-collection/blob/main/ansible_collections/junipernetworks/apstra/docs/routing_policy_module.rst) | Manage routing policies
[junipernetworks.apstra.security_zone](https://github.com/Juniper/apstra-ansible-collection/blob/main/ansible_collections/junipernetworks/apstra/docs/security_zone_module.rst) | Manage security zones
[junipernetworks.apstra.tag](https://github.com/Juniper/apstra-ansible-collection/blob/main/ansible_collections/junipernetworks/apstra/docs/tag_module.rst) | Manage tags
[junipernetworks.apstra.virtual_network](https://github.com/Juniper/apstra-ansible-collection/blob/main/ansible_collections/junipernetworks/apstra/docs/virtual_network_module.rst) | Manage virtual networks

Click the `Content` button to see the list of content included in this collection.

## Installation

You can install the Juniper Networks Apstr collection with the Ansible Galaxy CLI:

```shell
ansible-galaxy collection install junipernetworks.apstra
```

You can also include it in a `requirements.yml` file and install it with `ansible-galaxy collection install -r requirements.yml`, using the format:

```yaml
---
collections:
  - name: junipernetworks.apstra
```

You can ensure that the [required packages](https://github.com/Juniper/apstra-ansible-collection/blob/main/ansible_collections/junipernetworks/apstra/requirements.txt) are installed via pip. For example, if your collection is installed in the default location:

```shell
pip install -r ~/.ansible/collections/ansible_collections/junipernetworks/apstra/requirements.txt
```

## Usage

You can call modules by their Fully Qualified Collection Namespace (FQCN), such as `junipernetworks.apstra.authenticate`.
The following example plays show how to log in to Apstra, create a blueprint and gather facts.

The collection is simply an Ansible interface to specific Apstra API. This is why

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

### Gather facts

```yaml
- name: Run apstra_facts module
  junipernetworks.apstra.apstra_facts:
    gather_network_facts: 'all'
    available_network_facts: true
    auth_token: "{{ auth.token }}"
  register: apstra_facts
```

### Create blueprint

```yaml
- name: Create/get blueprint
  junipernetworks.apstra.blueprint:
    body:
      label: "test_blueprint"
      design: "two_stage_l3clos"
    lock_state: "locked"
    auth_token: "{{ auth.token }}"
  register: bp
```


## Contributing to this collection

We welcome community contributions to this collection. If you find problems, please open an issue or create a PR against the [Juniper Networks Apstr collection repository](https://github.com/Juniper/apstra-ansible-collection). See [Contributing to Ansible-maintained collections](https://docs.ansible.com/ansible/devel/community/contributing_maintained_collections.html#contributing-maintained-collections) for complete details.

You can also join us on:

- IRC - the `#ansible-network` [irc.libera.chat](https://libera.chat/) channel
- Slack - https://ansiblenetwork.slack.com

See the [Ansible Community Guide](https://docs.ansible.com/ansible/latest/community/index.html) for details on contributing to Ansible.

### Code of Conduct

This collection follows the Ansible project's
[Code of Conduct](https://docs.ansible.com/ansible/devel/community/code_of_conduct.html).
Please read and familiarize yourself with this document.

## Release Notes

Release notes are available [here](https://github.com/Juniper/apstra-ansible-collection/blob/main/ansible_collections/junipernetworks/apstra/CHANGELOG.rst).

## Roadmap

<!-- Optional. Include the roadmap for this collection, and the proposed release/versioning strategy so users can anticipate the upgrade/update cycle. -->

## More Information

- [Ansible network resources](https://docs.ansible.com/ansible/latest/network/getting_started/network_resources.html)
- [Ansible Collection overview](https://github.com/ansible-collections/overview)
- [Ansible User guide](https://docs.ansible.com/ansible/latest/user_guide/index.html)
- [Ansible Developer guide](https://docs.ansible.com/ansible/latest/dev_guide/index.html)
- [Ansible Community code of conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html)

## Licensing

GNU General Public License v3.0 or later.

See [LICENSE](https://www.gnu.org/licenses/gpl-3.0.txt) to see the full text.
