import requests

with open("C:\\Users\\HP\\Downloads\\Telegram Desktop\\opportunities-by-created.webp", 'rb') as file:
    files = {'file': file}
    response = requests.post("http://127.0.0.1:8000/interpret", files={'file': file})

print(response.json())