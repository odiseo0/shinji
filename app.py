from starlite import Starlite, get


@get(path="/")
def index() -> str:
    """Index function that retuns a "Hello World"."""
    return "Hello World"


app = Starlite(route_handlers=[index])
