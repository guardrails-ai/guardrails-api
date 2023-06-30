from guardrails import Guard
from src.classes.rail_spec_struct import RailSpecStruct
from src.models.guard_item import GuardItem

from src.utils.pluck import pluck

class GuardStruct:
    def __init__(
          self,
          name: str,
          railspec: RailSpecStruct,
          num_reasks: int = None
          # base_model: dict = None,
      ):
      self.name = name
      self.railspec = railspec
      self.num_reasks = num_reasks
      # self.base_model = base_model
    
    @classmethod
    def from_guard(cls, guard: Guard):
       return cls(
          'guard-1',
          RailSpecStruct.from_rail(guard.rail),
          guard.num_reasks
       )
    
    def to_guard(self) -> Guard:
       return

    @classmethod
    def from_dict(cls, guard: dict):
       name, railspec, num_reasks = pluck(
          guard,
          [  
            "name",
            "railspec",
            "num_reasks"
          ]
        )
       return cls(
          name,
          RailSpecStruct.from_dict(railspec),
          num_reasks
       )

    def to_dict(self) -> dict:
       return {
          "name": self.name,
          "railspec": self.railspec.to_dict(),
          "num_reasks": self.num_reasks
       }
    
    @classmethod
    def from_request(cls, guard: dict):
       name, railspec, num_reasks = pluck(
          guard,
          [  
            "name",
            "railspec",
            "numReasks"
          ]
        )
       return cls(
          name,
          RailSpecStruct.from_request(railspec),
          num_reasks
       )
    
    def to_response(self) -> dict:
       return {
          "name": self.name,
          "railspec": self.railspec.to_response(),
          "num_reasks": self.num_reasks
       }
    
    @classmethod
    def from_guard_item(cls, guard_item: GuardItem):
       return cls(
          guard_item.name,
          RailSpecStruct.from_dict(guard_item.railspec),
          guard_item.num_reasks
       )