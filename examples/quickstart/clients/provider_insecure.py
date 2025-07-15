from arrowhead_client.client.implementations import SyncClient
from arrowhead_client.client.core_service_forms.client import ServiceRegistrationForm
from arrowhead_client.system import ArrowheadSystem
import requests

provider = SyncClient.create(
    system_name='quickstart-provider',
    address='127.0.0.1',
    port=7655,
    authentication_info="",  # Required in insecure mode
    service_registry_address='127.0.0.1',
    service_registry_port=8443,
    orchestrator_address='127.0.0.1',
    orchestrator_port=8441,
    authorization_address='127.0.0.1',
    authorization_port=8445,
)

# Manual service registration (before setup)
session = requests.Session()
session.verify = False  # Disable cert check in insecure mode

def register(service_def, uri, method):
    form = ServiceRegistrationForm(
        service_definition=service_def,
        service_uri=uri,
        interfaces=['HTTP-INSECURE-JSON'],
        provider_system=ArrowheadSystem(
            system_name='quickstart-provider',
            address='127.0.0.1',
            port=7655,
            authentication_info=""
        )
    )
    res = session.post("http://127.0.0.1:8443/serviceregistry/mgmt", json=form.dto())
    print(f"[DEBUG] Registered {service_def}:", res.status_code, res.text)

register("hello-arrowhead", "hello", "GET")
register("echo", "echo", "PUT")

@provider.provided_service(
    service_definition='hello-arrowhead',
    service_uri='hello',
    protocol='HTTP',
    method='GET',
    payload_format='JSON',
    access_policy='NOT_SECURE'
)
def hello_arrowhead(request):
    return {"msg": "Hello, Arrowhead!"}

@provider.provided_service(
    service_definition='echo',
    service_uri='echo',
    protocol='HTTP',
    method='PUT',
    payload_format='JSON',
    access_policy='NOT_SECURE'
)
def echo(request):
    return request.read_json()

if __name__ == '__main__':
    try:
        provider.setup()
        provider.run_forever()
    except Exception as e:
        print("Error starting provider:", e)
