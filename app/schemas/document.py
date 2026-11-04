from typing import Literal

from pydantic import BaseModel, Field


class PermissionGrant(BaseModel):
    user_id: int = Field(gt=0)
    access_level: Literal["viewer", "editor"]


class PermissionResponse(BaseModel):
    document_id: int
    user_id: int
    access_level: Literal["viewer", "editor"]
    granted_by: int


class DocumentResponse(BaseModel):
    id: int
    original_filename: str
    content_type: str
    file_size: int
    owner_id: int
