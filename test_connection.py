import requests
import json

try:
    print("Testing health...")
    r = requests.get('http://localhost:5000/api/health')
    print(f"Health: {r.status_code} {r.text}")

    print("Testing generate...")
    # Minimal valid payload structure might be needed to avoid verification error, but let's try empty first
    r = requests.post('http://localhost:5000/api/generate/full', json={"teachers": [], "subjects": [], "labs": []})
    print(f"Generate: {r.status_code} {r.text}")
except Exception as e:
    print(f"Error: {e}")
