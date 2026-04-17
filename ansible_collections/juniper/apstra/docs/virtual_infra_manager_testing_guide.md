# virtual_infra_manager Module — Infrastructure Setup & Testing Guide

**Apstra server:** `https://10.88.137.14`
**Existing blueprint:** `vg-am-cops-tb-0` (`e1d32dac-895f-4ae6-b27a-272dcef072a7`)
**Containerlab host:** `5d9s18-node4.englab.juniper.net`
**Module file:** `plugins/modules/virtual_infra_manager.py`

---

## 0. vCenter Status & Key API Notes

### vCenter provided by infra team

| Field | Value |
|---|---|
| vCenter IP | `10.204.16.35` |
| ESXi host IP | `10.204.16.25` |
| Username | `administrator@vsphere.local` |
| Password | `C0ntrail!23` |
| vCenter version | `7.0.3` |
| Port 443 | ✅ OPEN |
| Auth from Apstra | ✅ **CONNECTED** (verified, connects in ~30s) |

### Apstra API field names (confirmed by live API testing)

The Apstra REST API for `/virtual-infra-managers` does NOT use `hostname` or `type`.
The actual field names are:

| Module doc (wrong) | Apstra API (correct) |
|---|---|
| `type` | `virtual_infra_type` |
| `hostname` | `management_ip` |
| `status` | `connection_state` |

✅ The test file and module examples have been updated to use the correct names.

### vCenter sub-resource (scope=vcenter) creation constraint

`POST /virtual-infra-managers/{id}/vcenters` to **add** a vCenter entry
only works for **NSX-type VIMs**. For vCenter-type VIMs, the `/vcenters`
sub-resource is read-only (auto-populated by Apstra when it connects to the VIM).

---

## 1. Actual Testbed Topology (from testbed.yaml)

All devices in `vg-am-cops-tb-0` are **containerlab containers** running on
`5d9s18-node4.englab.juniper.net`. There are no real physical devices or
hypervisors in this testbed.

| Node | Role | Type | IP |
|---|---|---|---|
| vg-am-cops-tb-0-spine1/2 | spine | clab container | 192.158.159.11/12 |
| vg-am-cops-tb-0-leaf1/2 | leaf | clab container | 192.158.159.13/14 |
| vg-am-cops-tb-0-leaf3/4border | leaf | clab container | 192.158.159.15/16 |
| **vg-am-cops-tb-0-h1** | generic | **Linux container** | 192.158.159.19 |
| **vg-am-cops-tb-0-h2** | generic | **Linux container** | 192.158.159.20 |
| **vg-am-cops-tb-0-h3** | generic | **Linux container** | 192.158.159.21 |
| **vg-am-cops-tb-0-h4** | generic | **Linux container** | 192.158.159.22 |
| vg-am-cops-tb-0-srx1/2 | generic | clab container | 192.158.159.17/18 |

### Host cabling (from testbed.yaml)

```
h1: eth1 → leaf1 ge-0/0/2,  eth2 → leaf2 ge-0/0/2
h2: eth1 → leaf1 ge-0/0/3,  eth2 → leaf2 ge-0/0/3
h3: eth1 → leaf1 ge-0/0/4,  eth2 → leaf2 ge-0/0/4
h4: eth1 → leaf1 ge-0/0/5,  eth2 → leaf2 ge-0/0/5
```

> ⚠️ **h1–h4 are plain Linux containers — they are NOT ESXi hypervisors.**
> They cannot run VMs or be managed by vCenter. They are irrelevant to
> virtual_infra_manager testing.

---

## 2. Do We Need a New Blueprint?

**Depends on what you want to test:**

| Test scope | New blueprint needed? | Notes |
|---|---|---|
| Global VIM CRUD (T1–T4f) | **No** — any testbed works | Only needs Apstra reachability to vCenter |
| Blueprint list/assign (T5a, T5) | **Yes — or add generic system** | Needs a blueprint node representing a real ESXi host |
| anomaly_resolver, query_vm, vnet (T5b–5d) | **Yes** | Needs VIM attached to blueprint + real VMs |

