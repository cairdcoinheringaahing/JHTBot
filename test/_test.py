import requests, re

URL = 'https://golfingsuccess.github.io/jelly-hypertraining/students.html'

res = requests.get(URL).text
print(re.split(r'</?tbody>', res))
