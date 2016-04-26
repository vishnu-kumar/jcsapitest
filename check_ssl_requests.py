import requests
res = requests.get("https://api.github.com/events", verify=False)
print res
