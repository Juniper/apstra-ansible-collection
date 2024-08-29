from aos.sdk.client import Client
import os

def apstra_client_module_args():
    return dict(
        api_url=dict(type='str', required=False),
        verify_certificates=dict(type='str', required=False, default='1'),
        auth_token=dict(type='str', required=False, no_log=True),
    )

def apstra_client_auth_info(params):
    api_url = params['api_url'] or os.getenv('APSTRA_API_URL')
    verify_certificates_env = params['verify_certificates'] or os.getenv('APSTRA_VERIFY_CERTIFICATES')
    verify_certificates = not (verify_certificates_env in ['0', 'false', 'False', 'FALSE', 'no', 'No', 'NO'])
    auth_token = params['auth_token'] or os.getenv('APSTRA_AUTH_TOKEN')
    return api_url, verify_certificates, auth_token

def apstra_client(params):
    api_url, verify_certificates, auth_token = apstra_client_auth_info(params)
    client = Client(api_url, verify_certificates)
    client.set_auth_token(auth_token)
    return client