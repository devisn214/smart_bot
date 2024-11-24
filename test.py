import requests

url = 'http://127.0.0.1:5000/api/compare-products'
data = {"products": ["car","dress"]}

# Send POST request
response = requests.post(url, json=data)

# Print response status code
print(response.status_code)  # Expected: 200 (Success)

# Print the response body (JSON data returned from Flask)
try:
    print(response.json())  # This will print the returned JSON data
except ValueError:
    print("Response is not in JSON format")
