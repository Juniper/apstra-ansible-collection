from ansible.plugins.callback import CallbackBase

class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'cleanup'
    CALLBACK_NAME = 'cleanup'

    def __init__(self, *args, **kwargs):
        super(CallbackModule, self).__init__(*args, **kwargs)

    def v2_playbook_on_cleanup(self, playbook):
        # Close the client connection
        if hasattr(playbook, 'apstra_client') and playbook.apstra_client:
            playbook.apstra_client.logout()