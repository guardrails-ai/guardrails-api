class HealthCheck:
  def __init__(self, status: int, message: str):
    self.status = status
    self.message = message
  def toDict(self):
    return {
      'status': self.status,
      'message': self.message
    }