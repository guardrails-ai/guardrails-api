from guard_rails_api_client import AuthenticatedClient
from guard_rails_api_client.api.guard import get_guards

client = AuthenticatedClient(base_url="http://localhost:8000", follow_redirects=True, token="test-token")
guards = get_guards.sync(client=client)
guards_json = [g.to_dict() for g in guards]
print('guards: ', guards_json)
