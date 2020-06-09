import codecs
import json
t = open("QA_6.json", mode="r+", encoding="utf-8")
j = json.loads(t.read())
j[0]["relations"] = ["attention"]
t.seek(0)
t.truncate()
json.dump(j, t, indent=1)
