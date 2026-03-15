import requests
import sys
import os

url = 'http://localhost:8080/pets/upload'
file_path = r'c:\Users\Anupa\Desktop\PetHub2\uploads\4ab73094-a845-4f2f-bfbe-f2cd69849985_6a4060e4-f795-4364-98f3-5f7141c4a9b5.jpeg'

with open(file_path, 'rb') as f:
    files = {'image': (os.path.basename(file_path), f, 'image/jpeg')}
    data = {'name': 'TestBot', 'type': 'Dog'}
    response = requests.post(url, files=files, data=data)
    
print("Status Code:", response.status_code)
print("Response Text:", response.text)
