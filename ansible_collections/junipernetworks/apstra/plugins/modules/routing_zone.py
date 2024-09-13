#!/usr/bin/python

# Copyright: (c) 2020, Juniper Networks, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r'''
---
module: design

short_description: Manage routing zones in Apstra

version_added: "0.1.0"
author: "Pratik Dave (@pratikd)"

description: "This module will automate the management of routing zone in Apstra."

options:
    auth_token:
        description:
          - used to authenticate to the API
        required: true
        type: str
    blueprint_label:
        description:
          - name of the blueprint where the routing zone will be created
        required: true
        type: str
    routing_zone_name:
        description:
          - name of the routing zone to be created
        required: true
        type: str
    vni_id:
        description: 
          - VNI ID for the routing zone
        required: false
        type: int
        default: 100000
    vrf_type:
        description:
          - type of the routing zone
        required: false
        choices: ['evpn', 'l3_fabric']
        default: 'evpn'
    state:
        description:
            - declare whether you want the resource to exist or be deleted
        required: true
        choices:
          - 'absent'
          - 'present'
        type: str
    verify_certificates:
        description:
            - whether to verify the SSL certificates of the AOS server
        required: false
        default: true
        type: bool
'''

EXAMPLES = r'''
---

- name: Connect to Apstra and get the auth token
  junipernetworks.apstra.authenticate:
    logout: false
  register: auth_response

- name: Create VRF in bluprint name apstra
  junipernetworks.apstra.routing_zone:
    auth_token: "{{ auth_response.auth_token }}"
    blueprint_label: "apstra"
    routing_zone_name: "default3"
    verify_certificates: false
    state: present
  register: routing_zone_response

- name: Delete the VRF in blueprint name apstra-bp 
  junipernetworks.apstra.blueprint:
    auth_token: "{{ auth_response.auth_token }}"
    blueprint_label: "apstra-bp"
    routing_zone_name: "default3"
    state: absent
'''

RETURN = '''
changed:
    description: Indicates whether the module has made any changes
    type: bool
    returned: always
message:
    description: The output message that the this module generates
    type: str
    returned: always
'''

## Import AOS-SDK and other necessary modules
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.junipernetworks.apstra.plugins.module_utils.apstra.client import (
    apstra_client_module_args,
    ApstraClientFactory,
)
import urllib3
import json

urllib3.disable_warnings()

# variable result to return at the end of each play

result = dict(
        changed=False,
        message='',
)

def check_status(blueprint_label,routing_zone_name,client):    
    blueprints = client.blueprints.list()
    blueprint_labels = [bp['label'] for bp in blueprints]
    if blueprint_label not in blueprint_labels:
        result['message'] = f"Blueprint '{blueprint_label}' does not exist."
        return "BP Not exists"
    else:
      for blueprint in blueprints:
        if blueprint['label'] == blueprint_label:
            my_bp_id = client.blueprints[blueprint['id']]
      routing_zone = my_bp_id.security_zones.list()
      vrf_names = []
      if isinstance(routing_zone, str):
          routing_zone = json.loads(routing_zone)  # Parse JSON string to dictionary
      for dictionary in routing_zone.values():
          vrf_names.append(dictionary.get('vrf_name'))
      if routing_zone_name not in vrf_names:
          return "Not exists"
      else:
          result['message'] = f"VRF '{routing_zone_name}' already exist in Blueprint '{blueprint_label}'."
          return "Exists"
    
def create_routing_zone(blueprint_label,routing_zone_name,client,vni_id,vrf_type):
    blueprints = client.blueprints.list()
    for blueprint in blueprints:
      if blueprint['label'] == blueprint_label:
            my_bp_id = client.blueprints[blueprint['id']] 
    
    my_bp_id.security_zones.create(data={
            "vrf_name": "{}".format(routing_zone_name), 
            "vni_id": vni_id, 
            "vrf_description": "vrf desc for {}".format(routing_zone_name), 
            "sz_type": vrf_type,
            "label": "{}".format(routing_zone_name)
        })
    result['message'] = f"Routing Zone '{routing_zone_name}' created in Blueprint '{blueprint_label}'."
    result['changed'] = True

def delete_routing_zone(blueprint_label,routing_zone_name,client):
    blueprints = client.blueprints.list()
    for blueprint in blueprints:
      if blueprint['label'] == blueprint_label:
            my_bp_id = client.blueprints[blueprint['id']] 
    
    routing_zone = my_bp_id.security_zones.list()
    vrf_to_id = {}
    for zone in routing_zone.values():
      vrf_name = zone.get('vrf_name')
      zone_id = zone.get('id')
      if vrf_name and zone_id:
        vrf_to_id[vrf_name] = zone_id

    my_bp_id.security_zones[vrf_to_id[routing_zone_name]].delete()
    result['message'] = f"Routing Zone '{routing_zone_name}' deleted from Blueprint '{blueprint_label}'."
    result['changed'] = True

def run_module():
    
    create_routing_zone_module_args = dict(
        blueprint_label=dict(type='str', required=True),
        routing_zone_name=dict(type='str', required=True),
        vni_id=dict(type='int', required=False,default=100000),
        vrf_type=dict(type='str', required=False, choices=['evpn', 'l3_fabric'],default='evpn'),
        state=dict(type='str', required=True, choices=['absent', 'present']),
        )
    
    client_module_args = apstra_client_module_args()
    module_args = client_module_args | create_routing_zone_module_args
   
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
        )
    
    client_factory = ApstraClientFactory.from_params(module.params)
    client = client_factory.l3clos_client()

    
# Check the status of a VRF and Blueprint exists or not
    status = check_status(module.params['blueprint_label'],module.params['routing_zone_name'],client)
    if status == "BP Not exists":
        result['changed'] = False
    elif status == "Exists" and module.params['state'] == "present":
        result['changed'] = False
    elif status == "Exists" and module.params['state'] == "absent":
        delete_routing_zone(module.params['blueprint_label'],module.params['routing_zone_name'],client)
    elif status == "Not exists" and module.params['state'] == "present":
        create_routing_zone(module.params['blueprint_label'],module.params['routing_zone_name'],client,module.params['vni_id'],module.params['vrf_type'])
    elif status == "Not exists" and module.params['state'] == 'absent':
        result['message'] = f"Routing Zone '{module.params['routing_zone_name']}' does not exist in Blueprint '{module.params['blueprint_label']}'."
        result['changed'] = False
    else:
        result['changed'] = "Either Blueprint/VRF does not exist or state is not defined"

    module.exit_json(**result)


def main():
    run_module()
    

if __name__ == '__main__':
    main()