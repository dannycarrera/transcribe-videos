#!/usr/bin/env python3
"""
Test script to verify that all dependencies are correctly installed.
"""
import sys
import subprocess
import importlib
import platform

def check_python_version():
    """Check if Python version is 3.8 or higher."""
    required_version = (3, 8)
    current_version = sys.version_info
    
    if current_version >= required_version:
        print(f"✓ Python version: {sys.version}")
        return True
    else:
        print(f"✗ Python version: {sys.version}")
        print(f"  Required: Python {required_version[0]}.{required_version[1]} or higher")
        return False

def check_ffmpeg():
    """Check if FFmpeg is installed and accessible."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✓ FFmpeg: {version_line}")
            return True
        else:
            print("✗ FFmpeg: Not found or not working properly")
            return False
    except FileNotFoundError:
        print("✗ FFmpeg: Not found in PATH")
        return False

def check_package(package_name):
    """Check if a Python package is installed."""
    try:
        module = importlib.import_module(package_name)
        if hasattr(module, '__version__'):
            version = module.__version__
        else:
            version = "Unknown version"
        print(f"✓ {package_name}: {version}")
        return True
    except ImportError:
        print(f"✗ {package_name}: Not installed")
        return False

def check_cuda():
    """Check if CUDA is available for PyTorch."""
    try:
        import torch
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            device_name = torch.cuda.get_device_name(0) if device_count > 0 else "N/A"
            print(f"✓ CUDA: Available (Devices: {device_count}, Name: {device_name})")
            return True
        else:
            print("✗ CUDA: Not available")
            print("  Note: CUDA is recommended for faster transcription but not required")
            return False
    except ImportError:
        print("✗ PyTorch: Not installed")
        return False

def main():
    """Run all checks and print a summary."""
    print("Testing installation for Video Transcription App")
    print("=" * 50)
    print(f"System: {platform.system()} {platform.release()}")
    print("-" * 50)
    
    python_ok = check_python_version()
    ffmpeg_ok = check_ffmpeg()
    
    print("\nChecking required Python packages:")
    torch_ok = check_package("torch")
    whisper_ok = check_package("whisper")
    ffmpeg_python_ok = check_package("ffmpeg")
    tqdm_ok = check_package("tqdm")
    numpy_ok = check_package("numpy")
    
    print("\nChecking CUDA availability:")
    cuda_ok = check_cuda()
    
    print("\nSummary:")
    print("-" * 50)
    
    required_checks = [python_ok, ffmpeg_ok, torch_ok, whisper_ok, ffmpeg_python_ok, tqdm_ok, numpy_ok]
    if all(required_checks):
        print("✓ All required components are installed correctly!")
    else:
        print("✗ Some required components are missing or not configured correctly.")
        print("  Please check the output above and install missing components.")
    
    if not cuda_ok:
        print("\nNote: CUDA is not available. The application will still work but transcription")
        print("      will be slower. For better performance, consider setting up CUDA.")
    
    print("\nIf you need to install missing packages, run:")
    print("pip install -r requirements.txt")

if __name__ == "__main__":
    main() 