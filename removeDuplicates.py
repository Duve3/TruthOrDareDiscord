"""
Remove dups from database
"""
import json

if __name__ == "__main__":
    print("Removing duplicates...")
    with open("./db.json") as db:
        data = json.load(db)

    ogtl = len(data["truths"])
    data["truths"] = list(set(data["truths"]))
    print(f"Found {ogtl - len(data['truths'])} duplicates in list [\"truths\"].")

    ogtd = len(data["dares"])
    data["dares"] = list(set(data["dares"]))
    print(f"Found {ogtd - len(data['dares'])} duplicates in list [\"dares\"].")

    with open("./db.json", "w") as db:
        db.write(json.dumps(data))

    print("No more duplicates.")
