import json

class PreferenceMemory:
    def __init__(self, path):
        self.path = path
        try:
            self.data = json.loads(path.read_text(encoding="utf8"))
        except Exception:
            self.data = {"preferences": []}

    def remember(self, preference):
        self.data["preferences"] = [p for p in self.data["preferences"] if p["key"] != preference["key"]]
        self.data["preferences"].append(preference)
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf8")

    def get(self, key):
        for p in reversed(self.data.get("preferences", [])):
            if p.get("key") == key:
                return p
        return None

    def summary(self):
        return self.data.get("preferences", [])
