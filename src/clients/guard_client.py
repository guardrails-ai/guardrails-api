import os
from guardrails import Guard
from flask_sqlalchemy import SQLAlchemy
from src.classes.guard_struct import GuardStruct

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
    
    def get_guard(self, guard_id: str):
        return Guard.from_rail(self.rail_file)

    def get_guards(
        self,
        db: SQLAlchemy = None
    ):
        # TODO: fetch from postgres or w/e database
        return [GuardStruct.from_dict(mockGuard)]

    def create_guard(
        self,
        payload: dict,
        db: SQLAlchemy = None
    ):
        # TODO: Upsert to postgres or w/e database
        guard = GuardStruct.from_dict(payload)
        return guard
        