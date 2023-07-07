# API Client Libraries
Comparing our options for auto-generating client libraries from our OpenAPI Spec.

## Auto-rest
See setup and usage here: https://github.com/tinystacks/guardrails-poc/tree/autorest-sdk
### Summary
  - Open source (MIT License)
  - Developed by Microsoft
  - Uses mostly native libraries with a few Azure libraries
  - Runs in Node

### Pros
  - Lightweight: can be run via npx in any Node environment >= 12.x
  - Supports most OpenAPI Spec features
  - Supported by Microsoft since 2016
  - Simple setup and config
  - Can generate base setup.py file for packaging
### Cons
  - Requires some Azure libraries
  - Forces use of Azure credential classes for setting auth headers
  - Requires custom property on parameters to prevent them from being considered global
  - Does not generate pyproject.toml
  - Responses are generic JSON, not explicit models

## OpenAPITools openapi-generator
See setup and usage here: https://github.com/tinystacks/guardrails-poc/tree/open-api-generator
### Summary
  - Open source (Apache License)
  - Fork of Swagger Codegen
  - Runs in JVM

### Pros
  - Extensive support of OpenAPI Specification
  - Highly configurable
  - Likely the most mature OpenAPI code generator
  - Generates usage docs in markdown for the client

### Cons
  - Requires JVM to run
  - Specifically requires Java 11 for generating python clients
  - Historically, migrating between major version is toilsome
  - Documenation is extensive but difficult to navigate
  - Does not generate pyproject.toml
  - Responses are not easily serializeable
  - Boilerplate for making a call is excessive
  - Passing parameters is unintuitive and not well typed
  - !!! Cannot install alongside the guardrails-ai package !!! See error below

### Issues
The client generated with the latest version of openapi-generator has clashing dependencies with the guardrails-ai package.

```bash
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following dependency conflicts.
guardrails-api-client 1.0.0 requires typing_extensions~=4.3.0, but you have typing-extensions 4.7.1 which is incompatible.
```

This might be resolvable by downgrading to a previous version but that is not a desireable outcome.


## openapi-python-client
See setup and usage here: https://github.com/tinystacks/guardrails-poc/tree/openapi-python-client
### Summary
  - Open source (MIT License)
  - Runs in Python

### Pros
  - Python native
  - Uses Poetry to package
  - Generates pyproject.toml
  - Generates Models along with client

### Cons
  - Doesn't support default responses (generates build time warning)
  - Strict about schema contract (i.e. not required !== nullable)