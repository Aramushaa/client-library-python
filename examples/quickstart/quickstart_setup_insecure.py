# changelog
# - Removed all HTTPS usages (https:// -> http://)
# - Removed client certificates (cert, key, CA)
# - Disabled session.verify and session.cert
# - Replaced all SECURE interface strings -> replaced with INSECURE
# - Removed authentication_info from provider system
# - Replaced ServiceRegistrationForm.make(...) with direct constructor to avoid injecting 'secure'
# - Confirmed insecure services are registered with 'secure': 'NOT_SECURE'
# - Removed manual service registration, orchestration, and authorization from setup script
# - Services are now only registered by the running provider
# - This setup is now INSECURE for local dev/testing only

import subprocess
import requests
import time
from typing import List

from arrowhead_client.dto import DTOMixin
from arrowhead_client.rules import OrchestrationRule
from arrowhead_client.service import ServiceInterface
from arrowhead_client.system import ArrowheadSystem
from arrowhead_client.service import Service
from arrowhead_client.client.core_system_defaults import default_config
from arrowhead_client.client.implementations import SyncClient

subprocess.run(['docker-compose', 'down'])
subprocess.run(['docker', 'volume', 'rm', 'mysql.quickstart'])
subprocess.run(['docker', 'volume', 'create', '--name', 'mysql.quickstart'])
subprocess.run(['docker-compose', 'up', '-d'])

with requests.Session() as session:
    session.verify = False
    is_online = [False, False, False]
    print('Waiting for core systems to get online (might take a few minutes...)')
    while True:
        try:
            if not is_online[0]:
                session.get('http://127.0.0.1:8443/serviceregistry/echo')
                is_online[0] = True
                print('Service Registry is online')
            if not is_online[1]:
                session.get('http://127.0.0.1:8441/orchestrator/echo')
                is_online[1] = True
                print('Orchestrator is online')
            if not is_online[2]:
                session.get('http://127.0.0.1:8445/authorization/echo')
                is_online[2] = True
                print('Authorization is online')
        except Exception:
            time.sleep(2)
        else:
            print('All core systems are online\n')
            break

setup_client = SyncClient.create(
    system_name='sysop',
    address='127.0.0.1',
    port=1337,
)

print('Setting up local cloud')

setup_client.orchestration_rules.store(
    OrchestrationRule(
        Service('mgmt_register_service', 'serviceregistry/mgmt', ServiceInterface.from_str('HTTP-INSECURE-JSON')),
        ArrowheadSystem(**default_config['service_registry']),
        'POST',
    )
)

setup_client.orchestration_rules.store(
    OrchestrationRule(
        Service('mgmt_get_systems', 'serviceregistry/mgmt/systems', ServiceInterface('HTTP', 'INSECURE', 'JSON')),
        ArrowheadSystem(**default_config['service_registry']),
        'GET',
    )
)

setup_client.orchestration_rules.store(
    OrchestrationRule(
        Service('mgmt_register_system', 'serviceregistry/mgmt/systems', ServiceInterface('HTTP', 'INSECURE', 'JSON')),
        ArrowheadSystem(**default_config['service_registry']),
        'POST',
    )
)

setup_client.orchestration_rules.store(
    OrchestrationRule(
        Service('mgmt_orchestration_store', 'orchestrator/mgmt/store', ServiceInterface('HTTP', 'INSECURE', 'JSON')),
        ArrowheadSystem(**default_config['orchestrator']),
        'POST',
    )
)

setup_client.orchestration_rules.store(
    OrchestrationRule(
        Service('mgmt_authorization_store', 'authorization/mgmt/intracloud', ServiceInterface('HTTP', 'INSECURE', 'JSON')),
        ArrowheadSystem(**default_config['authorization']),
        'POST',
    )
)

setup_client.setup()

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

consumer_data = setup_client.consume_service('mgmt_register_system', json=consumer_system.dto()).read_json()
provider_data = setup_client.consume_service('mgmt_register_system', json=provider_system.dto()).read_json()

systems = {
    'consumer': (ArrowheadSystem.from_dto(consumer_data), consumer_data['id']),
    'provider': (ArrowheadSystem.from_dto(provider_data), provider_data['id']),
}

print('Local cloud insecure setup finished!')