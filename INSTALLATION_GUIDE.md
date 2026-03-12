![Juniper Networks](https://juniper-prod.scene7.com/is/image/junipernetworks/juniper_black-rgb-header?wid=320&dpr=off)

# Juniper Apstra Ansible Collection — Installation Guide

This guide provides step-by-step instructions for **customers and partners** to install and use the **Juniper Apstra Ansible Collection** (`juniper.apstra`) along with the required **Apstra SDK** (`aos_sdk`).

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Install the Apstra Ansible Collection](#2-install-the-apstra-ansible-collection)
   - [Option A: From Ansible Galaxy (Recommended)](#option-a-from-ansible-galaxy-recommended)
   - [Option B: From a Tarball (Offline / Air-Gapped)](#option-b-from-a-tarball-offline--air-gapped)
   - [Option C: From GitHub Source](#option-c-from-github-source)
3. [Install the Apstra SDK](#3-install-the-apstra-sdk)
   - [Option A: From Juniper Support Downloads (Recommended)](#option-a-from-juniper-support-downloads-recommended)
   - [Option B: From a Provided Wheel File (Offline / Air-Gapped)](#option-b-from-a-provided-wheel-file-offline--air-gapped)
4. [Install Remaining Python Dependencies](#4-install-remaining-python-dependencies)
5. [Verify the Installation](#5-verify-the-installation)
6. [Quick Start — Your First Playbook](#6-quick-start--your-first-playbook)
7. [Available Modules](#7-available-modules)
8. [Environment & Configuration Reference](#8-environment--configuration-reference)
9. [Upgrading](#9-upgrading)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Prerequisites

| Requirement | Minimum Version |
|---|---|
| **Python** | 3.11+ |
| **Ansible Core** | 2.16.14+ (collection requires >= 2.15.0) |
| **pip** | Latest recommended |
| **Apstra Server** | 5.0+ |

### Install Python 3.11+ and Ansible

```bash
# Ubuntu / Debian
sudo apt update && sudo apt install -y python3.11 python3.11-venv python3-pip

# RHEL / CentOS / Rocky
sudo dnf install -y python3.11 python3.11-pip

# macOS (via Homebrew)
brew install python@3.11
```

Set up a virtual environment (recommended):

```bash
python3.11 -m venv ~/apstra-ansible-env
source ~/apstra-ansible-env/bin/activate
pip install --upgrade pip
```

Install Ansible:

```bash
pip install "ansible-core>=2.16.14"
```

---

## 2. Install the Apstra Ansible Collection

Choose **one** of the three options below. Each is a self-contained installation method — you do **not** need to combine them.

### Option A: From Ansible Galaxy (Recommended — No Git Clone Required)

This is the simplest method. The `ansible-galaxy` CLI downloads the collection directly from [Ansible Galaxy](https://galaxy.ansible.com/ui/repo/published/juniper/apstra/) — **no git clone needed**.

```bash
# This single command downloads and installs the collection
ansible-galaxy collection install juniper.apstra
```

The collection is installed to `~/.ansible/collections/ansible_collections/juniper/apstra/`.

To install a specific version:

```bash
ansible-galaxy collection install juniper.apstra:1.0.5
```

To force-reinstall (upgrade):

```bash
ansible-galaxy collection install juniper.apstra --force
```

#### Using a `requirements.yml` (for automation / CI)

Create a `requirements.yml` file:

```yaml
---
collections:
  - name: juniper.apstra
    version: ">=1.0.5"
```

Then install:

```bash
ansible-galaxy collection install -r requirements.yml
```

### Option B: From a Tarball (Offline / Air-Gapped — No Git Clone Required)

Use this if you have received the collection as a `.tar.gz` file from your Juniper account team (e.g., `juniper-apstra-1.0.5.tar.gz`). **No git clone or internet access needed.**

```bash
ansible-galaxy collection install juniper-apstra-1.0.5.tar.gz --ignore-certs
```

### Option C: Build from GitHub Source (Developer / Advanced)

Use this **only** if you need the latest unreleased code or want to contribute. This is the only option that requires cloning the repository.

```bash
# Step 1: Clone the repository
git clone https://github.com/Juniper/apstra-ansible-collection.git
cd apstra-ansible-collection

# Step 2: Build the collection tarball from source
cd ansible_collections/juniper/apstra
ansible-galaxy collection build

# Step 3: Install the tarball you just built
ansible-galaxy collection install juniper-apstra-*.tar.gz --force
```

> **Summary:** For most users, **Option A** is all you need — just run `ansible-galaxy collection install juniper.apstra` and proceed to [Step 3 (Install the SDK)](#3-install-the-apstra-sdk).

---

## 3. Install the Apstra SDK

The collection depends on the **Apstra SDK** (`aos_sdk`) Python package. A different package named `aos-sdk-api` exists on PyPI but is **not compatible** — the full SDK must be downloaded from the Juniper Support Downloads portal.

### Option A: From Juniper Support Downloads (Recommended)

1. Go to the **Juniper Support Downloads** page for Apstra:

   > **https://support.juniper.net/support/downloads/?p=apstra**

2. Under **"Application Tools"**, locate **"Apstra Automation Python3 SDK"**.

3. Download the `.tar.gz` archive (e.g., `apstra-automation-python3-sdk-<version>.tar.gz`).

4. Extract the archive to obtain the SDK wheel file:

   ```bash
   # Extract the downloaded archive
   tar -xzf apstra-automation-python3-sdk-*.tar.gz

   # The wheel file will be inside the extracted directory
   # Look for: aos_sdk-6.1.0-py3-none-any.whl
   find . -name "aos_sdk-*.whl"
   ```

5. Install the SDK wheel into your Python environment:

   ```bash
   pip install aos_sdk-6.1.0-py3-none-any.whl
   ```

> **Note:** A valid Juniper support account is required to access the downloads portal. Contact your Juniper account team if you need access.

### Option B: From a Provided Wheel File (Offline / Air-Gapped)

If your Juniper SE or account team has provided the `aos_sdk-*.whl` file directly:

```bash
pip install /path/to/aos_sdk-6.1.0-py3-none-any.whl
```

---

## 4. Install Remaining Python Dependencies

After installing the collection, install the remaining required Python packages. The collection ships a `requirements.txt` file:

```bash
# If installed from Galaxy, requirements.txt is at:
pip install -r ~/.ansible/collections/ansible_collections/juniper/apstra/requirements.txt
```

Or install the dependencies manually:

```bash
pip install "jmespath>=1.1.0" "jsonpatch>=1.33" "kubernetes>=35.0.0" "requests-oauthlib>=2.0.0"
```

> **Note:** The `requirements.txt` shipped with the collection references the `aos_sdk` wheel by local path. If you've already installed the SDK per [Step 3](#3-install-the-apstra-sdk), the remaining dependencies are just the four packages listed above.

### Summary of All Dependencies

| Package | Minimum Version | Purpose |
|---|---|---|
| `aos_sdk` | 6.1.0 | Core Apstra API SDK (Juniper-provided) |
| `ansible-core` | 2.16.14 | Ansible automation engine |
| `jmespath` | 1.1.0 | JSON query expressions for filtering |
| `jsonpatch` | 1.33 | JSON Patch (RFC 6902) for config diffs |
| `kubernetes` | 35.0.0 | Kubernetes API client (for K8s-based Apstra deployments) |
| `requests-oauthlib` | 2.0.0 | OAuth authentication support |

---

## 5. Verify the Installation

### Check the collection is installed

```bash
ansible-galaxy collection list | grep juniper.apstra
```

Expected output:

```
juniper.apstra    1.0.5
```

### Check the SDK is importable

```bash
python -c "from aos.sdk.client import Client; print('Apstra SDK loaded successfully')"
```

### Check a module is loadable

```bash
ansible-doc juniper.apstra.authenticate
```

This should display the full documentation for the `authenticate` module.

### List all available modules

```bash
ansible-doc -l juniper.apstra
```

---

## 6. Quick Start — Your First Playbook

### Step 1: Create an inventory file

Create `inventory.yml`:

```yaml
all:
  hosts:
    localhost:
      ansible_connection: local
```

### Step 2: Create a playbook

Create `apstra_quickstart.yml`:

```yaml
---
- name: Apstra Quick Start
  hosts: localhost
  gather_facts: false

  vars:
    apstra_url: "https://<YOUR_APSTRA_SERVER_IP>/api"
    apstra_username: "admin"
    apstra_password: "YOUR_PASSWORD"
    # Set to false if your Apstra server uses a self-signed certificate
    apstra_verify_certs: false

  tasks:
    # ── Step 1: Authenticate ──────────────────────────────────
    - name: Log in to Apstra
      juniper.apstra.authenticate:
        api_url: "{{ apstra_url }}"
        username: "{{ apstra_username }}"
        password: "{{ apstra_password }}"
        verify_certificates: "{{ apstra_verify_certs }}"
        logout: false
      register: auth

    # ── Step 2: Gather facts ──────────────────────────────────
    - name: Gather all Apstra facts
      juniper.apstra.apstra_facts:
        api_url: "{{ apstra_url }}"
        auth_token: "{{ auth.token }}"
        verify_certificates: "{{ apstra_verify_certs }}"
        gather_network_facts: "all"
        available_network_facts: true
      register: facts_result

    - name: Display discovered blueprints
      ansible.builtin.debug:
        var: apstra_facts.blueprints

    # ── Step 3: Create a blueprint ────────────────────────────
    - name: Create or retrieve a blueprint
      juniper.apstra.blueprint:
        api_url: "{{ apstra_url }}"
        auth_token: "{{ auth.token }}"
        verify_certificates: "{{ apstra_verify_certs }}"
        body:
          label: "my_first_blueprint"
          design: "two_stage_l3clos"
        lock_state: "ignore"
      register: bp

    - name: Show blueprint details
      ansible.builtin.debug:
        var: bp

    # ── Step 4: Log out ───────────────────────────────────────
    - name: Log out of Apstra
      juniper.apstra.authenticate:
        api_url: "{{ apstra_url }}"
        auth_token: "{{ auth.token }}"
        verify_certificates: "{{ apstra_verify_certs }}"
        logout: true
```

### Step 3: Run the playbook

```bash
ansible-playbook -i inventory.yml apstra_quickstart.yml -v
```

> **Tip:** Use `-e apstra_password=YOUR_PASSWORD` or Ansible Vault to avoid hardcoding credentials.

### Using Ansible Vault for Credentials (Recommended)

```bash
# Create an encrypted vars file
ansible-vault create vars/apstra_secrets.yml
```

Add:

```yaml
apstra_username: admin
apstra_password: YOUR_SECRET_PASSWORD
```

Reference in playbook:

```yaml
  vars_files:
    - vars/apstra_secrets.yml
```

Run with:

```bash
ansible-playbook -i inventory.yml apstra_quickstart.yml --ask-vault-pass
```

---

## 7. Available Modules

| Module | Description |
|---|---|
| `juniper.apstra.authenticate` | Login / logout and retrieve session tokens |
| `juniper.apstra.apstra_facts` | Gather facts (blueprints, VNs, security zones, pools, etc.) |
| `juniper.apstra.blueprint` | Create, commit, lock/unlock, delete, and query blueprints |
| `juniper.apstra.security_zone` | Manage security zones (VRFs) |
| `juniper.apstra.virtual_network` | Create/delete VXLAN/VLAN virtual networks |
| `juniper.apstra.routing_policy` | Manage BGP routing policies |
| `juniper.apstra.external_gateway` | EVPN external gateway peering |
| `juniper.apstra.connectivity_template` | Create/manage connectivity templates |
| `juniper.apstra.connectivity_template_assignment` | Assign CTs to interfaces |
| `juniper.apstra.configlets` | Global and blueprint-scoped configlets |
| `juniper.apstra.property_set` | Key-value property sets |
| `juniper.apstra.resource_pools` | ASN, IP, VLAN, VNI resource pools |
| `juniper.apstra.resource_group` | Assign resource pools to blueprint groups |
| `juniper.apstra.endpoint_policy` | Endpoint policies and application points |
| `juniper.apstra.design` | Design objects (logical devices, rack types, templates) |
| `juniper.apstra.generic_systems` | External/generic system management |
| `juniper.apstra.system_agents` | NOS device agent onboarding |
| `juniper.apstra.interface_map` | Interface map assignment |
| `juniper.apstra.fabric_settings` | Fabric-wide settings (MTU, EVPN, overlay) |
| `juniper.apstra.tag` | Tag management for blueprint objects |
| `juniper.apstra.rollback` | Blueprint rollback operations |

For full documentation on any module:

```bash
ansible-doc juniper.apstra.<module_name>
```

---

## 8. Environment & Configuration Reference

### SSL Certificate Verification

If your Apstra server uses a self-signed certificate, disable SSL verification:

```yaml
# Option 1: Per-task parameter (add to every juniper.apstra task)
verify_certificates: false

# Option 2: Environment variable (applies to all tasks)
environment:
  APSTRA_VERIFY_CERTIFICATES: "false"
```

Or globally via `ansible.cfg`:

```ini
[defaults]
# Suppress localhost warnings
localhost_warning = false
inventory_unparsed_warning = false
```

### Collection Installation Paths

| Method | Default Location |
|---|---|
| `ansible-galaxy install` (user) | `~/.ansible/collections/ansible_collections/juniper/apstra/` |
| `ansible-galaxy install -p ./collections` | `./collections/ansible_collections/juniper/apstra/` |
| System-wide | `/usr/share/ansible/collections/ansible_collections/juniper/apstra/` |

### Custom Collection Path

```ini
# ansible.cfg
[defaults]
collections_path = /opt/ansible/collections:~/.ansible/collections
```

---

## 9. Upgrading

### Upgrade the Collection

```bash
# From Galaxy
ansible-galaxy collection install juniper.apstra --force --upgrade

# From tarball
ansible-galaxy collection install juniper-apstra-<NEW_VERSION>.tar.gz --force
```

### Upgrade the SDK

```bash
pip install --force-reinstall /path/to/aos_sdk-<NEW_VERSION>-py3-none-any.whl
```

### Upgrade Dependencies

```bash
pip install --upgrade -r ~/.ansible/collections/ansible_collections/juniper/apstra/requirements.txt
```

---

## 10. Troubleshooting

### "No module named 'aos'" error

**Cause:** The Apstra SDK (`aos_sdk`) is not installed or not in the active Python environment.

**Fix:**

```bash
# Check if the SDK is installed
pip show aos-sdk

# If not, install it
pip install /path/to/aos_sdk-6.1.0-py3-none-any.whl

# Make sure you're using the same Python that Ansible uses
ansible --version   # check the python path
```

### "Collection juniper.apstra not found" error

**Cause:** The collection is not installed or not in Ansible's collection search path.

**Fix:**

```bash
# Verify installation
ansible-galaxy collection list | grep juniper

# Reinstall if needed
ansible-galaxy collection install juniper.apstra --force
```

### SSL/TLS Certificate errors

```bash
# Option 1: Use --ignore-certs during install
ansible-galaxy collection install juniper.apstra --ignore-certs

# Option 2: Disable TLS verification in playbook
# Add to your task:
#   environment:
#     APSTRA_API_TLS_VERIFY: "false"
```

### "ansible-galaxy: command not found"

```bash
pip install "ansible-core>=2.16.14"
```

### Version compatibility matrix

| Apstra Server Version | SDK Version | Collection Version |
|---|---|---|
| 5.0+ | 6.1.0 | 1.0.5 |

---

## One-Liner Full Setup (Copy-Paste Ready)

For a quick setup on a fresh machine:

```bash
# 1. Create virtual environment and install Ansible + collection
python3.11 -m venv ~/apstra-ansible-env && \
source ~/apstra-ansible-env/bin/activate && \
pip install --upgrade pip && \
pip install "ansible-core>=2.16.14" && \
ansible-galaxy collection install juniper.apstra --ignore-certs

# 2. Download the SDK from Juniper Support Downloads:
#    https://support.juniper.net/support/downloads/?p=apstra
#    → Application Tools → Apstra Automation Python3 SDK → Download .tar.gz

# 3. Extract and install the SDK wheel
tar -xzf apstra-automation-python3-sdk-*.tar.gz && \
pip install aos_sdk-6.1.0-py3-none-any.whl

# 4. Install remaining dependencies and verify
pip install "jmespath>=1.1.0" "jsonpatch>=1.33" "kubernetes>=35.0.0" "requests-oauthlib>=2.0.0" && \
ansible-doc -l juniper.apstra && \
echo "✅ Installation complete!"
```

---

## Support & Resources

| Resource | Link |
|---|---|
| GitHub Repository | https://github.com/Juniper/apstra-ansible-collection |
| Issue Tracker | https://github.com/Juniper/apstra-ansible-collection/issues |
| Ansible Galaxy | https://galaxy.ansible.com/ui/repo/published/juniper/apstra/ |
| Apstra Documentation | https://www.juniper.net/documentation/product/us/en/apstra/ |
| Juniper Support | https://support.juniper.net/ |
| Ansible Forum (Juniper tag) | https://forum.ansible.com/tag/juniper |

---

*Document Version: 1.0 — March 2026*
*Collection Version: 1.0.5 | SDK Version: 6.1.0 | Apstra Server: 5.0+*
