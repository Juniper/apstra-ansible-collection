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
            client = self.client()
            client.logout() 

    def _login(self, client):
        if (bool(self.auth_token)):
            client.set_auth_token(self.auth_token)
        elif (self.username and self.password):
            self.auth_token, self.user_id = client.login(self.username, self.password)
        else:
            raise Exception("Missing required parameters: api_url, auth_token or (username and password)")

    def client(self):
        client = Client(self.api_url, self.verify_certificates)
        self._login(client)
        return client

    def l3clos_client(self):
        client = l3closClient(self.api_url, self.verify_certificates)
        self._login(client)
        return client

    def freeform_client(self):
        client = freeformClient(self.api_url, self.verify_certificates)
        self._login(client)
        return client

    def endpointpolicy_client(self):
        client = endpointPolicyClient(self.api_url, self.verify_certificates)
        self._login(client)
        return client

    def tags_client(self):
        client = tagsClient(self.api_url, self.verify_certificates)
        self._login(client)
        return client
