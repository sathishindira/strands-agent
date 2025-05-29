import os
import re
import shutil

def fix_diagram_paths(content):
    """
    Fix diagram paths in content and ensure images are copied to the right location
    """
    if not content:
        return content
    
    # Create directories if they don't exist
    os.makedirs('./generated-diagrams', exist_ok=True)
    
    # Patterns to match different image path formats
    patterns = [
        r'sandbox:/tmp/generated-diagrams/([\w\-\.]+\.png)',
        r'/tmp/generated-diagrams/([\w\-\.]+\.png)',
        r'./generated-diagrams/([\w\-\.]+\.png)'
    ]
    
    # Extract all image filenames
    all_images = []
    for pattern in patterns:
        matches = re.findall(pattern, content)
        all_images.extend(matches)
    
    # Copy images to the correct location
    for img_name in all_images:
        source_paths = [
            f"/tmp/generated-diagrams/{img_name}",
            f"/app/generated-diagrams/{img_name}"
        ]
        
        dest_path = f"./generated-diagrams/{img_name}"
        
        # Copy from any source that exists
        for src_path in source_paths:
            if os.path.exists(src_path):
                try:
                    shutil.copy2(src_path, dest_path)
                    print(f"Copied {src_path} to {dest_path}")
                    break
                except Exception as e:
                    print(f"Error copying {src_path} to {dest_path}: {e}")
    
    # Replace paths in content
    fixed_content = content
    
    # Replace sandbox:/tmp/generated-diagrams/ with ./generated-diagrams/
    fixed_content = re.sub(
        r'sandbox:/tmp/generated-diagrams/([\w\-\.]+\.png)',
        r'./generated-diagrams/\1',
        fixed_content
    )
    
    # Replace /tmp/generated-diagrams/ with ./generated-diagrams/
    fixed_content = re.sub(
        r'/tmp/generated-diagrams/([\w\-\.]+\.png)',
        r'./generated-diagrams/\1',
        fixed_content
    )
    
    # Fix markdown image syntax
    fixed_content = re.sub(
        r'!\[(.*?)\]\(/tmp/generated-diagrams/(.*?)\)',
        r'![\1](./generated-diagrams/\2)',
        fixed_content
    )
    
    return fixed_content