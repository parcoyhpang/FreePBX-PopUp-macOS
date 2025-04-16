#!/usr/bin/env python3
"""
Run script for FreePBX Popup Client - Main entry point for launching the application.
Handles initialization, configuration, and resource setup before starting the main app.
"""

import os
import sys
import signal
import subprocess

def run_app():
    """Run the FreePBX Popup Client"""
    print("Starting FreePBX Popup Client...")

    import platform
    if platform.system() == 'Darwin':
        try:
            import objc
            from Foundation import NSBundle
            bundle = NSBundle.mainBundle()
            info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
            info['LSUIElement'] = '1'
            print("Hiding dock icon")
        except Exception as e:
            print(f"Failed to hide dock icon: {e}")

    config_path = os.path.expanduser('~/Library/Application Support/FreePBXPopup/config.json')
    if not os.path.exists(config_path):
        print("Configuration file not found. Creating default configuration...")
        create_default_config()

    # Check if we're running from a packaged app
    is_frozen = getattr(sys, 'frozen', False)

    if not is_frozen:
        # Only create icons and install requirements when running from source
        icon_path = os.path.join('resources', 'icon.png')
        if not os.path.exists(icon_path) or os.path.getsize(icon_path) < 1000:
            print("Icon not found or invalid. Creating icon...")
            create_icon()

        install_requirements()
    else:
        print("Running from packaged app, skipping resource creation and dependency installation.")

    print("Running application...")
    try:
        def signal_handler(sig, frame):
            print("Received signal to terminate. Shutting down...")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        from asterisk_popup.main import main
        main()
    except KeyboardInterrupt:
        print("Keyboard interrupt received. Shutting down...")
    except Exception as e:
        print(f"Error running application: {e}")

    print("Application terminated.")

def create_default_config():
    """Create default configuration file"""
    try:
        import json

        config = {
            'ami': {
                'host': 'localhost',
                'port': 5038,
                'username': 'admin',
                'secret': '',
                'auto_connect': True
            },
            'notifications': {
                'sound': 'default',
                'custom_sound_path': '',
                'show_missed_calls': True,
                'auto_dismiss': False,
                'auto_dismiss_timeout': 10
            },
            'extensions': {
                'monitor_all': True,
                'extensions_to_monitor': []
            },
            'general': {
                'start_at_login': True,
                'log_level': 'INFO'
            },
            'ui': {
                'theme': 'system',
                'show_in_dock': False
            }
        }

        config_dir = os.path.expanduser('~/Library/Application Support/FreePBXPopup')
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        config_path = os.path.join(config_dir, 'config.json')
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)

        print(f"Default configuration created at {config_path}")
    except Exception as e:
        print(f"Error creating default configuration: {e}")

def create_icon():
    """Create icon for the application"""
    try:
        if not os.path.exists('resources'):
            os.makedirs('resources')

        try:
            create_fa_icon()
        except Exception as e:
            print(f"Failed to create Font Awesome icon: {e}")
            create_simple_icon()
    except Exception as e:
        print(f"Error creating icon: {e}")

def create_fa_icon():
    """Create a Font Awesome icon"""
    try:
        try:
            import cairosvg
        except ImportError:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'cairosvg'])
            import cairosvg

        try:
            from PIL import Image
        except ImportError:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'Pillow'])
            from PIL import Image

        import io

        phone_icon_svg = """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
        <path fill="#3498db" d="M164.9 24.6c-7.7-18.6-28-28.5-47.4-23.2l-88 24C12.1 30.2 0 46 0 64C0 311.4 200.6 512 448 512c18 0 33.8-12.1 38.6-29.5l24-88c5.3-19.4-4.6-39.7-23.2-47.4l-96-40c-16.3-6.8-35.2-2.1-46.3 11.6L304.7 368C234.3 334.7 177.3 277.7 144 207.3L193.3 167c13.7-11.2 18.4-30 11.6-46.3l-40-96z"/>
        </svg>
        """

        png_data = cairosvg.svg2png(bytestring=phone_icon_svg.encode('utf-8'),
                                   output_width=128,
                                   output_height=128)

        img = Image.open(io.BytesIO(png_data))
        img.save('resources/icon.png')

        create_white_menu_bar_icon()

        print("Font Awesome icon created at resources/icon.png")
    except Exception as e:
        print(f"Error creating Font Awesome icon: {e}")
        raise

