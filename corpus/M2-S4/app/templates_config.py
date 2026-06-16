from jinja2 import Environment, FileSystemLoader
from starlette.templating import Jinja2Templates as _Base

class Templates:
    """Wrapper that works with jinja2 3.1.x + starlette 1.2.x"""
    def __init__(self, directory: str):
        self.env = Environment(
            loader=FileSystemLoader(directory),
            autoescape=True,
        )
    
    def TemplateResponse(self, name: str, context: dict):
        from starlette.responses import HTMLResponse
        template = self.env.get_template(name)
        html = template.render(**context)
        return HTMLResponse(html)