For **Phase 1** (global VIM + vCenter CRUD, T1–T4f): no blueprint changes needed.

For **Phase 2** (blueprint assignment, T5+): you need **one of**:
- **Option A (recommended):** Add a new `generic_system` node to the existing
  blueprint representing the ESXi host and connect it to leaf1/leaf2.
- **Option B:** Create a fresh small blueprint with just the ESXi host node.

---

## 3. What Is `system_id` in `virtual_infra`?

**It is not the blueprint ID and not a leaf/spine system_id.**

It is the **Apstra-assigned UUID of a specific ESXi host** as discovered
through the vCenter VIM after it connects.

```
Step 1: Create global VIM (POST /virtual-infra-managers)
              │
              │ Apstra connects to vCenter API
              ▼
Step 2: Apstra discovers ESXi hosts managed by vCenter
        → Each ESXi host receives an Apstra system_id (UUID)
              │
              │ GET /virtual-infra-managers/{vim-id}/vcenters
              ▼
Step 3: You read the system_id of your ESXi host
              │
              │ POST /blueprints/{blueprint_id}/virtual_infra
              ▼
Step 4: body: { infra_type: "vcenter", system_id: "<esxi-uuid>" }
```

The MAC-style IDs like `0C001C710900` (seen on spines/leaves) are **switch**
system IDs — completely different from ESXi host system IDs, which are UUIDs.

---

## 4. Required Infrastructure

### 4.1 What the Infra Team Must Provide

Since the testbed has no hypervisor, the infra team must stand up a separate
vCenter + ESXi environment. Minimum viable setup:

```
┌─────────────────────────────────────────────────────────────────┐
│                 Network reachable from 10.88.137.14             │
│                                                                  │
│   ┌─────────────────┐        ┌──────────────────────────┐      │
│   │  vCenter Server  │        │      ESXi Host           │      │
│   │  (VCSA VM)       │◄──────►│  vmnic0 ── (trunk)       │      │
│   │  mgmt IP: x.x.x.x│       │  vmnic1 ── (trunk)       │      │
│   └─────────────────┘        │                          │      │
│                               │  ┌──────┐  ┌──────┐    │      │
│                               │  │ VM-A │  │ VM-B │    │      │
│                               │  └──────┘  └──────┘    │      │
│                               └──────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

The ESXi host uplink **does NOT need to physically connect to the containerlab
leaf switches** for the Ansible module tests to pass. Apstra only needs to:
1. Reach vCenter on port 443 to discover ESXi hosts (global VIM)
2. Have a blueprint node to bind the discovered `system_id` to (blueprint VIM)

### 4.2 Minimum Component List

| Component | Count | Notes |
|---|---|---|
| vCenter Server (VCSA) | 1 | VM is fine; needs port 443 reachable from `10.88.137.14` |
| ESXi host | 1 | Any version ≥ 6.7; managed by the vCenter above |
| VMs on ESXi | 1+ | Only needed to get results from `scope=query_vm` |
| DVS port-group | 1 | Optional; improves VLAN-match anomaly testing |

### 4.3 Service Account Permissions

Create a dedicated vCenter service account with **Read-Only** role at the
vCenter root level. This is sufficient for Apstra discovery.

Optional (for anomaly auto-resolution tests):
```
Host > Configuration > Network configuration
Network > Assign network
```

### 4.4 Network Requirements

| From | To | Port | Purpose |
|---|---|---|---|
| `10.88.137.14` (Apstra) | vCenter management IP | TCP 443 | VIM API polling |
| `10.88.137.14` (Apstra) | ESXi management IP | TCP 443 | Optional direct ESXi polling |

No connectivity needed between the ESXi host and the containerlab leaf switches
for Phase 1 module testing.

### 4.5 Information to Provide Back

```
vCenter hostname/IP  : ___________________________
vCenter username     : ___________________________
vCenter password     : ___________________________
ESXi host hostname   : ___________________________
ESXi host IP         : ___________________________
```

---

## 5. Adding ESXi Host to Existing Blueprint (Phase 2)

Once you have the ESXi `system_id` from Step 3 above, you need a blueprint
node to bind it to. **Do not use h1–h4** — those are Linux containers.

### Option A — Add a new generic system to existing blueprint (recommended)

In the Apstra UI on blueprint `vg-am-cops-tb-0`:

1. Go to **Physical → Generic Systems → Add Generic System**
2. Set hostname: `esxi-host-1`
3. Connect it to `leaf1 ge-0/0/6` (or any unused port)
4. Leave `system_id` empty — Apstra fills it when you POST `virtual_infra`

Or via Ansible after getting the `system_id`:

```yaml
- name: Bind ESXi host to blueprint virtual_infra
  juniper.apstra.virtual_infra_manager:
    id:
      blueprint: "vg-am-cops-tb-0"
    body:
      infra_type: "vcenter"
      system_id: "<esxi-host-uuid-from-discovery>"
    state: present
    auth_token: "{{ auth.token }}"
