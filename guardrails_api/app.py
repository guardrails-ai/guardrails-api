from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from guardrails import configure_logging
from guardrails_api.clients.cache_client import CacheClient
from guardrails_api.clients.postgres_client import postgres_is_enabled
from guardrails_api.otel import otel_is_disabled, initialize
from guardrails_api.utils.trace_server_start_if_enabled import (
    trace_server_start_if_enabled,
)
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from rich.console import Console
from rich.rule import Rule
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
from urllib.parse import urlparse
import importlib.util
import json
import os

# from pyinstrument import Profiler
# from pyinstrument.renderers.html import HTMLRenderer
# from pyinstrument.renderers.speedscope import SpeedscopeRenderer
# from starlette.middleware.base import RequestResponseEndpoint
# class ProfilingMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
#         """Profile the current request

#         Taken from https://pyinstrument.readthedocs.io/en/latest/guide.html#profile-a-web-request-in-fastapi
#         with small improvements.

#         """
#         # we map a profile type to a file extension, as well as a pyinstrument profile renderer
#         profile_type_to_ext = {"html": "html", "speedscope": "speedscope.json"}
#         profile_type_to_renderer = {
#             "html": HTMLRenderer,
#             "speedscope": SpeedscopeRenderer,
#         }

#         if request.headers.get("X-Profile-Request"):
#                 # The default profile format is speedscope
#                 profile_type = request.query_params.get("profile_format", "speedscope")

#                 # we profile the request along with all additional middlewares, by interrupting
#                 # the program every 1ms1 and records the entire stack at that point
#                 with Profiler(interval=0.001, async_mode="enabled") as profiler:
#                     response = await call_next(request)

#                 # we dump the profiling into a file
#                 # Generate a unique filename based on timestamp and request properties
#                 timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#                 method = request.method
#                 path = request.url.path.replace("/", "_").strip("_")
#                 extension = profile_type_to_ext[profile_type]
#                 filename = f"profile_{timestamp}_{method}_{path}.{extension}"

#                 # Ensure the profiling directory exists
#                 profiling_dir = "profiling"
#                 os.makedirs(profiling_dir, exist_ok=True)

#                 # Dump the profiling into a file
#                 renderer = profile_type_to_renderer[profile_type]()
#                 filepath = os.path.join(profiling_dir, filename)
#                 with open(filepath, "w") as out:
#                     out.write(profiler.output(renderer=renderer))

#                 return response
#         else:
#             return await call_next(request)


# Custom JSON encoder
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, set):
            return list(o)
        if callable(o):
            return str(o)
        return super().default(o)


# Custom middleware for reverse proxy
class ReverseProxyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        self_endpoint = os.environ.get("SELF_ENDPOINT", "http://localhost:8000")
        url = urlparse(self_endpoint)
        request.scope["scheme"] = url.scheme
        response = await call_next(request)
        return response


def register_config(config: Optional[str] = None):
    default_config_file = os.path.join(os.getcwd(), "./config.py")
    config_file = config or default_config_file
    config_file_path = os.path.abspath(config_file)
    if os.path.isfile(config_file_path):
        spec = importlib.util.spec_from_file_location("config", config_file_path)
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)


def create_app(
    env: Optional[str] = None, config: Optional[str] = None, port: Optional[int] = None
):
    trace_server_start_if_enabled()
    # used to print user-facing messages during server startup
    console = Console()

    if os.environ.get("APP_ENVIRONMENT") != "production":
        from dotenv import load_dotenv

        # Always load default env file, but let user specified file override it.
        default_env_file = os.path.join(os.path.dirname(__file__), "default.env")
        load_dotenv(default_env_file, override=True)

        if env:
            env_file_path = os.path.abspath(env)
            load_dotenv(env_file_path, override=True)

    set_port = port or os.environ.get("PORT", 8000)
    host = os.environ.get("HOST", "http://localhost")
    self_endpoint = os.environ.get("SELF_ENDPOINT", f"{host}:{set_port}")
    os.environ["SELF_ENDPOINT"] = self_endpoint

    register_config(config)

    app = FastAPI()

    # Initialize FastAPIInstrumentor
    FastAPIInstrumentor.instrument_app(app)

    # app.add_middleware(ProfilingMiddleware)

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add reverse proxy middleware
    app.add_middleware(ReverseProxyMiddleware)

    guardrails_log_level = os.environ.get("GUARDRAILS_LOG_LEVEL", "INFO")
    configure_logging(log_level=guardrails_log_level)

    if not otel_is_disabled():
        initialize()

    # if no pg_host is set, don't set up postgres
    if postgres_is_enabled():
        from guardrails_api.clients.postgres_client import PostgresClient

        pg_client = PostgresClient()
        pg_client.initialize(app)

    cache_client = CacheClient()
    cache_client.initialize(app)

    from guardrails_api.api.root import router as root_router
    from guardrails_api.api.guards import router as guards_router, guard_client

    app.include_router(root_router)
    app.include_router(guards_router)

    # Custom JSON encoder
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return JSONResponse(
            status_code=400,
            content={"message": str(exc)},
        )

    console.print(f"\n:rocket: Guardrails API is available at {self_endpoint}")
    console.print(
        f":book: Visit {self_endpoint}/docs to see available API endpoints.\n"
    )

    console.print(":green_circle: Active guards and OpenAI compatible endpoints:")

    guards = guard_client.get_guards()

    for g in guards:
        g_dict = g.to_dict()
        console.print(
            f"- Guard: [bold white]{g_dict.get('name')}[/bold white] {self_endpoint}/guards/{g_dict.get('name')}/openai/v1"
        )

    console.print("")
    console.print(
        Rule("[bold grey]Server Logs[/bold grey]", characters="=", style="white")
    )

    return app


if __name__ == "__main__":
    import uvicorn

    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
