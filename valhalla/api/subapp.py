import traceback

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from .. import limit


class SubApp(FastAPI):
    def setup(self) -> None:
        super().setup()

        limit.setup(self)
        self.add_exception_handler(Exception, self.exception_handler)

    def exception_handler(self, request: Request, exc: Exception) -> JSONResponse:
        traceback.print_exception(type(exc), exc, exc.__traceback__)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "detail": {
                    "type": exc.__class__.__name__,
                    "message": str(exc),
                },
            },
        )
