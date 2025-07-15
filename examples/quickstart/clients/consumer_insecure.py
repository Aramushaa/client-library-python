import time
from arrowhead_client.client.implementations import SyncClient
from arrowhead_client.errors import NoAvailableServicesError

consumer = SyncClient.create(
    system_name='quickstart-consumer',
    address='127.0.0.1',
    port=7656,
    service_registry_address='127.0.0.1',
    service_registry_port=8443,
    orchestrator_address='127.0.0.1',
    orchestrator_port=8441,
    authorization_address='127.0.0.1',
    authorization_port=8445,
)

if __name__ == '__main__':
    consumer.setup()

    service_found = False
    max_retries = 10
    retry_delay = 5

    print(f"Looking for 'hello-arrowhead' service ({max_retries} retries)...")

    for attempt in range(max_retries):
        try:
            consumer.add_orchestration_rule('hello-arrowhead', 'GET')
            response = consumer.consume_service('hello-arrowhead')
            print("hello-arrowhead response:", response.read_json()['msg'])
            service_found = True
            break
        except NoAvailableServicesError:
            print(f"[{attempt + 1}/{max_retries}] Service not available. Retrying in {retry_delay}s...")
            time.sleep(retry_delay)
        except Exception as e:
            print("Unexpected error:", e)
            break

    if not service_found:
        print("Could not connect to 'hello-arrowhead'. Is the provider running?")
    else:
        consumer.add_orchestration_rule('echo', 'PUT')
        echo_response = consumer.consume_service('echo', json={'msg': 'ECHO'})
        print("echo response:", echo_response.read_json()['msg'])
