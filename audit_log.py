import json,datetime
class Trace:
    def __init__(self,path): self.path=path; path.write_text("")
    def log(self,event,**kw):
        row={"ts":datetime.datetime.now(datetime.timezone.utc).isoformat(),"event":event,**kw}
        with self.path.open("a",encoding="utf8") as f:f.write(json.dumps(row)+"\n")
