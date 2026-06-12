from fastapi.templating import Jinja2Templates

UPLOAD_DIR = "static/uploads"
APP_NAME = "Scotch & Bourbon"
APP_VERSION = "1.0.0"

templates = Jinja2Templates(directory="templates")
