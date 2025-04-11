#!/usr/bin/env python
"""
Font Registration Script for ImageMagick

This script automatically registers all fonts from the project's font directories
to ImageMagick's configuration file. It helps ensure that MoviePy can properly use
custom fonts when rendering text in videos.
"""

import os
import re
import sys
import glob
import argparse
from xml.etree import ElementTree as ET
from xml.dom import minidom

# Constants
DEFAULT_IMAGEMAGICK_CONFIG_PATH = r"C:\Dev\ImageMagick\type-ghostscript.xml"
FONT_DIRS = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib", "fonts"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib", "fonts_emoji")
]
FONT_EXTENSIONS = [".ttf", ".otf", ".ttc"]

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Register fonts with ImageMagick for use with MoviePy.')
    parser.add_argument('-p', '--path', type=str, default=DEFAULT_IMAGEMAGICK_CONFIG_PATH,
                        help=f'Path to ImageMagick type-ghostscript.xml file (default: {DEFAULT_IMAGEMAGICK_CONFIG_PATH})')
    return parser.parse_args()

def prettify_xml(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def get_font_info(font_path):
    """Extract font information from the font path."""
    font_name = os.path.splitext(os.path.basename(font_path))[0]
    font_family = font_name.split('-')[0] if '-' in font_name else font_name
    
    # Determine style and weight based on font name
    style = "normal"
    weight = "400"
    
    if "Bold" in font_name or "Black" in font_name or "Heavy" in font_name:
        weight = "700"
    if "Italic" in font_name or "Oblique" in font_name:
        style = "italic"
    if "Light" in font_name or "Thin" in font_name:
        weight = "300"
    
    return {
        "name": font_name,
        "fullname": font_name.replace('-', ' '),
        "family": font_family,
        "style": style,
        "weight": weight,
        "path": font_path
    }

def find_all_fonts():
    """Find all font files in the specified directories."""
    fonts = []
    
    for font_dir in FONT_DIRS:
        if not os.path.exists(font_dir):
            print(f"⚠️ Font directory not found: {font_dir}")
            continue
        
        print(f"🔍 Scanning for fonts in: {font_dir}")
        for ext in FONT_EXTENSIONS:
            font_files = glob.glob(os.path.join(font_dir, f"*{ext}"))
            for font_file in font_files:
                fonts.append(get_font_info(font_file))
                print(f"  📝 Found font: {os.path.basename(font_file)}")
    
    return fonts

def parse_existing_config(config_path):
    """Parse the existing ImageMagick configuration file."""
    if not os.path.exists(config_path):
        print(f"❌ ImageMagick configuration file not found: {config_path}")
        return None
    
    try:
        tree = ET.parse(config_path)
        root = tree.getroot()
        return tree, root
    except Exception as e:
        print(f"❌ Error parsing ImageMagick configuration: {str(e)}")
        return None

def get_registered_font_names(root):
    """Get a list of already registered font names."""
    registered_fonts = []
    for type_elem in root.findall('type'):
        name = type_elem.get('name')
        if name:
            registered_fonts.append(name)
    return registered_fonts

def create_font_element(root, font_info):
    """Create a new font element for the XML tree."""
    font_elem = ET.SubElement(root, 'type')
    font_elem.set('name', font_info['name'])
    font_elem.set('fullname', font_info['fullname'])
    font_elem.set('family', font_info['family'])
    font_elem.set('style', font_info['style'])
    font_elem.set('weight', font_info['weight'])
    font_elem.set('stretch', 'normal')
    font_elem.set('format', 'type1')
    font_elem.set('metrics', font_info['path'])
    font_elem.set('glyphs', font_info['path'])
    return font_elem

def register_fonts(imagemagick_config_path):
    """Register all fonts from the project to ImageMagick's configuration."""
    # Find all fonts
    fonts = find_all_fonts()
    if not fonts:
        print("❌ No fonts found in the specified directories.")
        return False
    
    # Parse existing config
    result = parse_existing_config(imagemagick_config_path)
    if not result:
        return False
    
    tree, root = result
    
    # Get already registered fonts
    registered_fonts = get_registered_font_names(root)
    print(f"ℹ️ Found {len(registered_fonts)} already registered fonts.")
    
    # Register new fonts
    new_fonts_count = 0
    for font_info in fonts:
        if font_info['name'] in registered_fonts:
            print(f"✅ Font already registered: {font_info['name']}")
            continue
        
        create_font_element(root, font_info)
        new_fonts_count += 1
        print(f"➕ Registered new font: {font_info['name']}")
    
    if new_fonts_count == 0:
        print("ℹ️ All fonts are already registered.")
        return True
    
    # Save the updated configuration
    try:
        # Create a backup of the original file
        backup_path = f"{imagemagick_config_path}.bak"
        with open(imagemagick_config_path, 'r') as f_in:
            with open(backup_path, 'w') as f_out:
                f_out.write(f_in.read())
        print(f"✅ Created backup of original config: {backup_path}")
        
        # Write the updated XML
        tree.write(imagemagick_config_path, encoding='utf-8', xml_declaration=True)
        print(f"✅ Updated ImageMagick configuration with {new_fonts_count} new fonts.")
        return True
    except Exception as e:
        print(f"❌ Error updating ImageMagick configuration: {str(e)}")
        return False

def main():
    """Main function."""
    args = parse_args()
    imagemagick_config_path = args.path
    
    print("🔤 Font Registration Script for ImageMagick")
    print("=" * 50)
    print(f"📁 Using ImageMagick config: {imagemagick_config_path}")
    
    # Check if running with admin privileges
    try:
        # Try to write to the config file directory to check permissions
        test_path = os.path.join(os.path.dirname(imagemagick_config_path), "test_write_permission.tmp")
        with open(test_path, 'w') as f:
            f.write("test")
        os.remove(test_path)
    except PermissionError:
        print("❌ This script requires administrator privileges to modify ImageMagick configuration.")
        print("   Please run this script as administrator.")
        return 1
    
    success = register_fonts(imagemagick_config_path)
    
    if success:
        print("\n✅ Font registration completed successfully!")
        print("   You can now use these fonts in your videos.")
    else:
        print("\n❌ Font registration failed.")
        print("   Please check the error messages above.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