def create_white_menu_bar_icon():
    """Create a white menu bar icon"""
    try:
        try:
            import cairosvg
        except ImportError:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'cairosvg'])
            import cairosvg

        try:
            from PIL import Image
        except ImportError:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'Pillow'])
            from PIL import Image

        import io

        phone_icon_svg = """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
        <path fill="#FFFFFF" d="M164.9 24.6c-7.7-18.6-28-28.5-47.4-23.2l-88 24C12.1 30.2 0 46 0 64C0 311.4 200.6 512 448 512c18 0 33.8-12.1 38.6-29.5l24-88c5.3-19.4-4.6-39.7-23.2-47.4l-96-40c-16.3-6.8-35.2-2.1-46.3 11.6L304.7 368C234.3 334.7 177.3 277.7 144 207.3L193.3 167c13.7-11.2 18.4-30 11.6-46.3l-40-96z"/>
        </svg>
        """

        png_data = cairosvg.svg2png(bytestring=phone_icon_svg.encode('utf-8'),
                                   output_width=22,
                                   output_height=22)

        img = Image.open(io.BytesIO(png_data))

        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        img.save('resources/menu_bar_icon.png')

        print("White menu bar icon created at resources/menu_bar_icon.png")
    except Exception as e:
        print(f"Error creating white menu bar icon: {e}")

def create_simple_icon():
    """Create a simple icon"""
    try:
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'Pillow'])
            from PIL import Image, ImageDraw

        img = Image.new('RGBA', (128, 128), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        padding = 16

        draw.rounded_rectangle(
            [(padding, padding), (128 - padding, 128 - padding)],
            radius=12,
            fill=(52, 152, 219)  # Blue color
        )

        center_x = 128 // 2
        center_y = 128 // 2
        circle_radius = 128 // 5
        draw.ellipse(
            [(center_x - circle_radius, center_y - circle_radius),
             (center_x + circle_radius, center_y + circle_radius)],
            fill=(255, 255, 255)  # White
        )

        inner_radius = circle_radius // 2
        draw.ellipse(
            [(center_x - inner_radius, center_y - inner_radius),
             (center_x + inner_radius, center_y + inner_radius)],
            fill=(41, 128, 185)  # Darker blue
        )

        img.save('resources/icon.png')

        create_white_menu_bar_icon_simple()

        print("Simple icon created at resources/icon.png")
    except Exception as e:
        print(f"Error creating simple icon: {e}")

def create_white_menu_bar_icon_simple():
    """Create a white menu bar icon from the simple icon"""
    try:
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'Pillow'])
            from PIL import Image, ImageDraw

        img = Image.new('RGBA', (22, 22), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        padding = 2

        draw.rounded_rectangle(
            [(padding, padding), (22 - padding, 22 - padding)],
            radius=3,
            fill=(255, 255, 255)  # White color
        )

        center_x = 22 // 2
        center_y = 22 // 2
        circle_radius = 22 // 6
        draw.ellipse(
            [(center_x - circle_radius, center_y - circle_radius),
             (center_x + circle_radius, center_y + circle_radius)],
            fill=(0, 0, 0, 0)  # Transparent
        )

        img.save('resources/menu_bar_icon.png')

        print("White menu bar icon created at resources/menu_bar_icon.png")
    except Exception as e:
        print(f"Error creating white menu bar icon: {e}")

def install_requirements():
    """Install required packages"""
    try:
        if os.path.exists('requirements.txt'):
            print("Installing requirements from requirements.txt...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        else:
            print("Installing required packages...")
            packages = [
                'rumps>=0.4.0',
                'wxPython>=4.2.0',
                'Pillow>=9.2.0',
                'requests>=2.28.1',
                'sqlalchemy>=2.0.0'
            ]

            for package in packages:
                print(f"Installing {package}...")
                subprocess.run([sys.executable, '-m', 'pip', 'install', package])
    except Exception as e:
        print(f"Error installing requirements: {e}")

if __name__ == "__main__":
    run_app()
