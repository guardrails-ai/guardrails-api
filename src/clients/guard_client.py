import os
from guardrails import Guard
from flask_sqlalchemy import SQLAlchemy
from src.classes.guard_struct import GuardStruct
from src.clients.postgres_client import GuardItem

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
    
    def get_guard(self, guard_name: str):
        return Guard.from_rail(self.rail_file)

    def get_guards(
        self,
        db: SQLAlchemy = None
    ):
        # TODO: fetch from postgres or w/e database
        guard_items = db.session.query(GuardItem).all()

        return [GuardStruct.from_dict(gi) for gi in guard_items]

    def create_guard(
        self,
        guard: GuardStruct,
        db: SQLAlchemy = None
    ):
        guard_item = GuardItem(
            name=guard.name,
            railspec=guard.railspec.to_dict(),
            num_reasks=guard.num_reasks
        )
        db.session.add(guard_item)
        db.session.commit()
        return guard
    
    def post_guard(
        self,
        payload: dict,
        db: SQLAlchemy = None
    ):
        # TODO: Upsert to postgres or w/e database
        guard = GuardStruct.from_request(payload)
        return self.create_guard(guard, db)
    
    def update_guard(
        self,
        guard_name: str,
        payload: dict,
        db: SQLAlchemy = None
    ):
        # TODO: Upsert to postgres or w/e database
        guard = GuardStruct.from_dict(payload)
        guard.name = guard_name
        return guard
    
    def put_guard(
        self,
        guard_name: str,
        payload: dict,
        db: SQLAlchemy = None
    ):
        # TODO: Upsert to postgres or w/e database
        guard = GuardStruct.from_request(payload)
        guard.name = guard_name
        return guard

    def delete_guard(
        self,
        guard_name: str,
        db: SQLAlchemy = None
    ):
        # TODO: Upsert to postgres or w/e database
        guard = GuardStruct.from_dict(mockGuard)
        guard.name = guard_name
        return guard
        