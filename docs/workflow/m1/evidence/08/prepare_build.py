exec((__import__('pathlib').Path(__file__).parent/'common.py').read_text())
import shutil,configparser
D=D/'build';D.mkdir(exist_ok=True);ops=[]
assert json.loads((D.parent/'conversion/result.json').read_text())['success']
repo=D/'repo';repo.mkdir(exist_ok=True);deps=json.loads((W/'temp/m1-target-20261114/weekend-j2/thumb-attempt-0/dependencies.json').read_text())
manifest=[]
for e in deps:
 p=W/e['path'];assert sha(p)==e['sha256'];q=repo/p.name;shutil.copy2(p,q);manifest.append(dict(path=q.name,sha256=sha(q)))
save('repo-manifest.json',manifest)
run('createrepo',['createrepo_c','--workers','2',str(repo)])
conf=W/'temp/gbs-deps-archive/ffmpeg-armv7l-20261114/tizen_unified_standard.conf';shutil.copy2(conf,repo/'tizen_unified_standard.conf')
for x in ['home','tmp','cache','config','state','gbs-tmp','roots']:(D/x).mkdir(exist_ok=True)
src=D/'ffmpeg';run('clone',['git','-c','gc.auto=0','clone','--shared','--no-checkout',str(W/'temp/m1-target-20261114/weekend-j2/ffmpeg'),str(src)])
run('checkout',['git','-C',str(src),'checkout','--detach','5fe76358596f66e955f005094e6f34ca525ab23d'])
patch=W/'temp/m1-target-20261114/profiling-fix1.patch';assert sha(patch)=='0c94e54d252ad1ecbc625f629af090b257edba4cd3753d76352fd031486243b6';run('apply',['git','-C',str(src),'apply',str(patch)])
assert sha(src/'packaging/ffmpeg.spec')=='0e611e7eb95ada2c024dbea379821c5b109383f1545bcb0c86ef85f238740c27'
profile=D.parent/'conversion/autofdo.extbinary';accessfile=D.parent/'conversion/Q5-17-profile-access.json';a=json.loads(accessfile.read_text());a.append(dict(object=str(profile),time=datetime.datetime.now().astimezone().isoformat(),purpose='复制到消费构建Source2000，随后AFDO编译器读取'));accessfile.write_text(json.dumps(a,indent=2,ensure_ascii=False)+'\n');shutil.copy2(profile,src/'packaging/autofdo.extbinary')
c=configparser.ConfigParser();c['general']={'tmpdir':str(D/'gbs-tmp'),'profile':'profile.tizen_unified_standard','buildroot':str(D/'roots/unused')};c['profile.tizen_unified_standard']={'repos':'repo.frozen'};c['repo.frozen']={'url':repo.as_uri()}
with (D/'frozen.conf').open('w') as f:c.write(f)
save('lock-inputs.json',dict(source='5fe76358596f66e955f005094e6f34ca525ab23d',patch=sha(patch),spec=sha(src/'packaging/ffmpeg.spec'),profile=sha(profile),config=sha(D/'frozen.conf'),buildconf=sha(repo/'tizen_unified_standard.conf')))
print('Prepared frozen repository and unchanged source/spec with locked profile')
