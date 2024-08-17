from ansible.plugins.connection import ConnectionBase
from aos.sdk.reference_design.two_stage_l3clos.client import Client
import os

class Connection(ConnectionBase):
    def __init__(self, play_context, *args, **kwargs):
        super(Connection, self).__init__(play_context, *args, **kwargs)
        self._client = None

    def _connect(self):
        if self._client is None:
            api_url = os.getenv('APSTRA_API_URL')
            verify_certificates_env = os.getenv('APSTRA_VERIFY_CERTIFICATES') or '1'
            verify_certificates = not (verify_certificates_env in ['0', 'false', 'False', 'FALSE', 'no', 'No', 'NO'])
            username = os.getenv('APSTRA_USERNAME')
            password = os.getenv('APSTRA_PASSWORD')

            self._client = Client(api_url, verify_certificates)
            self._client.login(username, password)
        return self._client

    def close(self):
        if self._client:
            self._client.logout()
            self._client = None

    def exec_command(self, cmd, in_data=None, sudoable=True):
        client = self._connect()
    
        # Split the command string to navigate through nested methods
        parts = cmd.split('.')
    
        # Start with the client object
        obj = client
    
        # Navigate through the nested attributes
        for part in parts[:-1]:
            obj = getattr(obj, part)
    
        # Get the final method to call
        method = getattr(obj, parts[-1])
    
        # Call the method and get the response
        response = method()
    
        return 0, response, ''
    
    def fetch_file(self, in_path, out_path):
        # Implement the logic to fetch a file from the remote system
        pass

    def put_file(self, in_path, out_path):
        # Implement the logic to put a file on the remote system
        pass

    def transport(self):
        # Implement the transport logic here
        pass

    def gather_facts(self, available_network_resources=False, gather_network_resources=False, gather_subset=[]):
        client = self._connect()
        
        # Get /api/version
        version = client.version.get()
        
        # Get /api/blueprints
        
        # Get /api/blueprints/{blueprint_id}/routing-zone-constraints
        
        # Get /api/blueprints/{blueprint_id}/config-templates
        
        # Get /api/blueprints/{{blueprint_id}}/endpoint-policies
        
        # Get /api/blueprints/{{blueprint_id}}/obj-policy-application-points
        
        # Example of gathering facts
        facts = {
            'version': version,
            # Add more facts as needed
        }
        
        return facts