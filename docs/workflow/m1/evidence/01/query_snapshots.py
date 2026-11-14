import subprocess,json,datetime,re,hashlib,gzip,xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urljoin
D=Path(__file__).resolve().parent;requests=[]
now=lambda:datetime.datetime.now().astimezone().isoformat()
def get(url,label):
 body=D/(label+".body");headers=D/(label+".headers")
 cmd=["curl","--silent","--show-error","--location","--connect-timeout","15","--max-time","90","--dump-header",str(headers),"--output",str(body),"--write-out","%{http_code}",url]
 start=now();p=subprocess.run(cmd,capture_output=True,text=True)
 row={"url":url,"time":start,"end":now(),"curl_exit":p.returncode,"http_status":p.stdout,"stderr":p.stderr,"body":str(body),"sha256":hashlib.sha256(body.read_bytes()).hexdigest() if body.exists() else None}
 requests.append(row);(D/"snapshot-requests.json").write_text(json.dumps(requests,indent=2)+"\n")
 print(label,p.returncode,p.stdout,flush=True)
 return body if p.returncode==0 and p.stdout=="200" else None
top="https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/"
listing=get(top,"base-list")
assert listing
ids=sorted(set(re.findall(r'tizen-base-toolchain_\d{8}\.\d{6}',listing.read_text())))
rows=[]
for sid in ids:
 url=top+sid+"/repos/standard/packages/"
 p=get(url,sid+"-packages")
 m=get(url+"repodata/repomd.xml",sid+"-repomd")
 valid=False;primary=None
 if m:
  try:
   root=ET.parse(m).getroot()
   primary=next(x.find("{*}location").attrib["href"] for x in root if x.attrib.get("type")=="primary")
   valid=True
  except (ET.ParseError,StopIteration,KeyError):pass
 rows.append({"snapshot":sid,"url":url,"packages_200":bool(p),"metadata_readable":valid,"primary":primary})
sid="tizen-unified-toolchain_20261104.125239"
url="https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Unified-Toolchain/"+sid+"/repos/standard/packages/"
p=get(url,sid+"-packages");m=get(url+"repodata/repomd.xml",sid+"-repomd")
valid=False;primary=None
if m:
 try:
  root=ET.parse(m).getroot();primary=next(x.find("{*}location").attrib["href"] for x in root if x.attrib.get("type")=="primary");valid=True
 except (ET.ParseError,StopIteration,KeyError):pass
rows.append({"snapshot":sid,"url":url,"packages_200":bool(p),"metadata_readable":valid,"primary":primary})
(D/"snapshot-candidates.json").write_text(json.dumps({"note":"Read-only candidates; board image queries pending, no selection yet.","repositories":rows},indent=2)+"\n")
print(json.dumps(rows,indent=2),flush=True)
