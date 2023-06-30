class ValidationOutput:
    def __init__(self, result: bool, validated_output: str, history: list = None):
        self.result = result
        self.validated_output = validated_output
        self.history = history
    def to_response(self):
        return {
          'result': self.result,
          'validatedOutput': self.validated_output,
          'history': self.history
        }