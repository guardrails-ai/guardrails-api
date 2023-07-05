# guardrails-poc
Docker compose stub of Guardrails as a Service

## Diagrams
Two diagrams for two different approaches to the infrastructure for this project.

## Open API Spec
One main OpenAPI Spec for the basic endpoints discussed.  This was manually written for proof-of-concept purposes.  For the long run you can consider tools like the following to generate this documentation for you if you prefere to define your data objects in code:
  - [flask-rest-api](https://flask-rest-api.readthedocs.io/en/stable/openapi.html)
  - [apispec](https://apispec.readthedocs.io/en/latest/index.html)


## Note On Serialization And Pydantic Models
This API is intended to transact in serialized rail specs.  By default that means not explicitly supporting Pydantic models via the main endpoints.  There are two options to choose between if we are to retain support for Pydantic models:

1. Pydantic Models are client side only
2. Pydantic Models are server side plugins

Both of these approaches have merits and difficulties as listed below.

### Client Only Pydantic Models
In this scenario the user can still use Pydantic Models to capture their schema structure, but the model must have some standard way of being serialized.  In Pydantic 2.x, this is avaiable via the `model_dump` and `model_dump_json` methods depending on whether we need a dictionary or a json-encoded string.  The advantages of this approach is that the serialization can take place client side in the sdk and the server does not have to worry about special cases, it continues to only accept JSON as input.  What we do lose with this approach is any ability to define custom validations in the Pydantic model that can be executed by the server since the model only exists client side.  One way around this is through the use of sockets.  When the validation endpoint is called from the sdk, if the sdk knows there is a pydantic model involved, rather than performing a standard http request it can open a web socket or rpc connection instead.  Then on the server, when it doesn't find a particular validation in its registry, it can use the socket to request the sdk to run that validation instead.  This would require some addtional implementation to support this back and forth; we also wouldn't have an out-of-the-box way to collect telemetry on any validators run client-side.

### Pydantic Model Plugins
In this scenrio the user publishes thier Pydantic model to some registry that can be accessed via pip.  Then, in the railspec, the user specifies the module names for any custom validators.  When validation is called, a prepare step is used to install any of these dependencies and import them so that the registration annotations can be run.  This seems to be possible by using a combination of `pip` and `__import__` with some error handling.  It might even be possible to [host our own pip repository](https://packaging.python.org/en/latest/guides/hosting-your-own-index/) and auto-publish the user's pydantic models for them to this private registry.  This would put the user's custom code within the compliance scope of GuardRails rather than a public repository.

The benefits of this approach is that the custom validations and pydantic models for the schema(s) can be handled "natively" on the server.  There is no requirement for back-and-forth communication between the server and the sdk keeping each call atomic.  There is also the potential to automate most of the addtional work this approach requires of the user.

The difficulties of this approach are simply the additonal effort required to make the models available to the server.  In the simpler case the user must make this additional effort by packaging and publishing their models.  This also introduces the necessity to deal with various versions of the model through pip.  This approach also would require additional effort to isolate these custom modules if the server is multi-tenant; likely requiring an isolated run environment be created during runtime which can get complicated.  We would also want a cleanup process to run after validation to free up the space consumed by loading these modules.