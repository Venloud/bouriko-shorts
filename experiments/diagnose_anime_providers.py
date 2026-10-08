"""Multi-provider network and anime image diagnostics for GitHub Actions."""
import json, os, socket, time, urllib.request, urllib.error, urllib.parse
from pathlib import Path
OUT=Path("output/clip_pull_test"); OUT.mkdir(parents=True,exist_ok=True)
TESTS=[
 ("jikan","https://api.jikan.moe/v4/anime/40748"),
 ("kitsu","https://kitsu.io/api/edge/anime?filter%5Btext%5D=jujutsu%20kaisen&page%5Blimit%5D=1"),
 ("trace_moe","https://api.trace.moe/search"),
 ("anilist","https://graphql.anilist.co"),
 ("anilist_image_cdn","https://s4.anilist.co"),
 ("jikan_image_cdn","https://cdn.myanimelist.net"),
]
def check(name,url):
    host=urllib.parse.urlsplit(url).hostname
    result={"provider":name,"url":url}
    try:
        result["dns_ipv4"]=sorted(set(x[4][0] for x in socket.getaddrinfo(host,443,socket.AF_INET,socket.SOCK_STREAM)))
    except Exception as e: result["dns_ipv4_error"]=str(e)
    try:
        result["dns_ipv6"]=sorted(set(x[4][0] for x in socket.getaddrinfo(host,443,socket.AF_INET6,socket.SOCK_STREAM)))
    except Exception as e: result["dns_ipv6_error"]=str(e)
    try:
        if name=="anilist":
            data=json.dumps({"query":"query { Media(id: 40748, type: ANIME) { id title { romaji } coverImage { large } } }"}).encode()
            req=urllib.request.Request(url,data=data,headers={"Content-Type":"application/json","User-Agent":"BourikoDiagnostics/1.0"})
        else: req=urllib.request.Request(url,headers={"User-Agent":"BourikoDiagnostics/1.0"})
        with urllib.request.urlopen(req,timeout=12) as response:
            body=response.read(30000)
            result.update(status="reachable",http_status=response.status,content_type=response.headers.get("Content-Type"),bytes_read=len(body))
            if name in ("anilist","jikan","kitsu"):
                try: result["sample"]=json.loads(body.decode()) if name=="anilist" else {"json_valid":bool(json.loads(body.decode()))}
                except Exception as e: result["json_error"]=str(e)
    except urllib.error.HTTPError as e:
        result.update(status="http_error",http_status=e.code,error=str(e))
    except Exception as e: result.update(status="network_error",error=str(e))
    return result
results=[check(name,url) for name,url in TESTS]
report={"checks":results,"checked_at_unix":int(time.time()),"note":"HTTP errors mean network reachable; network_error means connection failure"}
(OUT/"provider_diagnostics.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
