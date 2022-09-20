from starlite import OpenAPIConfig, OpenAPIController


class OpenAPI(OpenAPIController):
    """`OpenAPI` controller."""


openapi_config = OpenAPIConfig(
    title="Shinji",
    version="0.1.0",
    description="An API for doing things.",
    summary="Just an API",
    use_handler_docstrings=True,
    root_schema_site="elements",
    openapi_controller=OpenAPI,
)
