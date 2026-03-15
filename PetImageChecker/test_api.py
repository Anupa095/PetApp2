import urllib.request
import mimetypes
import uuid
import json
import sys

def post_multipart(url, filename):
    content_type, _ = mimetypes.guess_type(filename)
    if content_type is None:
        content_type = 'application/octet-stream'

    boundary = uuid.uuid4().hex
    headers = {'Content-type': f'multipart/form-data; boundary={boundary}'}

    with open(filename, 'rb') as f:
        file_content = f.read()

    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f'Content-Type: {content_type}\r\n\r\n'
    ).encode('utf-8') + file_content + f'\r\n--{boundary}--\r\n'.encode('utf-8')

    req = urllib.request.Request(url, data=body, headers=headers, method='POST')
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.read().decode()}")
        return None
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}")
        return None

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python test_api.py <image_path>")
        sys.exit(1)
        
    image_path = sys.argv[1]
    print(f"Testing {image_path} against http://localhost:8000/verify-pet-image...")
    result = post_multipart("http://localhost:8000/verify-pet-image", image_path)
    print("Result:", result)
