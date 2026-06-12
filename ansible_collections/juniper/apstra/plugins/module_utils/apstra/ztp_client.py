"""
ZTP Client utility for the Apstra ZTP VM.

This module provides a lightweight REST client for communicating with the
Apstra ZTP VM, which is a separate appliance from the Apstra server and
uses its own authentication and API surface.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
import os

try:
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    pass

try:
    from urllib.request import Request, urlopen
    from urllib.error import URLError, HTTPError
except ImportError:
    from urllib2 import Request, urlopen, URLError, HTTPError

import ssl


def ztp_client_module_args():
    """
    Return the module arguments for ZTP VM connection parameters.

    These are separate from the Apstra server args because the ZTP VM
    is a distinct appliance with its own auth.
    """
    return dict(
        ztp_url=dict(
            type="str",
            required=False,
            default=os.getenv("ZTP_URL"),
        ),
        ztp_username=dict(
            type="str",
            required=False,
            default=os.getenv("ZTP_USERNAME"),
        ),
        ztp_password=dict(
            type="str",
            required=False,
            no_log=True,
            default=os.getenv("ZTP_PASSWORD"),
        ),
        ztp_auth_token=dict(
            type="str",
            required=False,
            no_log=True,
            default=os.getenv("ZTP_AUTH_TOKEN"),
        ),
        ztp_verify_certificates=dict(
            type="bool",
            required=False,
            default=not (
                os.getenv("ZTP_VERIFY_CERTIFICATES")
                in ["0", "false", "False", "FALSE", "no", "No", "NO"]
            ),
        ),
    )


class ZtpClientError(Exception):
    """Raised when a ZTP API call fails."""

    def __init__(self, message, status_code=None, response_body=None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class ZtpClient:
    """
    REST client for the Apstra ZTP VM API.

    Handles authentication via /api/ztp/aaa/login and provides
    methods for DHCP configurator and ZTP JSON config endpoints.
    """

    LOGIN_ENDPOINT = "/api/ztp/aaa/login"
    LOGOUT_ENDPOINT = "/api/ztp/aaa/logout"
    DHCP_CONFIGURATOR_ENDPOINT = "/api/ztp/config/dhcp/configurator"
    ZTP_CONFIG_ENDPOINT = "/api/ztp/config/ztpjson"
    CHANGE_PASSWORD_ENDPOINT = "/api/ztp/aaa/change-password"
    CREATE_AGENT_ENDPOINT = "/api/ztp/create_agent"
    DEVICE_LOG_ENDPOINT = "/api/ztp/device/log"
    DEVICE_STATUS_ENDPOINT = "/api/ztp/device/status"

    def __init__(
        self,
        base_url,
        username=None,
        password=None,
        auth_token=None,
        verify_certificates=False,
    ):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.auth_token = auth_token
        self.verify_certificates = verify_certificates

        if not self.auth_token and self.username and self.password:
            self._login()

    def _get_ssl_context(self):
        ctx = ssl.create_default_context()
        if not self.verify_certificates:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        return ctx

    def _request(self, endpoint, method="GET", data=None):
        """
        Make an HTTP request to the ZTP VM.

        :param endpoint: The API endpoint path (e.g., /api/ztp/config/ztpjson).
        :param method: HTTP method (GET, POST, PUT, DELETE).
        :param data: Dictionary to send as JSON body.
        :return: Parsed JSON response or None for empty responses.
        :raises ZtpClientError: On HTTP errors.
        """
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["AuthToken"] = self.auth_token

        body = None
        if data is not None:
            body = json.dumps(data).encode("utf-8")

        req = Request(url, data=body, headers=headers, method=method)

        try:
            response = urlopen(req, context=self._get_ssl_context())
            response_data = response.read().decode("utf-8")
            if response_data:
                return json.loads(response_data)
            return None
        except HTTPError as e:
            response_body = e.read().decode("utf-8") if e.fp else None
            error_msg = f"ZTP API error: {e.code} {e.reason}"
            if response_body:
                try:
                    error_detail = json.loads(response_body)
                    if isinstance(error_detail, dict):
                        error_msg = error_detail.get("errors", error_msg)
                except (json.JSONDecodeError, ValueError):
                    error_msg = response_body
            raise ZtpClientError(
                error_msg, status_code=e.code, response_body=response_body
            )
        except URLError as e:
            raise ZtpClientError(f"Failed to connect to ZTP VM at {url}: {e.reason}")

    def _login(self):
        """Authenticate with the ZTP VM and store the auth token."""
        response = self._request(
            self.LOGIN_ENDPOINT,
            method="POST",
            data={"username": self.username, "password": self.password},
        )
        if not response or "token" not in response:
            raise ZtpClientError("ZTP login failed: no token in response")
        self.auth_token = response["token"]

    # --- DHCP Configurator ---

    def get_dhcp_configurator(self):
        """GET /api/ztp/config/dhcp/configurator — returns configurator data."""
        return self._request(self.DHCP_CONFIGURATOR_ENDPOINT)

    def update_dhcp_configurator(self, data):
        """POST /api/ztp/config/dhcp/configurator — update DHCP via configurator."""
        return self._request(self.DHCP_CONFIGURATOR_ENDPOINT, method="POST", data=data)

    # --- ZTP JSON Config ---

    def get_ztp_config(self):
        """GET /api/ztp/config/ztpjson — returns ZTP JSON config."""
        return self._request(self.ZTP_CONFIG_ENDPOINT)

    def update_ztp_config(self, data):
        """PUT /api/ztp/config/ztpjson — update ZTP JSON config."""
        return self._request(self.ZTP_CONFIG_ENDPOINT, method="PUT", data=data)

    # --- Password Management ---

    def change_password(self, old_password, new_password):
        """PUT /api/ztp/aaa/change-password — change the ZTP admin password."""
        return self._request(
            self.CHANGE_PASSWORD_ENDPOINT,
            method="PUT",
            data={"old_password": old_password, "new_password": new_password},
        )

    # --- Agent Management ---

    def create_agent(
        self,
        management_ip,
        username,
        password,
        agent_type="offbox",
        job_on_create="install",
        platform="junos",
    ):
        """POST /api/ztp/create_agent — create system agent via ZTP VM.

        This creates the agent on the Apstra server and tracks it in the
        ZTP VM. The ZTP VM proxies the request to Apstra's
        /api/ztp/create_agent endpoint.

        :param management_ip: Device management IP address.
        :param username: SSH username for the device.
        :param password: SSH password for the device.
        :param agent_type: Agent type (default: offbox).
        :param job_on_create: Job to run on create (default: install).
        :param platform: Device platform (default: junos).
        :return: Dict with agent id, e.g. {"id": "uuid"}.
        """
        data = {
            "management_ip": management_ip,
            "username": username,
            "password": password,
            "agent_type": agent_type,
            "job_on_create": job_on_create,
            "platform": platform,
        }
        return self._request(self.CREATE_AGENT_ENDPOINT, method="POST", data=data)

    # --- Device Status ---

    def update_device_log(self, ip, system_id="", platform="", task="", log=""):
        """POST /api/ztp/device/log — update device status in ZTP VM.

        This is how ztp.py reports device provisioning progress. Setting
        task to 'Device Ready' marks the device as completed.

        :param ip: Device IP address.
        :param system_id: Device system ID (serial/MAC).
        :param platform: Device platform (junos, nxos, eos).
        :param task: Current task name. 'Device Ready' = completed,
                     'ZTP Failed' = failed.
        :param log: Log message describing the status.
        :return: Empty dict on success.
        """
        data = {"ip": ip}
        if system_id:
            data["system_id"] = system_id
        if platform:
            data["platform"] = platform
        if task:
            data["task"] = task
        if log:
            data["log"] = log
        return self._request(self.DEVICE_LOG_ENDPOINT, method="POST", data=data)

    def get_device_status(self, ip=None):
        """GET /api/ztp/device/status — get ZTP device status.

        :param ip: Optional device IP. If provided, gets status for that
                   device via /api/ztp/device/status/<ip>. Otherwise
                   returns all devices.
        :return: Device status dict or list of all devices.
        """
        if ip:
            return self._request(f"{self.DEVICE_STATUS_ENDPOINT}/{ip}")
        return self._request(self.DEVICE_STATUS_ENDPOINT)

    @classmethod
    def from_module_params(cls, module):
        """
        Create a ZtpClient from Ansible module params.

        :param module: The AnsibleModule instance.
        :return: A ZtpClient instance.
        :raises ZtpClientError: If required params are missing.
        """
        ztp_url = module.params.get("ztp_url")
        if not ztp_url:
            raise ZtpClientError(
                "ztp_url is required. Set it via the module parameter or "
                "the ZTP_URL environment variable."
            )

        ztp_auth_token = module.params.get("ztp_auth_token")
        ztp_username = module.params.get("ztp_username")
        ztp_password = module.params.get("ztp_password")

        if not ztp_auth_token and not (ztp_username and ztp_password):
            raise ZtpClientError(
                "Either ztp_auth_token or both ztp_username and ztp_password "
                "are required. Set them via module parameters or the ZTP_AUTH_TOKEN, "
                "ZTP_USERNAME, ZTP_PASSWORD environment variables."
            )

        return cls(
            base_url=ztp_url,
            username=ztp_username,
            password=ztp_password,
            auth_token=ztp_auth_token,
            verify_certificates=module.params.get("ztp_verify_certificates", False),
        )
