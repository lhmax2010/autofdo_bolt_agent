import subprocess,json,gzip,hashlib,xml.etree.ElementTree as ET,datetime
from pathlib import Path
D=Path(__file__).resolve().parent;data=json.loads((D/"snapshot-candidates.json").read_text())
requests=json.loads((D/"snapshot-requests.json").read_text());results=[]
for row in data["repositories"]:
 if row["snapshot"] not in ["tizen-base-toolchain_20261030.120529","tizen-unified-toolchain_20261104.125239"]:continue
 path=D/(row["snapshot"]+"-primary.xml.gz");url=row["url"]+row["primary"]
 cmd=["curl","--silent","--show-error","--location","--connect-timeout","15","--max-time","120","--output",str(path),"--write-out","%{http_code}",url]
 start=datetime.datetime.now().astimezone().isoformat();r=subprocess.run(cmd,capture_output=True,text=True)
 requests.append({"url":url,"time":start,"curl_exit":r.returncode,"http_status":r.stdout,"stderr":r.stderr,"body":str(path),"sha256":hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None})
 (D/"snapshot-requests.json").write_text(json.dumps(requests,indent=2)+"\n")
 assert r.returncode==0 and r.stdout=="200"
 expected=row["primary"].split("/")[-1].split("-")[0];assert hashlib.sha256(path.read_bytes()).hexdigest()==expected
 matches=[];arches=set()
 with gzip.open(path,"rb") as f:
  for _,e in ET.iterparse(f,events=["end"]):
   if e.tag.endswith("}package"):
    name=e.find("{*}name").text;arch=e.find("{*}arch").text;arches.add(arch)
    if name=="clang":
     matches.append({"name":name,"arch":arch,"version":e.find("{*}version").attrib,"location":e.find("{*}location").attrib["href"]})
    e.clear()
 results.append({"snapshot":row["snapshot"],"role":"fallback candidate; not selected before board query","available_architectures":sorted(arches),"clang":matches,"metadata_sha_verified":True})
(D/"candidate-clang.json").write_text(json.dumps(results,indent=2)+"\n")
print(json.dumps(results,indent=2),flush=True)
