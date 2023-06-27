class HttpError:
  def __init__(self, status: int, message: str, cause: str = None, fields: dict = None, context: str = None):
    self.status = status
    self.message = message
    self.cause = cause
    self.fields = fields
    self.context = context
  
  def toDict(self):
    return {
      'status': self.status,
      'message': self.message,
      'cause': self.cause,
      'fields': self.fields,
      'context': self.context
    }