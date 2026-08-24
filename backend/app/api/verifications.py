import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.verification import VerificationCreate, VerificationRead
from app.services import image_service, verification_service
from app.utils.file_validation import validate_image_file

router = APIRouter(tags=["Verifications"])


@router.post(
    "/upload",
    response_model=VerificationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Packaged Product Image",
    description="Securely upload a packaged product image, validate integrity, store safely, and register a new Verification record.",
)
def upload_verification_image(
    file: UploadFile = File(..., description="Packaged product image file (JPG, PNG, WebP, max 10MB)"),
    product_id: Optional[uuid.UUID] = Form(default=None, description="Optional associated product ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VerificationRead:
    """Validate, store, and create a Verification record for an uploaded product image."""
    # 1. Validate image format, MIME type, size, and binary integrity
    image_bytes = validate_image_file(file)

    # 2. Persist image with sanitized UUID filename
    stored_path = image_service.save_image_file(
        content=image_bytes,
        original_filename=file.filename or "image.jpg",
    )

    # 3. Create Verification record; safely clean up file if database transaction fails
    try:
        verification_in = VerificationCreate(
            source_image_path=stored_path,
            product_id=product_id,
            inspector_id=current_user.id,
        )
        return verification_service.create_verification(db=db, verification_in=verification_in)
    except Exception:
        image_service.delete_image_file(stored_path)
        raise


@router.post(
    "",
    response_model=VerificationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Verification",
    description="Initiate a new product compliance verification run directly.",
)
def create_verification(
    verification_in: VerificationCreate,
    db: Session = Depends(get_db),
) -> VerificationRead:
    return verification_service.create_verification(db=db, verification_in=verification_in)


@router.get(
    "",
    response_model=List[VerificationRead],
    status_code=status.HTTP_200_OK,
    summary="List Verifications",
    description="Retrieve all product compliance verification runs.",
)
def list_verifications(
    db: Session = Depends(get_db),
) -> List[VerificationRead]:
    return verification_service.get_verifications(db=db)


@router.get(
    "/{id}",
    response_model=VerificationRead,
    status_code=status.HTTP_200_OK,
    summary="Get Verification",
    description="Retrieve a verification run by unique identifier.",
)
def get_verification(
    id: uuid.UUID,
    db: Session = Depends(get_db),
) -> VerificationRead:
    return verification_service.get_verification(db=db, verification_id=id)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Verification",
    description="Delete a verification run by unique identifier.",
)
def delete_verification(
    id: uuid.UUID,
    db: Session = Depends(get_db),
) -> None:
    verification_service.delete_verification(db=db, verification_id=id)
