import requests

response = requests.post("http://localhost:8000/api/run-parser/", json={"query": "10177"})
result = response.json()

# Попробуем напечатать, без перекодировки, сразу как есть
print("---- STDOUT ----")
print(result.get("stdout", ""))

print("\n---- STDERR ----")
print(result.get("stderr", ""))
