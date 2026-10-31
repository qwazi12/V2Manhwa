"""Single bounded offline neural-voice invocation, supervised by the media worker."""
import argparse,wave
from pathlib import Path
from .voice_models import verify,PROFILES

def synthesize(text,output,profile):
    if profile not in PROFILES:raise ValueError('Unknown local neural voice profile')
    if not text.strip() or len(text)>1600:raise ValueError('Narration must contain 1..1600 characters')
    folder=verify()
    import numpy as np
    import onnxruntime as rt
    from kokoro_onnx import Kokoro
    rt.disable_telemetry_events()
    options=rt.SessionOptions();options.intra_op_num_threads=2;options.inter_op_num_threads=1
    session=rt.InferenceSession(str(folder/'kokoro-v1.0.onnx'),sess_options=options,providers=['CPUExecutionProvider'])
    model=Kokoro.from_session(session,str(folder/'voices-v1.0.bin'))
    voice=PROFILES[profile]
    samples,rate=model.create(text,voice=voice,speed=1.0,lang='en-gb' if voice.startswith('b') else 'en-us')
    samples=np.asarray(samples).reshape(-1)
    if rate!=24000 or not np.isfinite(samples).all() or len(samples)<2400 or len(samples)>24000*100:raise RuntimeError('Neural narration duration or PCM data is invalid')
    pcm=(np.clip(samples,-1,1)*32767).astype('<i2').tobytes()
    with wave.open(str(output),'wb') as audio:
        audio.setnchannels(1);audio.setsampwidth(2);audio.setframerate(rate);audio.writeframes(pcm)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--text-file',required=True);parser.add_argument('--output',required=True);parser.add_argument('--profile',choices=PROFILES,required=True);args=parser.parse_args()
    synthesize(Path(args.text_file).read_text(),Path(args.output),args.profile)
