import requests
import json

# Test the LLM API
url = "http://127.0.0.1:5000/query"
headers = {"Content-Type": "application/json"}

# Test question
data = {
    "question": "List teams with their player counts"
}

try:
    response = requests.post(url, headers=headers, data=json.dumps(data))
    print("Status Code:", response.status_code)
    print("Response:", response.json())
except Exception as e:
    print("Error:", str(e))