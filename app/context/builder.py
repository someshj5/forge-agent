from app.tools.filesystem import read_file


class ContextBuilder:
    def build(self,candidates):
        if candidates == []: return []

        for c in candidates:

            res = read_file(c['path'])
            if res["success"] == True:
                c["content"] = res['content'] 
            else:
                c["error"] = res["error"]
                
        return candidates