import json

result = [""]
with open("test.json", "r") as fil:
    data = json.load(fil)

print(json.dumps(data[4], indent=4, ensure_ascii=False))

# {object_class_id} {x_center} {y_center} {width} {height}