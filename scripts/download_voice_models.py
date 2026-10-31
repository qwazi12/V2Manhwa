"""Fetch only pinned, public, Apache-2.0 Kokoro model release assets. No inference API."""
import json,sys,urllib.request
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'api'))
from flamingo_next_api.voice_models import directory,FILES,RELEASE,file_sha

folder=directory();folder.mkdir(parents=True,exist_ok=True)
for name,info in FILES.items():
    target=folder/name
    if target.is_file() and target.stat().st_size==info['size_bytes'] and file_sha(target)==info['sha256']:
        print(name+': verified');continue
    partial=folder/(name+'.partial')
    try:
        request=urllib.request.Request(RELEASE+name,headers={'User-Agent':'V2Manhwa-local-voice-setup'})
        total=0
        with urllib.request.urlopen(request,timeout=60) as response,partial.open('wb') as file:
            while block:=response.read(1024*1024):
                total+=len(block)
                if total>info['size_bytes']:raise ValueError('Model download exceeded pinned release size')
                file.write(block)
        if total!=info['size_bytes'] or file_sha(partial)!=info['sha256']:raise ValueError('Release checksum mismatch')
        partial.replace(target);print(name+': downloaded and verified')
    finally:
        if partial.exists():partial.unlink()
(folder/'provenance.json').write_text(json.dumps({'release':RELEASE,'model_license':'Apache-2.0','wrapper_license':'MIT','files':FILES},indent=2))
print('Local voice files are ready. No paid provider or account was used.')
