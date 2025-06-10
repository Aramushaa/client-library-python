#!/usr/bin/env python3
"""
quickstart_setup_insecure.py

A variant of the quickstart setup that:
  - Preserves the MySQL volume if it already exists (no more endless init loops)
  - Uses INSECURE (HTTP, no TLS) mode for faster local dev
  - Registers Arrowhead core systems and example services over HTTP-INSECURE-JSON
  - Simplifies client creation (no cert/key/cafile needed)

CHANGE NOTES:
  * Removed unconditional `docker volume rm mysql.quickstart`
  * Added conditional volume creation if `mysql.quickstart` doesn’t exist
  * Switched all `ServiceInterface` entries from SECURE to INSECURE
  * Changed access policies for example services to NOT_SECURE
  * Switched health-check requests from HTTPS → HTTP (no certs)
  * Simplified `SyncClient.create()` invocation (removed TLS params)
"""

import subprocess
import requests
import time
import socket
from typing import List

from arrowhead_client.dto import DTOMixin
from arrowhead_client.rules import OrchestrationRule
from arrowhead_client.service import ServiceInterface
from arrowhead_client.system import ArrowheadSystem
from arrowhead_client.service import Service
from arrowhead_client.client.core_system_defaults import default_config
from arrowhead_client.client.core_service_forms.client import ServiceRegistrationForm
from arrowhead_client.client.implementations import SyncClient

# -------------------------------------------------------------------
# Step 1: Tear down existing containers, but KEEP volumes intact
# -------------------------------------------------------------------
subprocess.run(['docker-compose', 'down'])

# -------------------------------------------------------------------
# Step 2: Create mysql.quickstart volume only if it doesn't already exist
# -------------------------------------------------------------------
vol_ls = subprocess.run(
    ['docker', 'volume', 'ls', '-q', '-f', 'name=mysql.quickstart'],
    capture_output=True, text=True
)
if not vol_ls.stdout.strip():
    # CHANGE: we're now conditionally creating the volume instead of destroying it each run
    subprocess.run(['docker', 'volume', 'create', '--name', 'mysql.quickstart'])
    print(">> Created mysql.quickstart volume")
else:
    print(">> mysql.quickstart volume already exists, skipping creation")

# -------------------------------------------------------------------
# Step 3: Start up all services
# -------------------------------------------------------------------
subprocess.run(['docker-compose', 'up', '-d'])

# -------------------------------------------------------------------
# Step 4: Wait for core systems to come online via HTTP (insecure)
# -------------------------------------------------------------------
print('Waiting for core systems to get online (insecure HTTP checks)…')
is_online = [False, False, False]
while True:
    try:
        if not is_online[0]:
            # CHANGE: HTTP, no SSL verification
            requests.get('http://127.0.0.1:8443/serviceregistry/echo', timeout=2)
            is_online[0] = True
            print('✔ Service Registry is online')
        if not is_online[1]:
            requests.get('http://127.0.0.1:8441/orchestrator/echo', timeout=2)
            is_online[1] = True
            print('✔ Orchestrator is online')
        if not is_online[2]:
            requests.get('http://127.0.0.1:8445/authorization/echo', timeout=2)
            is_online[2] = True
            print('✔ Authorization is online')
    except Exception:
        time.sleep(2)
    else:
        print('\nAll core systems are online!\n')
        break

# -------------------------------------------------------------------
# Step 5: Initialize Arrowhead client in INSECURE mode (no certs)
# -------------------------------------------------------------------
setup_client = SyncClient.create(
    system_name='sysop',
    address='127.0.0.1',
    port=1337
)

print('Setting up local cloud…')

# -------------------------------------------------------------------
# Prefix→config-key mapping to match default_config names
# -------------------------------------------------------------------
prefix_map = {
    'serviceregistry': 'service_registry',  # FIXED: map to underscore key
    'orchestrator': 'orchestrator',
    'authorization': 'authorization',
}


# -------------------------------------------------------------------
# Step 6: Store orchestration-management rules over HTTP-INSECURE-JSON
# -------------------------------------------------------------------
for svc_name, path, method in [
    ('mgmt_register_service', 'serviceregistry/mgmt', 'POST'),
    ('mgmt_get_systems', 'serviceregistry/mgmt/systems', 'GET'),
    ('mgmt_register_system', 'serviceregistry/mgmt/systems', 'POST'),
    ('mgmt_orchestration_store', 'orchestrator/mgmt/store', 'POST'),
    ('mgmt_authorization_store', 'authorization/mgmt/intracloud', 'POST'),
]:
    prefix = path.split('/')[0]
    cfg_key = prefix_map[prefix]  # USE the mapped key
    setup_client.orchestration_rules.store(
        OrchestrationRule(
            Service(
                svc_name,
                path,
                ServiceInterface.from_str('HTTP-INSECURE-JSON'),
            ),
            ArrowheadSystem(**default_config[cfg_key]),
            method,
        )
    )


# -------------------------------------------------------------------
# Step 7: Final client setup call
# -------------------------------------------------------------------
setup_client.setup()

# -------------------------------------------------------------------
# Step 8: Register example consumer & provider systems
# -------------------------------------------------------------------
consumer_system = ArrowheadSystem(
        system_name='quickstart-consumer',
        address='127.0.0.1',
        port=7656
)
provider_system = ArrowheadSystem(
        system_name='quickstart-provider',
        address='127.0.0.1',
        port=7655,
)

consumer_data = setup_client.consume_service(
    'mgmt_register_system', json=consumer_system.dto()
).read_json()
provider_data = setup_client.consume_service(
    'mgmt_register_system', json=provider_system.dto()
).read_json()

systems = {
    'consumer': (ArrowheadSystem.from_dto(consumer_data), consumer_data['id']),
    'provider': (ArrowheadSystem.from_dto(provider_data), provider_data['id']),
}

# -------------------------------------------------------------------
# Step 9: Register example services in insecure / NOT_SECURE mode
# -------------------------------------------------------------------
for svc_def, uri in [('hello-arrowhead','hello'), ('echo','echo')]:
    setup_client.consume_service(
        'mgmt_register_service',
        json=ServiceRegistrationForm.make(
            Service(
                svc_def,
                uri,
                ServiceInterface.from_str('HTTP-INSECURE-JSON'),  # CHANGE
                'NOT_SECURE',                                    # CHANGE
            ),
            systems['provider'][0],
        ).dto()
    )

print('✅ Local cloud setup finished!')