```

### Option B — Create a fresh test blueprint

Not needed — the test playbook already creates and destroys its own
fresh blueprint automatically on every run. You cannot pass `blueprint_id`
or `use_new_blueprint` as extra vars; the test is self-contained.

---

## 6. Testing Instructions (Developer)

### 6.1 Prerequisites

```bash
cd /home/vgavini/ACS/ansible_apstra/apstra-ansible-collection
source .env          # sets APSTRA_API_URL, APSTRA_USERNAME, APSTRA_PASSWORD
make install         # rebuilds and installs the collection
```

### Accepted extra vars (`-e`)

| Variable | Used in | Default (when omitted) |
|---|---|---|
| `vcenter_hostname` | Test 1, T4c VIM/vCenter hostname | `192.0.2.1` / `192.0.2.50` |
| `vcenter_username` | Test 1, T4c username | `testuser` / `vc-test@vsphere.local` |
| `vcenter_password` | Test 1, T4c password | `TestPass123!` / `VcTest123!` |
| `system_id` | Test 5 blueprint VIM assignment | Test 5 skipped (shows NOTE) |

> `blueprint_id` and `use_new_blueprint` are **not accepted** — the test
> always creates and deletes its own blueprint automatically.

### 6.2 Phase 1 — No vCenter Needed (Run Now)

```bash
make test-virtual_infra_manager
```

T1–T6, T5a must pass. T4c–T4f and T5b–T5d will be SKIPPED/ignored — expected.

### 6.3 Phase 2 — Global VIM with Real vCenter

Pass the three vcenter vars. Test 1 and T4c will use them instead of
the built-in dummy values:

```bash
make test-virtual_infra_manager ANSIBLE_FLAGS="-v \
  -e vcenter_hostname=<vcenter-ip-or-fqdn> \
  -e vcenter_username='admin@vsphere.local' \
  -e vcenter_password='<password>'"
