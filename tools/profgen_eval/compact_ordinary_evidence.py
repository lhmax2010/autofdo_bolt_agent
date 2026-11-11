"""Lossless identity-check compaction: reference copies live in shared coverage tables."""
import collections,csv,json
from pathlib import Path
from run_scoped import WORK,sha
from pack_static_evidence import tables
BASE=WORK/"docs/profgen/eval/prep/evidence/ruling2/supplement3/rev1/identity-gate/ordinary-v2"
ARCHIVE=WORK/"temp/prep-identity-gate/ordinary-full-checks"

def main():
    ARCHIVE.mkdir(exist_ok=True);logs=[]
    for obj in ("spike-thumb","spike-a32","ffmpeg-thumb","ffmpeg-a32"):
        src=BASE/(obj+"-ordinary");dest=ARCHIVE/src.name
        assert not dest.exists();src.rename(dest);src.mkdir()
        meta=json.loads((dest/"index.json").read_text());old_counts=collections.Counter();new_counts=collections.Counter()
        cols=None
        first=next(dest.glob("checks-*.csv"))
        with first.open() as f:cols=next(csv.reader(f))
        def compacted():
            for part in meta["parts"]:
                f=dest/Path(part["path"]).name
                assert sha(f)==part["sha256"]
                with f.open() as stream:
                    for r in csv.DictReader(stream):
                        old_counts[r["conclusion"]]+=1
                        candidates=json.loads(r["candidates"])
                        for c in candidates:c.pop("copies",None)
                        r["candidates"]=candidates
                        new_counts[r["conclusion"]]+=1
                        yield [r[k] for k in cols]
        parts=tables(src,"checks",cols,compacted())
        assert old_counts==new_counts
        meta["uncompacted_index"]=str(dest/"index.json");meta["uncompacted_index_sha256"]=sha(dest/"index.json")
        meta["archive_path_rule"]="replace original object-ordinary prefix with uncompacted index parent; filenames unchanged"
        meta["compaction"]="Remove only redundant candidate copies; full raw coverage names/copies remain at reference_id in coverage-table index"
        meta["parts"]=parts
        (src/"index.json").write_text(json.dumps(meta,indent=2)+"\n")
        logs.append(dict(object=obj,conclusions=dict(new_counts),index=str(src/"index.json"),sha256=sha(src/"index.json"),
            before_bytes=sum(f.stat().st_size for f in dest.glob("checks-*.csv")),after_bytes=sum(f.stat().st_size for f in src.glob("checks-*.csv"))))
        print(json.dumps(logs[-1]),flush=True)
        (BASE/"compaction.json").write_text(json.dumps(logs,indent=2)+"\n")

if __name__=="__main__":main()
