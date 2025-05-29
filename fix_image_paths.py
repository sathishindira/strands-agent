import re
import os
import shutil

def fix_image_paths(response):
    """
    Replace sandbox:/tmp/generated-diagrams/ paths with ./generated-diagrams/
    and copy files if needed
    """
    if not response:
        return response
        
    # Extract all image filenames from various path formats
    image_patterns = [
        r'sandbox:/tmp/generated-diagrams/([\w\-\.]+\.png)',
        r'/tmp/generated-diagrams/([\w\-\.]+\.png)',
        r'./generated-diagrams/([\w\-\.]+\.png)'
    ]
    
    # Find all image filenames
    all_images = []
    for pattern in image_patterns:
        all_images.extend(re.findall(pattern, response))
    
    # Copy any images from /tmp to ./generated-diagrams if they exist
    for img_name in all_images:
        src_paths = [
            f"/tmp/generated-diagrams/{img_name}",
            f"/app/generated-diagrams/{img_name}"
        ]
        
        dst_path = f"./generated-diagrams/{img_name}"
        
        # Ensure the destination directory exists
        os.makedirs("./generated-diagrams", exist_ok=True)
        
        # Try to copy from any source path that exists
        for src_path in src_paths:
            if os.path.exists(src_path):
                try:
                    shutil.copy2(src_path, dst_path)
                    print(f"Copied {src_path} to {dst_path}")
                    break
                except Exception as e:
                    print(f"Error copying file: {e}")
    
    # Replace sandbox:/tmp/generated-diagrams/ with ./generated-diagrams/
    fixed_response = re.sub(
        r'sandbox:/tmp/generated-diagrams/([^)]+)',
        r'./generated-diagrams/\1',
        response
    )
    
    # Also fix markdown image paths like ![VPC Architecture Diagram](/tmp/generated-diagrams/vpc-architecture.png)
    fixed_response = re.sub(
        r'!\[(.*?)\]\(/tmp/generated-diagrams/([^)]+)\)',
        r'![\1](./generated-diagrams/\2)',
        fixed_response
    )
    
    return fixed_response