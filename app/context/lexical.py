from collections import Counter


def rank_matches(search_result: dict) -> list[dict]:
    if not search_result.get("success"):
        return []

    extracted = [s.split(":", 1)[0] for s in search_result["matches"]]
    count = Counter(extracted)
    output=[]
    for k,v in count.items():
        res ={
            "path" : str(k),
            "score" : v,
            "source" : "lexical"
        }
        output.append(res)
        
    output.sort(
        key=lambda item: item["score"],
        reverse=True,
    )
    return output