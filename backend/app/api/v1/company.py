from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.user import User
from app.models.company import CompanyProfile
from app.schemas.company import (
    CompanyProfileCreate,
    CompanyProfileUpdate,
    CompanyProfileResponse,
)
from app.schemas.auth import ApiResponse
from app.api.v1.auth import get_current_user_required

router = APIRouter(prefix="/company-profile", tags=["Company"])


@router.put("", response_model=ApiResponse)
async def update_company_profile(
    profile_data: CompanyProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
) -> ApiResponse:
    result = await db.execute(
        select(CompanyProfile).where(CompanyProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    update_data = profile_data.model_dump(exclude_unset=True)
    if profile:
        for key, value in update_data.items():
            setattr(profile, key, value)
    else:
        profile = CompanyProfile(
            user_id=current_user.id,
            **update_data,
        )
        db.add(profile)

    await db.commit()
    await db.refresh(profile)
    return ApiResponse(code=0, data=CompanyProfileResponse.model_validate(profile).model_dump(), message="ok")


@router.get("", response_model=ApiResponse)
async def get_company_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
) -> ApiResponse:
    result = await db.execute(
        select(CompanyProfile).where(CompanyProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        return ApiResponse(code=404, data=None, message="Company profile not found")

    return ApiResponse(code=0, data=CompanyProfileResponse.model_validate(profile).model_dump(), message="ok")