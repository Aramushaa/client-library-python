import requests
from datetime import datetime

# === Basic Info ===
HEADERS = {"Content-Type": "application/json"}
ORCH_URL = "http://127.0.0.1:8441/orchestrator/mgmt/store"
AUTH_URL = "http://127.0.0.1:8445/authorization/mgmt/intracloud"
PROVIDER_SYSTEM = {
    "systemName": "quickstart-provider",
    "address": "127.0.0.1",
    "port": 7655
}
INTERFACE = "HTTP-INSECURE-JSON"

# === Services to Setup ===
SERVICES = [
    {"service": "hello-arrowhead", "method": "GET"},
    {"service": "echo", "method": "PUT"}
]

def register_orchestration(service, method):
    payload = {
        "serviceDefinition": {"serviceDefinition": service},
        "consumerSystem": {
            "systemName": "quickstart-consumer",
            "address": "127.0.0.1",
            "port": 7656
        },
        "providerSystem": PROVIDER_SYSTEM,
        "serviceInterfaceName": INTERFACE,
        "priority": 1,
        "instruction": {},
        "serviceUri": service if service != "hello-arrowhead" else "hello"
    }
    res = requests.post(ORCH_URL, headers=HEADERS, json=payload)
    print(f"[ORCH] {service}: {res.status_code} - {res.text}")

def register_authorization(service):
    payload = {
        "consumerId": 6,  # adjust based on DB or query dynamically
        "providerIdsWithInterfaceIds": [
            {
                "id": 5,  # provider ID = quickstart-provider
                "interfaces": [2]  # id=2 is HTTP-INSECURE-JSON
            }
        ],
        "serviceDefinitionId": 13 if service == "hello-arrowhead" else 14
    }
    res = requests.post(AUTH_URL, headers=HEADERS, json=payload)
    print(f"[AUTH] {service}: {res.status_code} - {res.text}")

# === Main Execution ===
for s in SERVICES:
    register_orchestration(s["service"], s["method"])
    register_authorization(s["service"])
