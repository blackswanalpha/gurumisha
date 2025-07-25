"""
Image optimization utilities for the enhanced gallery system
"""
import os
from PIL import Image, ImageOps
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from io import BytesIO
import uuid


class ImageOptimizer:
    """Enhanced image optimization for car gallery"""
    
    # Image size configurations
    SIZES = {
        'thumbnail': (150, 150),
        'medium': (400, 300),
        'large': (800, 600),
        'original': None  # Keep original size
    }
    
    # Quality settings
    QUALITY = {
        'thumbnail': 85,
        'medium': 90,
        'large': 95,
        'original': 95
    }
    
    # Maximum file sizes (in bytes)
    MAX_SIZES = {
        'thumbnail': 50 * 1024,      # 50KB
        'medium': 200 * 1024,        # 200KB
        'large': 500 * 1024,         # 500KB
        'original': 5 * 1024 * 1024  # 5MB
    }
    
    @classmethod
    def optimize_image(cls, image_file, size_type='large'):
        """
        Optimize an image for the specified size type
        
        Args:
            image_file: Django UploadedFile or file-like object
            size_type: One of 'thumbnail', 'medium', 'large', 'original'
            
        Returns:
            ContentFile: Optimized image file
        """
        try:
            # Open the image
            img = Image.open(image_file)
            
            # Convert to RGB if necessary (handles RGBA, P mode images)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Auto-orient based on EXIF data
            img = ImageOps.exif_transpose(img)
            
            # Get target size and quality
            target_size = cls.SIZES.get(size_type)
            quality = cls.QUALITY.get(size_type, 90)
            
            # Resize if target size is specified
            if target_size:
                # Calculate aspect ratio preserving resize
                img.thumbnail(target_size, Image.Resampling.LANCZOS)
            
            # Save optimized image to BytesIO
            output = BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            output.seek(0)
            
            # Generate filename
            original_name = getattr(image_file, 'name', 'image.jpg')
            name, ext = os.path.splitext(original_name)
            optimized_name = f"{name}_{size_type}.jpg"
            
            return ContentFile(output.getvalue(), name=optimized_name)
            
        except Exception as e:
            raise ValueError(f"Error optimizing image: {str(e)}")
    
    @classmethod
    def validate_image(cls, image_file):
        """
        Validate image file before processing
        
        Args:
            image_file: Django UploadedFile
            
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            # Check file size
            if image_file.size > cls.MAX_SIZES['original']:
                return False, f"Image file size cannot exceed {cls.MAX_SIZES['original'] // (1024*1024)}MB"
            
            # Check file type
            if not image_file.content_type.startswith('image/'):
                return False, "Please upload a valid image file"
            
            # Try to open with PIL to validate
            img = Image.open(image_file)
            img.verify()
            
            # Reset file pointer after verify
            image_file.seek(0)
            
            # Check minimum dimensions
            img = Image.open(image_file)
            if img.width < 200 or img.height < 200:
                return False, "Image must be at least 200x200 pixels"
            
            # Reset file pointer
            image_file.seek(0)
            
            return True, None
            
        except Exception as e:
            return False, f"Invalid image file: {str(e)}"
    
    @classmethod
    def generate_variants(cls, image_file):
        """
        Generate all size variants for an image
        
        Args:
            image_file: Django UploadedFile
            
        Returns:
            dict: Dictionary of size_type -> ContentFile
        """
        variants = {}
        
        for size_type in cls.SIZES.keys():
            try:
                # Reset file pointer
                image_file.seek(0)
                
                # Generate variant
                variant = cls.optimize_image(image_file, size_type)
                variants[size_type] = variant
                
            except Exception as e:
                print(f"Error generating {size_type} variant: {str(e)}")
                continue
        
        return variants
    
    @classmethod
    def get_upload_path(cls, instance, filename, size_type='original'):
        """
        Generate upload path for image variants
        
        Args:
            instance: Model instance
            filename: Original filename
            size_type: Size variant type
            
        Returns:
            str: Upload path
        """
        # Generate unique filename
        name, ext = os.path.splitext(filename)
        unique_id = str(uuid.uuid4())[:8]
        
        if size_type == 'original':
            new_filename = f"{unique_id}_{name}.jpg"
        else:
            new_filename = f"{unique_id}_{name}_{size_type}.jpg"
        
        return f"cars/gallery/{new_filename}"


def optimize_car_image(image_file):
    """
    Convenience function to optimize a car image
    
    Args:
        image_file: Django UploadedFile
        
    Returns:
        ContentFile: Optimized image
    """
    return ImageOptimizer.optimize_image(image_file, 'large')


def validate_car_image(image_file):
    """
    Convenience function to validate a car image
    
    Args:
        image_file: Django UploadedFile
        
    Returns:
        tuple: (is_valid, error_message)
    """
    return ImageOptimizer.validate_image(image_file)


def create_thumbnail(image_file):
    """
    Create a thumbnail version of an image
    
    Args:
        image_file: Django UploadedFile or file path
        
    Returns:
        ContentFile: Thumbnail image
    """
    return ImageOptimizer.optimize_image(image_file, 'thumbnail')
