from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_optional_user
from app.core.config import settings
from app.db.session import get_db
from app.models.link import Link
from app.models.user import User
from app.schemas.link import LinkCreate, LinkCreateResponse, LinkStatsResponse
from app.services.cache import (
    delete_link_cache,
)
from app.utils.code_generator import generate_short_code


router = APIRouter(prefix="/links", tags=["Links"])


def get_unique_short_code(db: Session) -> str:
    while True:
        short_code = generate_short_code(6)
        existing = db.query(Link).filter(Link.short_code == short_code).first()
        if not existing:
            return short_code


@router.post(
    "/shorten", response_model=LinkCreateResponse, status_code=status.HTTP_201_CREATED
)
def create_short_link(
    payload: LinkCreate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    custom_alias = payload.custom_alias.strip() if payload.custom_alias else None

    if payload.expires_at is not None:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        expires_at = (
            payload.expires_at.replace(tzinfo=None)
            if payload.expires_at.tzinfo
            else payload.expires_at
        )
        if expires_at <= now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="expires_at must be in the future",
            )
    else:
        expires_at = None

    if custom_alias:
        existing_alias = db.query(Link).filter(Link.short_code == custom_alias).first()
        if existing_alias:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Custom alias already exists",
            )
        short_code = custom_alias
    else:
        short_code = get_unique_short_code(db)

    new_link = Link(
        original_url=str(payload.original_url),
        project_name=payload.project_name,
        short_code=short_code,
        expires_at=expires_at,
        owner_id=current_user.id if current_user else None,
    )

    db.add(new_link)
    db.commit()
    db.refresh(new_link)

    return LinkCreateResponse(
        short_code=new_link.short_code,
        short_url=f"{settings.BASE_URL}/{new_link.short_code}",
        original_url=new_link.original_url,
        project_name=new_link.project_name,
        expires_at=new_link.expires_at,
    )


@router.get("/search", response_model=LinkCreateResponse)
def search_link_by_original_url(
    original_url: str = Query(..., description="Original URL to search"),
    db: Session = Depends(get_db),
):
    link = db.query(Link).filter(Link.original_url == original_url).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    return LinkCreateResponse(
        short_code=link.short_code,
        short_url=f"{settings.BASE_URL}/{link.short_code}",
        original_url=link.original_url,
        expires_at=link.expires_at,
    )


@router.get("/{short_code}/stats", response_model=LinkStatsResponse)
def get_link_stats(short_code: str, db: Session = Depends(get_db)):
    link = db.query(Link).filter(Link.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    return link


@router.put("/{short_code}", response_model=LinkCreateResponse)
def update_link(
    short_code: str,
    payload: LinkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    link = db.query(Link).filter(Link.short_code == short_code).first()

    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    if link.owner_id is None:
        raise HTTPException(
            status_code=403,
            detail="Anonymous links cannot be modified",
        )

    if link.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not allowed to modify this link",
        )

    link.original_url = str(payload.original_url)
    link.expires_at = payload.expires_at

    db.commit()
    db.refresh(link)

    delete_link_cache(short_code)

    return LinkCreateResponse(
        short_code=link.short_code,
        short_url=f"{settings.BASE_URL}/{link.short_code}",
        original_url=link.original_url,
        expires_at=link.expires_at,
    )


@router.delete("/{short_code}")
def delete_link(
    short_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    link = db.query(Link).filter(Link.short_code == short_code).first()

    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    if link.owner_id is None:
        raise HTTPException(
            status_code=403,
            detail="Anonymous links cannot be deleted",
        )

    if link.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not allowed to delete this link",
        )

    db.delete(link)
    db.commit()

    delete_link_cache(short_code)

    return {"message": "Link deleted"}


@router.get("/expired")
def get_expired_links(db: Session = Depends(get_db)):
    now = datetime.utcnow()

    expired_links = (
        db.query(Link)
        .filter(Link.expires_at.is_not(None))
        .filter(Link.expires_at < now)
        .all()
    )

    return expired_links


@router.get("/project/{project_name}")
def get_links_by_project(project_name: str, db: Session = Depends(get_db)):
    links = db.query(Link).filter(Link.project_name == project_name).all()
    return links
