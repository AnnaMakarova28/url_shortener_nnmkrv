from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.auth import router as auth_router
from app.api.links import router as links_router
from app.db import base  # noqa: F401
from app.db.session import Base, engine, get_db
from app.models.link import Link
from app.services.cache import get_original_url_from_cache, set_original_url_to_cache


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="URL Shortener API",
    description=(
        "Сервис сокращения ссылок с регистрацией пользователей, "
        "аналитикой, кастомными alias, временем жизни ссылок и кэшированием."
    ),
    version="1.0.0",
)

app.include_router(auth_router)
app.include_router(links_router)


@app.get("/")
def root():
    return {
        "message": "URL Shortener API is running",
        "docs": "/docs",
    }


@app.get("/{short_code}")
def redirect_by_short_code(short_code: str, db: Session = Depends(get_db)):
    cached_url = get_original_url_from_cache(short_code)
    if cached_url:
        link = db.query(Link).filter(Link.short_code == short_code).first()
        if link:
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            if link.expires_at and link.expires_at < now:
                db.delete(link)
                db.commit()
                raise HTTPException(status_code=404, detail="Link has expired")

            link.clicks += 1
            link.last_used_at = now
            db.commit()

        return RedirectResponse(
            url=cached_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT
        )

    link = db.query(Link).filter(Link.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail="Short link not found")

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if link.expires_at and link.expires_at < now:
        db.delete(link)
        db.commit()
        raise HTTPException(status_code=404, detail="Link has expired")

    link.clicks += 1
    link.last_used_at = now
    db.commit()

    if link.clicks >= 3:
        set_original_url_to_cache(link.short_code, link.original_url)

    return RedirectResponse(
        url=link.original_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT
    )
