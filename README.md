# guardrails-poc
Docker compose stub of Guardrails as a Service

## Diagrams
Two diagrams for two different approaches to the infrastructure for this project.

## Open API Spec
One main OpenAPI Spec for the basic endpoints discussed.  This was manually written for proof-of-concept purposes.  For the long run you can consider tools like the following to generate this documentation for you if you prefere to define your data objects in code:
  - [flask-rest-api](https://flask-rest-api.readthedocs.io/en/stable/openapi.html)
  - [apispec](https://apispec.readthedocs.io/en/latest/index.html)


## Notes On Serialization And Pydantic Models
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

## Notes On Data Auditing
Outside of our typical telemetry (metrics, logs, and traces) we also want to capture audit-style details about both the Guard objects (railspec configurations) and the data consumed and generated during validation.


### Auditing The Guards/Railspecs
The first is relatively simple; we can use the concepts of Functions and Triggers already built in to Postgres to capture a snapshot of the Guard object when writes occur.  These snapshots would be stored in their own table `guards_audit` and have all of the same columns as guards with the addition of a `replaced_on` timestamp column and `replaced_by` user id column to capture when it was updated and by whom.

The most straight forward way to allow users to query previous versions of these objects are to implement a `GET /guards/{guard-name}` endpoint with an optional `as-of` datetime query parameter.  This limits the results to only one guard and one version which should satisfy most auditing use cases.  For a more flexible search, we could add `start-date` and `end-date` datetime query paramters to this same endpoint.

### Auditing Validations
Auditing the data used during validation is slightly less simple because it requires additional server-side implementation.
Depending on what all we need to capture, we might be able to just persist the history object already generated by the sdk to a new postgres table.  In addtion to the json data the history object contains, we would also want to tag it with a start time, end time, whether the validations succeed or failed, the guard name, and if possible the trace-id for the request.  Starting out we can probaly just save this to a dedicate postgres table via SqlAlchemy before returning the results to the user.  In the long wrong though, since this data can potentially get rather large, we would want to send it to an asynchronous agent to handle while we return the result to the user.

This data has the potential to grow to a large size, both per row and number of rows.  The row, or really column, size is handled automatically if the data is stored in Postgres since it compresses large items automatically.  The number of rows however is more worrisome.  In the short term proper indexing should suffice.  In the long term it might make sense to move this data to something more wide-column/key-value oriented like DynamoDB or OpenSearch.

Exposing this data to a consumer could be accomplished via an endpoint like `GET /guards/audit/{guard-name}`.  Potential user specified query params are the time range (start and end datetimes) or the trace-id but not both since the trace implicitly specifies a time range/single document.  This endpoint would be a good candidate for GraphQL especially if the user wanted to query these audit records along with other telemetry.