import requests
import json  # Dodajemy to, by ładnie wyświetlić strukturę

url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchDestination"

querystring = {"query": "Lisbon"}

headers = {
    "x-rapidapi-key": "8e6dfd68femshdfa437a5181dbb4p172746jsn521e3e39dd2b", # Pamiętaj o kluczu!
    "x-rapidapi-host": "booking-com15.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)
data = response.json()

print("🔍 SUROWA ODPOWIEDŹ Z API (Szukaj dest_id lub id):")
# json.dumps ładnie formatuje wynik robiąc wcięcia (indent=2)
print(json.dumps(data, indent=2))