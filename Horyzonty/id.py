import requests
import json  # Added to pretty-print the structure

url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchDestination"

querystring = {"query": "Lisbon"}

headers = {
    "x-rapidapi-key": "8e6dfd68femshdfa437a5181dbb4p172746jsn521e3e39dd2b",  # Remember your key!
    "x-rapidapi-host": "booking-com15.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)
data = response.json()

print("🔍 RAW API RESPONSE (look for dest_id or id):")
# json.dumps pretty-prints the result with indentation (indent=2)
print(json.dumps(data, indent=2))