from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="Provenix")

    @app.get("/api/v1/ping")
    async def ping() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
