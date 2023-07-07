from opentelemetry.sdk.resources import Resource

resource = Resource(attributes={
   'service.name': 'validation-loop'
})