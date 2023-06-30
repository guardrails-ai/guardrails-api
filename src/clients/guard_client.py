import os
from typing import List
from guardrails import Guard
from src.classes.guard_struct import GuardStruct
from src.models.guard_item import GuardItem
from src.clients.postgres_client import PostgresClient

mockGuard = {
   "name": "guard-1",
   "railspec": {
      "output_schema": {
         "schema": {
            "user_orders": {
               "element": {  
                  "type": "list",
                  "name": "user_orders",
                  "description": "Generate a list of user, and how many orders they have placed in the past.",
                  "on_fail": "noop"
               },
               "formatters": ["length: 1 10"],
               "children": {
                  "item": {
                      "user_id": {
                        "element": {
                           "type": "string",
                           "name": "user_id",
                           "description": "The user's id."
                        },
                        "formatters": []
                      },
                      "user_name": {
                        "element": {
                           "type": "string",
                           "name": "user_name",
                           "description": "The user's first name and last name"
                        },
                        "formatters": ["two-words"]
                      },
                      "num_orders": {
                        "element": {
                           "type": "integer",
                           "name": "num_orders",
                           "description": "The number of orders the user has placed"
                        },
                        "formatters": ["valid-range: 0 50"]
                      },
                      "city": {
                        "element": {
                           "type": "string",
                           "name": "city",
                           "description": "City where user lives"
                        },
                        "formatters": ["valid-choices: {['Chicago', 'SF', 'NY']}"]
                      },
                      "last_order_date": {
                        "element": {
                           "type": "date",
                           "name": "last_order_date",
                           "description": "Date of last order"
                        },
                        "formatters": []
                      },
                  }
               }
            }
         }
      },
      "prompt": """Generate a dataset of fake user orders. Each row of the dataset should be valid.

@complete_json_suffix""",
      "version": "0.1",
   },
   "num_reasks": 1
}

class GuardClient:
    def __init__(self):
        self.initialized = True
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, '../../rail-spec.xml')
        self.rail_file = os.path.abspath(filename)
        self.pgClient = PostgresClient()
    
    def get_guard(self, guard_name: str) -> GuardStruct:
        guard_item = self.pgClient.db.session.query(GuardItem).filter_by(name=guard_name).first()
        return GuardStruct.from_guard_item(guard_item)

    def get_guard_item(self, guard_name: str) -> GuardItem:
        return self.pgClient.db.session.query(GuardItem).filter_by(name=guard_name).first()

    def get_guards(
        self
    ) -> List[GuardStruct]:
        # TODO: fetch from postgres or w/e database
        guard_items = self.pgClient.db.session.query(GuardItem).all()

        return [GuardStruct.from_guard_item(gi) for gi in guard_items]

    def create_guard(
        self,
        guard: GuardStruct
    ) -> GuardStruct:
        guard_item = GuardItem(
            name=guard.name,
            railspec=guard.railspec.to_dict(),
            num_reasks=guard.num_reasks
        )
        self.pgClient.db.session.add(guard_item)
        self.pgClient.db.session.commit()
        return GuardStruct.from_guard_item(guard_item)
    
    def update_guard(
        self,
        guard_name: str,
        guard: GuardStruct
    ) -> GuardStruct:
        guard_item = self.get_guard_item(guard_name)
        guard_item.railspec = guard.railspec.to_dict()
        guard_item.num_reasks = guard.num_reasks
        self.pgClient.db.session.commit()
        return GuardStruct.from_guard_item(guard_item)

    def delete_guard(
        self,
        guard_name: str
    ) -> GuardStruct:
        guard_item = self.get_guard_item(guard_name)
        self.pgClient.db.session.delete(guard_item)
        self.pgClient.db.session.commit()
        guard = GuardStruct.from_guard_item(guard_item)
        return guard
        