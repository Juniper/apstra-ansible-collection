from aos.sdk.client import Client
from aos.sdk.reference_design.two_stage_l3clos import Client as l3closClient
from aos.sdk.reference_design.freeform.client import Client as freeformClient
from aos.sdk.reference_design.extension.endpoint_policy import Client as endpointPolicyClient
from aos.sdk.reference_design.extension.tags.client import Client as tagsClient
import os

def apstra_client_module_args():
    return dict(
        api_url=dict(type='str', required=False, default=os.getenv('APSTRA_API_URL')),
        verify_certificates=dict(type='bool', required=False, default=not (os.getenv('APSTRA_VERIFY_CERTIFICATES') in ['0', 'false', 'False', 'FALSE', 'no', 'No', 'NO'])),
        auth_token=dict(type='str', required=False, no_log=True, default=os.getenv('APSTRA_AUTH_TOKEN')),
        username=dict(type='str', required=False, default=os.getenv('APSTRA_USERNAME')),
        password=dict(type='str', required=False, no_log=True, default=os.getenv('APSTRA_PASSWORD')),
        logout=dict(type='bool', required=False)
    )

class ApstraClientFactory:
    def __init__(self, api_url, verify_certificates, auth_token, username, password, logout):
        self.api_url = api_url
        self.verify_certificates = verify_certificates
        self.auth_token = auth_token
        self.username = username
        self.password = password
        self.logout = logout
        self.user_id = None
        self.base_client = None
        self.l3clos_client = None
        self.freeform_client = None
        self.endpointpolicy_client = None
        self.tags_client = None

        # Map client members to client types
        self.client_types = {
            'base_client': Client,
            'l3clos_client': l3closClient,
            'freeform_client': freeformClient,
            'endpointpolicy_client': endpointPolicyClient,
            'tags_client': tagsClient,
        }

        # Map client to types. Dotted types are traversed.
        self.client_to_types = {
            'freeform_client': ['config_templates'],
            'l3clos_client': ['virtual_networks', 'routing_zone_constraints'],
            'endpointpolicy_client': ['endpoint_policies', 'obj_policy_application_points'],
            'tags_client' : ['tags'],            
        }

        # Populate the list (and set) of supported objects
        self.network_resources = []
        self.network_resources_set = {}
        for resource_client, resource_types in self.client_to_types.items():
            for resource_type in resource_types:
                self.network_resources.append(resource_type)
                # Map the resource type to the client
                self.network_resources_set[resource_type] = resource_client

    @classmethod
    def from_params(cls, params):
        api_url = params.get('api_url')
        verify_certificates = params.get('verify_certificates')
        auth_token = params.get('auth_token')
        username = params.get('username')
        password = params.get('password')

        # Do not log out if auth_token is already set
        logout = params.get('logout')
        if logout is None:
            logout = not bool(auth_token)

        return cls(api_url, verify_certificates, auth_token, username, password, logout)

    def __del__(self):
        if (self.logout):
            base_client = self.get_base_client()
            base_client.logout() 

    def _login(self, client):
        if (bool(self.auth_token)):
            client.set_auth_token(self.auth_token)
        elif (self.username and self.password):
            self.auth_token, self.user_id = client.login(self.username, self.password)
        else:
            raise Exception("Missing required parameters: api_url, auth_token or (username and password)")

    def _get_client(self, client_attr, client_class):
        client_instance = getattr(self, client_attr)
        if client_instance is None:
            client_instance = client_class(self.api_url, self.verify_certificates)
            setattr(self, client_attr, client_instance)
        self._login(client_instance)
        return client_instance

    def get_client(self, resource_type):
        client_attr = self.network_resources_set.get(resource_type)
        if client_attr is None:
            raise Exception("Unsupported resource type: {}".format(resource_type))
        client_type = self.client_types.get(client_attr)
        if client_type is None:
            raise Exception("Unsupported client type: {}".format(client_attr))
        return self._get_client(client_attr, client_type)

    def get_base_client(self):
        return self._get_client('base_client', Client)

    def get_l3clos_client(self):
        return self._get_client('l3clos_client', l3closClient)

    def get_freeform_client(self):
        return self._get_client('freeform_client', freeformClient)

    def get_endpointpolicy_client(self):
        return self._get_client('endpointpolicy_client', endpointPolicyClient)

    def get_tags_client(self):
        return self._get_client('tags_client', tagsClient)
