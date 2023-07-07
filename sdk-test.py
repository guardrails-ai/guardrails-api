from guard_rails_api_client import Client
from guard_rails_api_client.api.guard import get_guards

client = Client(base_url="http://localhost:8000", follow_redirects=True)
guards = get_guards.sync(client=client)
print('guards: ', guards)
