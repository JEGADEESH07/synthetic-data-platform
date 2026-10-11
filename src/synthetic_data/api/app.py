from fastapi import FastAPI

from synthetic_data import __version__


app = FastAPI(
    title="Synthetic Data Engineering & Privacy Platform",
    version=__version__,
    description="V0.3 execution platform API.",
)


@app.get("/api/v1/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/api/v1/version")
def version() -> dict[str, str]:
    return {"version": __version__}