import os
import shutil
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import UploadFile, HTTPException
from PIL import Image
import logging

logger = logging.getLogger(__name__)

class ProfilePicUploadHandler:
    def __init__(self):
        # Define paths
        self.temp_dir = Path("temp_uploads")
        self.uploads_dir = Path("uploads")
        self.public_uploads_dir = Path("public/uploads")
        
        # Create directories if they don't exist
        self.temp_dir.mkdir(exist_ok=True)
        self.uploads_dir.mkdir(exist_ok=True)
        self.public_uploads_dir.mkdir(parents=True, exist_ok=True)
        
        # Allowed file types
        self.allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        self.max_file_size = 5 * 1024 * 1024  # 5MB
        
    def validate_file(self, file: UploadFile) -> bool:
        """
        Validate uploaded file for image type and size
        """
        try:
            # Check if filename exists
            if not file.filename:
                raise HTTPException(status_code=400, detail="No filename provided")
            
            # Check file extension
            file_extension = Path(file.filename).suffix.lower()
            if file_extension not in self.allowed_extensions:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid file type. Allowed types: {', '.join(self.allowed_extensions)}"
                )
            
            # Check file size
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
            
            logger.info(f"File saved to temp: {temp_file_path}")
            return temp_file_path
            
        except Exception as e:
            logger.error(f"Error saving temp file: {e}")
            raise HTTPException(status_code=500, detail="Error saving file")
    
    def process_and_move_file(self, temp_file_path: Path, user_id: str) -> Dict[str, Any]:
        """
        Process image and move from temp to permanent location.
        Returns a dict with:
            - uploadfilename: str
            - uploadurl: str
            - filesize_bytes: int (file size in bytes)
            - filesize_kb: float (file size in kilobytes, rounded to 2 decimals)
        """
        try:
            # Open and validate image
            with Image.open(temp_file_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Generate final filename
                file_extension = temp_file_path.suffix.lower()
                final_filename = f"profile_{user_id}_{uuid.uuid4().hex[:8]}{file_extension}"
                final_file_path = self.uploads_dir / final_filename
                
                # Save processed image
                img.save(final_file_path, quality=85, optimize=True)
                
                # Get file size after processing
                file_size_bytes = final_file_path.stat().st_size
                file_size_kb = round(file_size_bytes / 1024, 2)
                
                # Remove temp file
                temp_file_path.unlink()
                
                # Create public URL path
                public_url = f"public/uploads/{final_filename}"
                
                logger.info(f"File processed and moved: {final_file_path}, size: {file_size_bytes} bytes ({file_size_kb} KB)")
                
                return {
                    "uploadfilename": final_filename,
                    "uploadurl": public_url,
                    "filesize_bytes": file_size_bytes,
                    "filesize_kb": file_size_kb
                }
                
        except Exception as e:
            # Clean up temp file on error
            if temp_file_path.exists():
                temp_file_path.unlink()
            
            logger.error(f"Error processing file: {e}")
            raise HTTPException(status_code=500, detail="Error processing image")
    
    async def upload_profile_pic(self, file: UploadFile, user_id: str) -> Dict[str, Any]:
        """
        Main method to handle profile picture upload.
        Returns a dict with:
            - uploadfilename: str
            - uploadurl: str
            - filesize_bytes: int (file size in bytes)
            - filesize_kb: float (file size in kilobytes, rounded to 2 decimals)
        """
        try:
            # Validate file
            self.validate_file(file)
            
            # Save to temp
            temp_file_path = self.save_temp_file(file)
            
            # Process and move to permanent location
            result = self.process_and_move_file(temp_file_path, user_id)
            
            logger.info(f"Profile picture uploaded successfully for user {user_id}")
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in upload_profile_pic: {e}")
            raise HTTPException(status_code=500, detail="Upload failed")
    
    def delete_profile_pic(self, filename: str) -> bool:
        """
        Delete profile picture file
        """
        try:
            file_path = self.uploads_dir / filename
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Profile picture deleted: {filename}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error deleting profile picture: {e}")
            return False

# Create global instance
profile_pic_handler = ProfilePicUploadHandler() 