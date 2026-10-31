"""Pinned, optional local voice assets. Never download during inference."""
import hashlib,importlib.util,os
from pathlib import Path

RELEASE='https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/'
FILES={
 'kokoro-v1.0.onnx':{'sha256':'beb0d1848dee9a49da392cc3df26958d46cfa35d321edf434f52949153f0df3a','size_bytes':325505369},
 'voices-v1.0.bin':{'sha256':'bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d','size_bytes':28214398},
}
PROFILES={'kokoro-am_michael-v1':'am_michael','kokoro-bm_george-v1':'bm_george','kokoro-af_heart-v1':'af_heart'}

def directory():return Path(os.getenv('FNS_KOKORO_DIR',str(Path(__file__).resolve().parents[2]/'local_data/models/kokoro-v1')))

def file_sha(path):
    value=hashlib.sha256()
    with path.open('rb') as file:
        for block in iter(lambda:file.read(1024*1024),b''):value.update(block)
    return value.hexdigest()

def installed():
    return importlib.util.find_spec('kokoro_onnx') is not None and all((directory()/name).is_file() and (directory()/name).stat().st_size==info['size_bytes'] for name,info in FILES.items())

def verify():
    for name,info in FILES.items():
        path=directory()/name
        if not path.is_file() or path.stat().st_size!=info['size_bytes'] or file_sha(path)!=info['sha256']:
            raise RuntimeError('Local neural voice model is absent or has an invalid checksum. Run download-voice-models.command; inference never downloads files.')
    return directory()
