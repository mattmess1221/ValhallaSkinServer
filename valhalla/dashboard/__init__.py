import json
import warnings
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .. import models
from ..auth import current_user
from ..config import Env, settings

router = APIRouter(default_response_class=HTMLResponse, include_in_schema=False)

templates = Jinja2Templates(Path(__file__).parent / "templates")
templates.env.globals["settings"] = settings


def read_manifest():
    with open(dist / "manifest.json") as f:
        return json.load(f)


templates.env.globals["read_manifest"] = read_manifest

assets = None
dist = Path(__file__).parent / "dist"
if dist.exists():
    assets = StaticFiles(directory=dist, html=True)


elif settings.env == Env.PRODUCTION:
    warnings.warn(
        "The dashboard assets were not found. The dashboard may not work.",
        UserWarning,
        2,
    )


@router.route("/")
async def index(request: Request):
    return RedirectResponse("/dashboard", 308)


@router.get("/dashboard")
async def dashboard(
    request: Request,
    user: models.User = Depends(current_user),
):
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
        },
    )
