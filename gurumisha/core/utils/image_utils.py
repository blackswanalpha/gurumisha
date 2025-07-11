"""
Image handling utilities for Gurumisha Motors
"""
import os
import uuid
from PIL import Image, ImageOps
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
from io import BytesIO


def generate_unique_filename(filename):
    """Generate a unique filename while preserving the extension"""
    ext = filename.split('.')[-1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    return unique_filename


def validate_image_file(file):
    """
    Validate uploaded image file
    Returns: (is_valid, error_message)
    """
    # Check file size (2MB limit)
    max_size = 2 * 1024 * 1024  # 2MB
    if file.size > max_size:
        return False, "File size must be less than 2MB"
    
    # Check file type
    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
    if file.content_type not in allowed_types:
        return False, "Only JPEG, PNG, GIF, and WebP images are allowed"
    
    # Check file extension
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    file_extension = os.path.splitext(file.name)[1].lower()
    if file_extension not in allowed_extensions:
        return False, "Invalid file extension"
    
    try:
        # Try to open the image to verify it's valid
        image = Image.open(file)
        image.verify()
        return True, None
    except Exception:
        return False, "Invalid image file"


def resize_image(image_file, max_width=800, max_height=800, quality=85):
    """
    Resize image while maintaining aspect ratio
    """
    try:
        # Open the image
        image = Image.open(image_file)
        
        # Convert RGBA to RGB if necessary
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # Auto-orient the image based on EXIF data
        image = ImageOps.exif_transpose(image)
        
        # Calculate new dimensions
        original_width, original_height = image.size
        
        # Only resize if image is larger than max dimensions
        if original_width > max_width or original_height > max_height:
            # Calculate aspect ratio
            aspect_ratio = original_width / original_height
            
            if aspect_ratio > 1:  # Landscape
                new_width = min(max_width, original_width)
                new_height = int(new_width / aspect_ratio)
            else:  # Portrait or square
                new_height = min(max_height, original_height)
                new_width = int(new_height * aspect_ratio)
            
            # Resize the image
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Save to BytesIO
        output = BytesIO()
        image_format = 'JPEG'
        image.save(output, format=image_format, quality=quality, optimize=True)
        output.seek(0)
        
        return output
    except Exception as e:
        raise ValueError(f"Error processing image: {str(e)}")


def create_thumbnail(image_file, size=(150, 150)):
    """
    Create a thumbnail of the image
    """
    try:
        image = Image.open(image_file)
        
        # Convert RGBA to RGB if necessary
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # Auto-orient the image
        image = ImageOps.exif_transpose(image)
        
        # Create thumbnail
        image.thumbnail(size, Image.Resampling.LANCZOS)
        
        # Save to BytesIO
        output = BytesIO()
        image.save(output, format='JPEG', quality=90, optimize=True)
        output.seek(0)
        
        return output
    except Exception as e:
        raise ValueError(f"Error creating thumbnail: {str(e)}")


def process_profile_image(image_file, image_type='profile'):
    """
    Process uploaded profile image (resize, optimize, generate filename)
    
    Args:
        image_file: Uploaded file object
        image_type: 'profile', 'logo', or 'cover'
    
    Returns:
        tuple: (processed_file, filename, thumbnail_file, thumbnail_filename)
    """
    # Validate the image
    is_valid, error_message = validate_image_file(image_file)
    if not is_valid:
        raise ValueError(error_message)
    
    # Set dimensions based on image type
    if image_type == 'profile':
        max_width, max_height = 400, 400
        thumb_size = (150, 150)
    elif image_type == 'logo':
        max_width, max_height = 300, 300
        thumb_size = (100, 100)
    elif image_type == 'cover':
        max_width, max_height = 1200, 400
        thumb_size = (300, 100)
    else:
        max_width, max_height = 800, 800
        thumb_size = (150, 150)
    
    # Generate unique filename
    original_filename = image_file.name
    unique_filename = generate_unique_filename(original_filename)
    
    # Process main image
    try:
        processed_image = resize_image(image_file, max_width, max_height)
        processed_file = ContentFile(processed_image.getvalue(), name=unique_filename)
        
        # Create thumbnail
        image_file.seek(0)  # Reset file pointer
        thumbnail_image = create_thumbnail(image_file, thumb_size)
        thumbnail_filename = f"thumb_{unique_filename}"
        thumbnail_file = ContentFile(thumbnail_image.getvalue(), name=thumbnail_filename)
        
        return processed_file, unique_filename, thumbnail_file, thumbnail_filename
        
    except Exception as e:
        raise ValueError(f"Error processing image: {str(e)}")


def delete_image_files(image_path, thumbnail_path=None):
    """
    Delete image files from storage
    """
    try:
        if image_path and default_storage.exists(image_path):
            default_storage.delete(image_path)
        
        if thumbnail_path and default_storage.exists(thumbnail_path):
            default_storage.delete(thumbnail_path)
            
        return True
    except Exception:
        return False


def get_image_info(image_file):
    """
    Get information about an image file
    """
    try:
        image = Image.open(image_file)
        return {
            'width': image.width,
            'height': image.height,
            'format': image.format,
            'mode': image.mode,
            'size_bytes': image_file.size if hasattr(image_file, 'size') else None
        }
    except Exception:
        return None


class ImageUploadHandler:
    """
    Class to handle image uploads with validation and processing
    """
    
    def __init__(self, max_size_mb=2, allowed_formats=None):
        self.max_size = max_size_mb * 1024 * 1024  # Convert to bytes
        self.allowed_formats = allowed_formats or ['JPEG', 'PNG', 'GIF', 'WEBP']
    
    def validate(self, image_file):
        """Validate uploaded image"""
        return validate_image_file(image_file)
    
    def process(self, image_file, image_type='profile'):
        """Process uploaded image"""
        return process_profile_image(image_file, image_type)
    
    def cleanup(self, old_image_path, old_thumbnail_path=None):
        """Clean up old image files"""
        return delete_image_files(old_image_path, old_thumbnail_path)


# Default image upload handler instance
default_image_handler = ImageUploadHandler()
