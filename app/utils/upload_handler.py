import os
import shutil
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, Set
from fastapi import UploadFile, HTTPException
from PIL import Image
import logging

from app.core.enums import PicType,FileType,DocType

logger = logging.getLogger(__name__)

class FileUploadHandler:
    def __init__(self, 
            allowed_extensions: Optional[Set[str]] = None,
            max_file_size: int = 5 * 1024 * 1024,  # 5MB default
            temp_dir: str = "public/temp_uploads",
            uploads_dir: str = "public/uploads",
            file_type: str = "generic"):
        """
        Initialize file upload handler
        
        Args:
            allowed_extensions: Set of allowed file extensions (e.g., {'.jpg', '.png', '.pdf'})
            max_file_size: Maximum file size in bytes
            temp_dir: Temporary upload directory
            uploads_dir: Permanent upload directory
            file_type: Type oallowed_extensionsf files being handled (e.g., 'profile_pic', 'document', 'generic')
        """
        # Define pathsforgot_password_api_v1_auth_forgot_password_post
        self.temp_dir = Path(temp_dir)
        self.uploads_dir = Path(uploads_dir)
        self.public_uploads_dir = self.uploads_dir  # For compatibility
        self.file_type = file_type
        
        # Create directories if they don't exist
        #self.temp_dir.mkdir(parents=True, exist_ok=True)
        #self.uploads_dir.mkdir(parents=True, exist_ok=True)
        
        # Allowed file types (default to images)
        self.allowed_extensions = allowed_extensions or {e.value for e in PicType}
        self.max_file_size = max_file_size

    def validate_file(self, file: UploadFile) -> bool:
        """
        Validate uploaded file for type and size
        """
        try:
            # Check if filename exists
            #if not file.filename:
               # raise HTTPException(status_code=400, detail="No filename provided")
            
            # Check file extension
            file_extension = Path(file.filename).suffix.lower()
            if file_extension not in self.allowed_extensions:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid file type. Allowed types: {', '.join(self.allowed_extensions)}"
                )
            
            # Check file size if available (this is a preliminary check)
            if file.size and file.size > self.max_file_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large. Maximum size: {self.max_file_size // (1024*1024)}MB"
                )
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"File validation error: {e}")
            raise HTTPException(status_code=400, detail="Invalid file")
    
    def validate_file_size(self, file_path: Path) -> bool:
        """
        Validate file size after saving to ensure it doesn't exceed max_file_size
        """
        try:
            file_size = file_path.stat().st_size
            if file_size > self.max_file_size:
                # Delete the oversized file
                file_path.unlink()
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large. Maximum size: {self.max_file_size // (1024*1024)}MB. Your file: {file_size // (1024*1024)}MB"
                )
            return True
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"File size validation error: {e}")
            raise HTTPException(status_code=400, detail="Error validating file size")
    
    def save_temp_file(self, file: UploadFile) -> Path:
        """
        Save uploaded file to temporary directory
        """
        try:
            # Check if filename exists
            if not file.filename:
                raise HTTPException(status_code=400, detail="No filename provided")
            
            # Generate unique filename
            file_extension = Path(file.filename).suffix.lower()
            temp_filename = f"{uuid.uuid4()}{file_extension}"
            temp_file_path = self.temp_dir / temp_filename
            
            # Save file to temp directory
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Validate file size after saving
            self.validate_file_size(temp_file_path)
            
            #logger.info(f"File saved to temp: {temp_file_path}")
            return temp_file_path
            
        except Exception as e:
            logger.error(f"Error saving temp file: {e}")
            raise HTTPException(status_code=500, detail="Error saving file")
    
    async def upload_to_temp(self, file: UploadFile, user_id: str, prefix: str = "file") -> Dict[str, Any]:
        """
        Upload file to temp_uploads directory and return file information.
        
        Args:
            file: UploadFile object
            user_id: User identifier
            prefix: Prefix for filename (default: "file", use "profile" for profile pics)
            
        Returns a dict with:
            - uploadfilename: str
            - uploadurl: str
            - filesize_kb: float (file size in kilobytes, rounded to 2 decimals)
        """
        try:
            # Validate file
            self.validate_file(file)
            
            # Generate unique filename
            if not file.filename:
                raise HTTPException(status_code=400, detail="No filename provided")
            file_extension = Path(file.filename).suffix.lower()
            temp_filename = f"{prefix}_{user_id}_{uuid.uuid4().hex[:8]}{file_extension}"
            temp_file_path = self.temp_dir / temp_filename
            
            # Save file to temp directory
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Validate file size after saving
            self.validate_file_size(temp_file_path)
            
            # Get file size
            file_size_bytes = temp_file_path.stat().st_size
            file_size_kb = round(file_size_bytes / 1024, 2)
            
            # Create public URL path for temp file
            public_url = f"public/temp_uploads/{temp_filename}"
            
            logger.info(f"File uploaded to temp: {temp_file_path}, size: {file_size_bytes} bytes ({file_size_kb} KB)")
            
            return {
                "uploadfilename": temp_filename,
                "uploadurl": public_url,
                "filesize_kb": file_size_kb
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in upload_to_temp: {e}")
            raise HTTPException(status_code=500, detail="Upload failed")
    
    def process_and_move_file(self, temp_file_path: Path, user_id: str, prefix: str = "file", process_image: bool = False, original_filename: str = None) -> Dict[str, Any]:
        """
        Process file and move from temp to permanent location.
        
        Args:
            temp_file_path: Path to temporary file
            user_id: User identifier
            prefix: Prefix for filename (default: "file", use "profile" for profile pics)
            process_image: Whether to process as image (resize, optimize, etc.)
            
        Returns a dict with:
            - uploadfilename: str
            - uploadurl: str
            - filesize_bytes: int (file size in bytes)
            - filesize_kb: float (file size in kilobytes, rounded to 2 decimals)
        """
        try:
            # Generate final filename using the same UUID from temp
            file_extension = temp_file_path.suffix.lower()
            uuid_part = temp_file_path.stem.split('_')[-1] if '_' in temp_file_path.stem else temp_file_path.stem
            final_filename = f"{prefix}_{user_id}_{uuid_part}{file_extension}"
            final_file_path = self.uploads_dir / final_filename
            
            if process_image and file_extension in [e.value for e in FileType]:
                # Process image (resize, optimize, etc.)
                with Image.open(temp_file_path) as img:
                    # Convert to RGB if necessary
                    if img.mode in ('RGBA', 'LA', 'P'):
                        img = img.convert('RGB')
                    
                    # Save processed image
                    img.save(final_file_path, quality=85, optimize=True)
            else:
                # Move file without processing
                shutil.move(str(temp_file_path), str(final_file_path))
            
            # Get file size after processing/moving
            file_size_bytes = final_file_path.stat().st_size
            file_size_kb = round(file_size_bytes / 1024, 2)
            
            # Remove temp file
            temp_file_path.unlink()
            
            # Create public URL path
            public_url = f"public/uploads/{final_filename}"
            
            logger.info(f"File processed and moved: {final_file_path}, size: {file_size_bytes} bytes ({file_size_kb} KB)")
            
            return {
                "uploadfilename": final_filename,
                "original_filename": original_filename,
                "uploadurl": public_url,
                "filesize_bytes": file_size_bytes,
                "filesize_kb": file_size_kb
            }
                
        except Exception as e:
            # Clean up temp file on error
            if temp_file_path.exists():
                temp_file_path.unlink()
            
            logger.error(f"Error processing file: {e}")
            raise HTTPException(status_code=500, detail="Error processing file")
    
    async def upload_file(self, file: UploadFile, user_id: str, prefix: str = "file", process_image: bool = False) -> Dict[str, Any]:
        """
        Main method to handle file upload.
        
        Args:
            file: UploadFile object
            user_id: User identifier
            prefix: Prefix for filename (default: "file", use "profile" for profile pics)
            process_image: Whether to process as image (resize, optimize, etc.)
            
        Returns a dict with:
            - uploadfilename: str
            - uploadurl: str
            - filesize_bytes: int (file size in bytes)
            - filesize_kb: float (file size in kilobytes, rounded to 2 decimals)
        """
        try:
            # Validate file
            self.validate_file(file)
            original_filename = file.filename
            # Save to temp
            temp_file_path = self.save_temp_file(file)
            
            # Process and move to permanent location
            result = self.process_and_move_file(temp_file_path, user_id, prefix, process_image, original_filename=original_filename)
            
            logger.info(f"File uploaded successfully for user {user_id}")
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in upload_file: {e}")
            raise HTTPException(status_code=500, detail="Upload failed")
    
    
    
    
    def delete_file_by_path(self, file_path: str) -> bool:
        """
        Delete file by full path or URL
        Supports:
        - Full file paths: "/home/user/file.jpg"
        - Relative paths: "public/uploads/file.jpg"
        - URL paths: "public/temp_uploads/file.jpg"
        """
        try:
            # Convert to Path object
            path_obj = Path(file_path)
            
            # If it's already an absolute path, use it directly
            if path_obj.is_absolute():
                if path_obj.exists():
                    path_obj.unlink()
                    logger.info(f"File deleted by absolute path: {file_path}")
                    return True
                return False
            
            # Handle relative paths starting with "public/"
            if file_path.startswith("public/"):
                # Remove "public/" prefix and check both directories
                relative_path = file_path[8:]  # Remove "public/"
                
                # Try temp_uploads
                temp_file_path = self.temp_dir / relative_path
                if temp_file_path.exists():
                    temp_file_path.unlink()
                    logger.info(f"File deleted from temp by path: {file_path}")
                    return True
                
                # Try uploads
                uploads_file_path = self.uploads_dir / relative_path
                if uploads_file_path.exists():
                    uploads_file_path.unlink()
                    logger.info(f"File deleted from uploads by path: {file_path}")
                    return True
            
            # Try as relative path in current directories
            for base_dir in [self.temp_dir, self.uploads_dir]:
                full_path = base_dir / file_path
                if full_path.exists():
                    full_path.unlink()
                    logger.info(f"File deleted by relative path: {file_path}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting file by path: {e}")
            return False
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get file information by path or URL
        Returns file details or None if file doesn't exist
        """
        try:
            path_obj = Path(file_path)
            
            # Handle different path formats
            if path_obj.is_absolute():
                if not path_obj.exists():
                    return None
                file_path_obj = path_obj
            elif file_path.startswith("public/"):
                # Remove "public/" prefix
                relative_path = file_path[8:]
                file_path_obj = self.uploads_dir / relative_path
                if not file_path_obj.exists():
                    file_path_obj = self.temp_dir / relative_path
            else:
                # Try both directories
                file_path_obj = self.uploads_dir / file_path
                if not file_path_obj.exists():
                    file_path_obj = self.temp_dir / file_path
            
            if not file_path_obj.exists():
                return None
            
            # Get file stats
            stat = file_path_obj.stat()
            file_size_bytes = stat.st_size
            file_size_kb = round(file_size_bytes / 1024, 2)
            
            return {
                "filename": file_path_obj.name,
                "filepath": str(file_path_obj),
                #"filesize_bytes": file_size_bytes,
                "filesize_kb": file_size_kb,
                "extension": file_path_obj.suffix.lower(),
                "exists": True
            }
            
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return None

# Create global instances for different file types
profile_pic_handler = FileUploadHandler(
    allowed_extensions={e.value for e in PicType},
    max_file_size=5 * 1024 * 1024,  # 5MB
    file_type="profile_pic"
)

document_handler = FileUploadHandler(
    allowed_extensions=DocType,
    max_file_size=10 * 1024 * 1024,  # 10MB
    file_type="document"
)

generic_file_handler = FileUploadHandler(
    allowed_extensions= FileType,
    max_file_size=20 * 1024 * 1024,  # 20MB
    file_type="generic"
) 