```

Verify connection status (~60s after creation):

```bash
source .env
TOKEN=$(curl -sk -X POST "$APSTRA_API_URL/user/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$APSTRA_USERNAME\",\"password\":\"$APSTRA_PASSWORD\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

curl -sk -H "AuthToken: $TOKEN" "$APSTRA_API_URL/virtual-infra-managers" \
  | python3 -c "
import sys,json
for v in json.load(sys.stdin).get('virtual_infra_managers',[]):
    print(v.get('display_name'), '→ status:', v.get('status'), '| id:', v.get('id'))
"
```

Expected: `status: connected`

### 6.4 Phase 3 — Discover ESXi system_id

```bash
VIM_ID="<id-from-phase-2-output>"

curl -sk -H "AuthToken: $TOKEN" \
  "$APSTRA_API_URL/virtual-infra-managers/$VIM_ID/vcenters" \
  | python3 -c "
import sys,json
d=json.load(sys.stdin)
items=d.get('items', d if isinstance(d,list) else [])
for vc in items:
    print('vCenter id:', vc.get('id'), ' management_ip:', vc.get('management_ip'))
    for s in vc.get('systems', vc.get('hosts', [])):
        print(f\"  ESXi: {s.get('hostname','?')}  system_id: {s.get('id','?')}\")
"
```

Note the **ESXi host system_id** (UUID format). This is what goes into
`body.system_id` for the blueprint assignment.

### 6.5 Phase 4 — Blueprint Virtual Infra Assignment

The test creates its own fresh blueprint internally. You only need to pass
`system_id` (the ESXi UUID from Phase 3). The `blueprint_id` is set inside
the test automatically — do not pass it as an extra var.

```bash
make test-virtual_infra_manager ANSIBLE_FLAGS="-v \
  -e vcenter_hostname=<vcenter-ip> \
  -e vcenter_username='admin@vsphere.local' \
  -e vcenter_password='<password>' \
  -e system_id=<esxi-host-uuid-from-phase-3>"
```

When `system_id` is provided, Test 5 activates and executes:
```
POST /blueprints/{auto-created-blueprint-id}/virtual_infra
body: { infra_type: "vcenter", system_id: "<esxi-uuid>" }
```

### 6.6 Phase 5 — Full Scope Tests

After Phase 4 completes and VMs exist on the ESXi host:

```bash
# Query VMs (scope=query_vm)
cd /home/vgavini/ACS/ansible_apstra/apstra-ansible-collection
pipenv run ansible localhost -m juniper.apstra.virtual_infra_manager \
  -a "id={'blueprint':'e1d32dac-895f-4ae6-b27a-272dcef072a7'} scope=query_vm body={'filter':{}} state=present auth_token=$TOKEN"

# Trigger anomaly resolver (scope=anomaly_resolver)
pipenv run ansible localhost -m juniper.apstra.virtual_infra_manager \
  -a "id={'blueprint':'e1d32dac-895f-4ae6-b27a-272dcef072a7'} scope=anomaly_resolver body={'anomaly_ids':[]} state=present auth_token=$TOKEN"
```

---

## 7. Test Coverage by Phase

| Test | Phase | Requires |
|---|---|---|
| T1 — global create | 1 (now) | Apstra only |
| T2 — idempotent | 1 (now) | Apstra only |
| T3 — PATCH hostname | 1 (now) | Apstra only |
| T3b — PUT replace | 1 (now) | Apstra only |
| T4 — name resolution | 1 (now) | Apstra only |
| T4b — list vCenters | 1 (now) | Apstra only (returns empty) |
| **T4c — create vCenter** | **2** | Real vCenter reachable from Apstra |
| **T4d — get vCenter** | **2** | Real vCenter |
| **T4e — patch vCenter** | **2** | Real vCenter |
| **T4f — delete vCenter** | **2** | Real vCenter |
| T5a — list blueprint nodes | 1 (now) | Apstra only (returns empty) |
| **T5 — blueprint assignment** | **4** | vCenter connected + ESXi system_id |
| T5b — anomaly_resolver | 3 | VIM connected to blueprint |
| **T5c — query_vm** | **5** | VMs running on ESXi |
| T5d — vnet 404 path | 1 (now) | Apstra only |
| T6 — global delete | 1 (now) | Apstra only |

---

## 8. Quick Reference

```
Apstra URL:           https://10.88.137.14/api
Blueprint ID:         e1d32dac-895f-4ae6-b27a-272dcef072a7
Blueprint label:      vg-am-cops-tb-0
Containerlab host:    5d9s18-node4.englab.juniper.net
h1-h4:                Linux containers — NOT ESXi, irrelevant to vCenter
Leaf1 free ports:     ge-0/0/6+ (h1-h4 use ge-0/0/2-5)
VNs available:        green1, red1, cats1, dogs1 (all VXLAN)
Module test target:   make test-virtual_infra_manager
```
