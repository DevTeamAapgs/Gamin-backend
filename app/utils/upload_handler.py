import os
import shutil
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, Set
from fastapi import UploadFile, HTTPException
from PIL import Image
import logging

from app.core.enums import PicType, FileType, DocType

logger = logging.getLogger(__name__)

class FileUploadHandler:
    def __init__(self, 
                 allowed_extensions: Optional[Set[str]] = None,
                 max_file_size: int = 5 * 1024 * 1024,  # 5MB
                 temp_dir: str = "public/temp_uploads",
                 uploads_dir: str = "public/uploads",
                 file_type: str = "generic"):
        self.temp_dir = Path(temp_dir)
        self.uploads_dir = Path(uploads_dir)
        self.file_type = file_type
        self.allowed_extensions = allowed_extensions or {e.value for e in PicType}
        self.max_file_size = max_file_size

    def validate_file(self, file: UploadFile) -> bool:
        try:
            file_extension = Path(file.filename).suffix.lower()
            if file_extension not in self.allowed_extensions:
                raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {', '.join(self.allowed_extensions)}")
            if file.size and file.size > self.max_file_size:
                raise HTTPException(status_code=400, detail=f"File too large. Max: {self.max_file_size // (1024 * 1024)}MB")
            return True
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"File validation error: {e}")
            raise HTTPException(status_code=400, detail="Invalid file")

    def validate_file_size(self, file_path: Path) -> bool:
        try:
            size = file_path.stat().st_size
            if size > self.max_file_size:
                file_path.unlink()
                raise HTTPException(status_code=400, detail=f"File too large. Max: {self.max_file_size // (1024 * 1024)}MB")
            return True
        except Exception as e:
            logger.error(f"File size validation error: {e}")
            raise HTTPException(status_code=400, detail="Error validating file size")

    def save_temp_file(self, file: UploadFile) -> Path:
        try:
            if not file.filename:
                raise HTTPException(status_code=400, detail="No filename provided")
            ext = Path(file.filename).suffix.lower()
            temp_filename = f"{uuid.uuid4()}{ext}"
            temp_path = self.temp_dir / temp_filename
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            self.validate_file_size(temp_path)
            return temp_path
        except Exception as e:
            logger.error(f"Error saving temp file: {e}")
            raise HTTPException(status_code=500, detail="Error saving file")

    async def upload_to_temp(self, file: UploadFile, user_id: str, prefix: str = "file") -> Dict[str, Any]:
        try:
            self.validate_file(file)
            ext = Path(file.filename).suffix.lower()
            temp_filename = f"{prefix}_{user_id}_{uuid.uuid4().hex[:8]}{ext}"
            temp_path = self.temp_dir / temp_filename
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            self.validate_file_size(temp_path)
            size_kb = round(temp_path.stat().st_size / 1024, 2)
            return {
                "uploadfilename": temp_filename,
                "uploadurl": f"public/temp_uploads/{temp_filename}",
                "filesize_kb": size_kb
            }
        except Exception as e:
            logger.error(f"Upload to temp failed: {e}")
            raise HTTPException(status_code=500, detail="Upload failed")

    def process_and_move_file(self, temp_path: Path, user_id: str, prefix: str = "file", process_image: bool = False, original_filename: str = None) -> Dict[str, Any]:
        try:
            ext = temp_path.suffix.lower()
            uuid_part = temp_path.stem.split('_')[-1] if '_' in temp_path.stem else temp_path.stem
            final_name = f"{prefix}_{user_id}_{uuid_part}{ext}"
            final_path = self.uploads_dir / final_name

            if process_image and ext in [e.value for e in FileType]:
                with Image.open(temp_path) as img:
                    if img.mode in ('RGBA', 'LA', 'P'):
                        img = img.convert('RGB')
                    img.save(final_path, quality=85, optimize=True)
            else:
                shutil.move(str(temp_path), str(final_path))

            size_bytes = final_path.stat().st_size
            size_kb = round(size_bytes / 1024, 2)
            return {
                "uploadfilename": final_name,
                "original_filename": original_filename,
                "uploadurl": f"public/uploads/{final_name}",
                "filesize_bytes": size_bytes,
                "filesize_kb": size_kb
            }
        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            logger.error(f"Processing file failed: {e}")
            raise HTTPException(status_code=500, detail="Error processing file")

    async def upload_file(self, file: UploadFile, user_id: str, prefix: str = "file", process_image: bool = False) -> Dict[str, Any]:
        try:
            self.validate_file(file)
            original_filename = file.filename
            temp_path = self.save_temp_file(file)
            return self.process_and_move_file(temp_path, user_id, prefix, process_image, original_filename)
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            raise HTTPException(status_code=500, detail="Upload failed")

    def delete_file_by_path(self, file_path: str) -> bool:
        try:
            path_obj = Path(file_path.strip())
            if path_obj.is_absolute() and path_obj.exists():
                path_obj.unlink()
                return True

            if file_path.startswith("public/"):
                relative_path = Path(file_path).relative_to("public")
                for subdir in ["temp_uploads", "uploads"]:
                    candidate = Path("public") / subdir / relative_path.name
                    if candidate.exists():
                        candidate.unlink()
                        return True

            for base in [self.temp_dir, self.uploads_dir]:
                candidate = base / file_path
                if candidate.exists():
                    candidate.unlink()
                    return True

            return False
        except Exception as e:
            logger.error(f"Delete file failed: {e}")
            return False

    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        try:
            path_obj = Path(file_path.strip())
            if path_obj.is_absolute() and path_obj.exists():
                file = path_obj
            elif file_path.startswith("public/"):
                relative_path = Path(file_path).relative_to("public")
                file = self.uploads_dir / relative_path
                if not file.exists():
                    file = self.temp_dir / relative_path
            else:
                file = self.uploads_dir / file_path
                if not file.exists():
                    file = self.temp_dir / file_path

            if not file.exists():
                return None

            stat = file.stat()
            return {
                "filename": file.name,
                "filepath": str(file),
                "filesize_kb": round(stat.st_size / 1024, 2),
                "extension": file.suffix.lower(),
                "exists": True
            }
        except Exception as e:
            logger.error(f"Get file info failed: {e}")
            return None

# Global handlers
profile_pic_handler = FileUploadHandler(
    allowed_extensions={e.value for e in PicType},
    max_file_size=5 * 1024 * 1024,
    file_type="profile_pic"
)

document_handler = FileUploadHandler(
    allowed_extensions=DocType,
    max_file_size=10 * 1024 * 1024,
    file_type="document"
)

generic_file_handler = FileUploadHandler(
    allowed_extensions=FileType,
    max_file_size=20 * 1024 * 1024,
    file_type="generic"
)
