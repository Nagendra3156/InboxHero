import json
class MailStore:
    def __init__(self,path):
        self.messages=json.loads(path.read_text()); self.by_id={m["id"]:m for m in self.messages}
    def get(self,i): 
        return self.by_id.get(i)
    def thread(self,t): 
        return sorted([m for m in self.messages if m["thread_id"]==t],key=lambda x:x["timestamp"])
    def search(self,terms):
        terms=[x.lower() for x in terms]
        return [m for m in self.messages if all(x in (m["subject"]+" "+m["body"]).lower() for x in terms)]
