from guardrails import Guard
from src.classes.rail_spec_struct import RailSpecStruct

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

    def to_dict(self):
       return {
          self.name,
          self.railspec.to_dict(),
          self.num_reasks
       }