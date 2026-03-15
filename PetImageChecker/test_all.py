import os
import sys
import glob

# Import post_multipart from test_api
from test_api import post_multipart

def main():
    uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'uploads'))
    if not os.path.exists(uploads_dir):
        print(f"Dir not found: {uploads_dir}")
        return
        
    files = glob.glob(os.path.join(uploads_dir, '*.*'))
    if not files:
        print("No files to test")
        return
        
    print(f"Testing {len(files)} files...")
    for f in files:
        res = post_multipart("http://localhost:8000/verify-pet-image", f)
        print(f"File: {os.path.basename(f)} -> Valid: {res.get('is_valid')}")

if __name__ == '__main__':
    main()
