"""Bounded offline narration + FFmpeg renderer. External provider calls absent."""
import array

def pcm_rms(data):
    samples=array.array("h",data)
    return (sum(v*v for v in samples)/len(samples))**.5 if samples else 0

import hashlib
import html
import hmac
import logging
import io
import json
import math
import os
import shutil
import signal
import sys
import subprocess
import tempfile
import time
import wave
from pathlib import Path
from .product_db import sha

class Cancelled(Exception): pass

class MediaEngine:
    fps=24
    rate=24000
    def __init__(self,storage,heartbeat=lambda:True):
        self.storage,self.heartbeat=storage,heartbeat
    def run(self,args,timeout=120):
        # File arguments are generated locally. Source text is supplied through a file.
        with tempfile.TemporaryFile() as stderr, tempfile.TemporaryFile() as stdout:
            process=subprocess.Popen(args,stdout=stdout,stderr=stderr,start_new_session=True)
            start=time.monotonic()
            try:
                while process.poll() is None:
                    if time.monotonic()-start>timeout: raise TimeoutError('Media command exceeded its time budget')
                    if not self.heartbeat(): raise Cancelled('Render cancelled or worker lease lost')
                    time.sleep(.2)
                stdout.seek(0);output=stdout.read(8_000_001)
                if len(output)>8_000_000:raise RuntimeError('Media tool text output exceeded 8 MB')
                if process.returncode:
                    stderr.seek(0);detail=stderr.read()[-1000:].decode(errors='replace')
                    raise RuntimeError(f'Media tool failed: {detail}')
                return output
            finally:
                if process.poll() is None:
                    os.killpg(process.pid,signal.SIGKILL);process.wait()
    def voice_engine(self,profile='system-default'):
        from .voice_models import PROFILES
        if profile in PROFILES:return profile
        if profile!='system-default':raise RuntimeError('Unknown voice profile')
        if shutil.which('say'):return 'macos-system-speech'
        if shutil.which('espeak-ng'):return 'espeak-ng'
        if shutil.which('espeak'):return 'espeak'
        raise RuntimeError('Install an offline system voice (macOS say or espeak-ng); no paid fallback is allowed')
    def speech(self,text,folder,index,profile='system-default'):
        engine=self.voice_engine(profile)
        from .voice_models import FILES
        identity=sha({'text':text,'engine':engine,'rate':155,'version':'v1','model_files':FILES if engine.startswith('kokoro-') else None})
        # Cache is immutable and keyed by exact narration and the voice adapter.
        cached=self.read_cache('voice',identity)
        if cached is not None:
            path=folder/f'voice-{index}.wav';path.write_bytes(cached)
            pcm=self.pcm(path)
            if pcm_rms(pcm)<50:raise RuntimeError('Cached narration is silent')
            return path,pcm,engine,True
        script=folder/f'speech-{index}.txt';script.write_text(text)
        raw=folder/f'raw-{index}.aiff';path=folder/f'voice-{index}.wav'
        if engine.startswith('kokoro-'):
            self.run([sys.executable,'-m','flamingo_next_api.kokoro_voice','--text-file',str(script),'--output',str(path),'--profile',profile],timeout=180)
        elif engine=='macos-system-speech':
            self.run(['say','-f',str(script),'-r','155','-o',str(raw)])
        else:
            raw=folder/f'raw-{index}.wav'
            self.run([engine,'-f',str(script),'-s','155','-w',str(raw)])
        if not engine.startswith('kokoro-'):
            self.run(['ffmpeg','-v','error','-y','-i',str(raw),'-ar',str(self.rate),'-ac','1','-c:a','pcm_s16le',str(path)])
        pcm=self.pcm(path)
        if not pcm or pcm_rms(pcm)<50:raise RuntimeError('Narration is missing or silent')
        blob=self.storage.put_blob(path.read_bytes(),'audio/wav')
        self.write_cache('voice',identity,blob)
        return path,pcm,engine,False
    def read_cache(self,namespace,identity):
        from botocore.exceptions import ClientError
        try:
            raw=self.storage.client.get_object(Bucket=self.storage.settings.bucket,Key=f'{namespace}-cache/{identity}.json')['Body'].read()
            entry=json.loads(raw);signature=entry.pop('signature')
            expected=hmac.new(self.storage.settings.signing_key.encode(),json.dumps(entry,sort_keys=True).encode(),hashlib.sha256).hexdigest()
            if entry['input_sha']!=identity or not hmac.compare_digest(signature,expected):raise ValueError('Cache signature mismatch')
            return self.storage.read_blob(entry['blob']['key'],entry['blob']['sha256'])
        except ClientError as e:
            if e.response['Error']['Code'] not in ('NoSuchKey','404'):raise
        except (ValueError,KeyError):
            logging.getLogger(__name__).warning('Invalid %s cache entry rejected',namespace)
        return None
    def write_cache(self,namespace,identity,blob):
        entry={'input_sha':identity,'blob':blob}
        entry['signature']=hmac.new(self.storage.settings.signing_key.encode(),json.dumps(entry,sort_keys=True).encode(),hashlib.sha256).hexdigest()
        self.storage.client.put_object(Bucket=self.storage.settings.bucket,Key=f'{namespace}-cache/{identity}.json',Body=json.dumps(entry).encode(),ContentType='application/json')
    def pcm(self,path):
        with wave.open(str(path),'rb') as audio:
            if audio.getnchannels()!=1 or audio.getsampwidth()!=2 or audio.getframerate()!=self.rate:
                raise RuntimeError('Narration format is inconsistent')
            return audio.readframes(audio.getnframes())
    def shot_filters(self,beat,width,height,frames):
        x,y,w,h=beat['crop']
        crop=f"crop=w='max(2,trunc(iw*{w}/2)*2)':h='max(2,trunc(ih*{h}/2)*2)':x=iw*{x}:y=ih*{y}"
        motion=beat.get('motion','static');span=max(1,frames-1)
        # Preserve the selected panel over a subdued backdrop from the same crop.
        fit=(f'split=2[frontsource][backsource];'
             f'[backsource]scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},boxblur=20:2,eq=brightness=-0.22[back];'
             f'[frontsource]scale={width}:{height}:force_original_aspect_ratio=decrease[front];'
             f'[back][front]overlay=(W-w)/2:(H-h)/2,setsar=1')
        if motion=='scroll_down':
            # Move a landscape viewport through the selected tall source region.
            viewport=f"crop=w=iw:h='min(ih,max(2,trunc(iw*{height}/{width}/2)*2))':x=0:y='(ih-oh)*min(t/{span/self.fps},1)'"
            return f'{crop},{viewport},{fit},format=yuv420p'
        if motion=='static':return f'{crop},{fit},format=yuv420p'
        zoom={'zoom_in':f'1+0.08*on/{span}','zoom_out':f'1.08-0.08*on/{span}'}.get(motion,'1.1')
        center='iw/2-iw/zoom/2';vertical='ih/2-ih/zoom/2'
        horizontal=f'(iw-iw/zoom)*on/{span}' if motion=='pan_right' else f'(iw-iw/zoom)*(1-on/{span})' if motion=='pan_left' else center
        return f"{crop},{fit},zoompan=z='{zoom}':x='{horizontal}':y='{vertical}':d={frames}:s={width}x{height}:fps={self.fps},format=yuv420p"
    def render(self,record,assets,kind='longform'):
        if not record['beats']:raise RuntimeError('A reviewed script is required')
        if len(record['beats'])>100:raise RuntimeError('Episode exceeds the 100-beat local render limit')
        width,height=(720,1280) if kind=='vertical' else (1280,720)
        with tempfile.TemporaryDirectory(prefix='fns-render-') as temp:
            folder=Path(temp);clips=[];timing=[];pcm_all=bytearray();frame_start=0;engines=set();cache_hits=0;clip_cache_hits=0
            for i,beat in enumerate(record['beats']):
                if not self.heartbeat():raise Cancelled('Render stopped')
                page=next(p for p in record['pages'] if p['id']==beat['page_id'])
                asset=assets[page['asset_id']]
                image=folder/f'page-{i}.png';image.write_bytes(self.storage.read_blob(asset['object_key'],asset['sha256']))
                from .pronunciation import for_speech
                speech_text=for_speech(beat['spoken_text'],record.get('pronunciations',{}))
                voice,pcm,engine,cached=self.speech(speech_text,folder,i,record.get('voice','system-default'))
                engines.add(engine);cache_hits+=int(cached)
                duration=len(pcm)/2/self.rate
                frames=math.ceil((duration+.16)*self.fps)
                if frames/self.fps>100:raise RuntimeError('A narration beat exceeds the 100-second limit')
                frame_end=frame_start+frames
                if frame_end/self.fps>1200:raise RuntimeError('Episode exceeds the 20-minute local limit')
                if kind=='vertical' and frame_end/self.fps>60:raise RuntimeError('Vertical plan exceeds 60 seconds; shorten the script in an explicit variant')
                total_samples=round(frames/self.fps*self.rate)
                padded=pcm+b'\0\0'*(total_samples-len(pcm)//2)
                pcm_all.extend(padded)
                filters=self.shot_filters(beat,width,height,frames)
                clip=folder/f'clip-{i}.mp4'
                clip_identity=sha({'source':asset['sha256'],'crop':beat['crop'],'frames':frames,'fps':self.fps,'size':[width,height],'motion':beat.get('motion','static'),'renderer':'ffmpeg-x264-v4-vbv1000-panelbackdrop'})
                cached_clip=self.read_cache('clip',clip_identity)
                if cached_clip is not None:
                    clip.write_bytes(cached_clip);clip_cache_hits+=1
                else:
                    # Bound 20-minute video + AAC below the 200 MB export ceiling.
                    # Each shot's 1 Mbit buffer also bounds short-clip overhead.
                    self.run(['ffmpeg','-v','error','-y','-loop','1','-framerate',str(self.fps),'-i',str(image),'-vf',filters,'-r',str(self.fps),'-frames:v',str(frames),'-an','-c:v','libx264','-preset','veryfast','-crf','23','-maxrate','1000k','-bufsize','1000k',str(clip)],timeout=120)
                    self.write_cache('clip',clip_identity,self.storage.put_blob(clip.read_bytes(),'video/mp4'))
                clips.append(clip)
                timing.append({'beat_id':beat['id'],'page_id':beat['page_id'],'source_asset_sha':asset['sha256'],'spoken_text':beat['spoken_text'],'tts_input_text':speech_text,'start_frame':frame_start,'end_frame':frame_end,'voice_seconds':round(duration,4),'voice_sha':hashlib.sha256(voice.read_bytes()).hexdigest(),'crop':beat['crop'],'motion':beat.get('motion','static')})
                frame_start=frame_end
            voice_path=folder/'narration.wav'
            with wave.open(str(voice_path),'wb') as wav:
                wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(self.rate);wav.writeframes(bytes(pcm_all))
            concat=folder/'clips.txt';concat.write_text(''.join(f"file '{p.name}'\n" for p in clips))
            output=folder/'episode.mp4'
            self.run(['ffmpeg','-v','error','-y','-f','concat','-safe','1','-i',str(concat),'-i',str(voice_path),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','160k','-movflags','+faststart',str(output)],timeout=180)
            if output.stat().st_size>200_000_000:raise RuntimeError('Final export exceeds local size limit')
            probe=json.loads(self.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(output)]))
            streams=probe['streams'];video=next((s for s in streams if s['codec_type']=='video'),None);audio=next((s for s in streams if s['codec_type']=='audio'),None)
            if not video or not audio:raise RuntimeError('Final export is missing video or narration')
            if video['width']!=width or video['height']!=height or int(video.get('nb_frames',frame_start))!=frame_start:raise RuntimeError('Final frame count or resolution differs from the shot manifest')
            expected=frame_start/self.fps
            actual=float(probe['format']['duration'])
            if abs(actual-expected)>.2:raise RuntimeError('Final duration does not match the shot manifest')
            self.run(['ffmpeg','-v','error','-xerror','-i',str(output),'-f','null','-'],timeout=180)
            decoded=folder/'decoded.wav'
            self.run(['ffmpeg','-v','error','-y','-i',str(output),'-vn','-ar',str(self.rate),'-ac','1','-c:a','pcm_s16le',str(decoded)])
            final_pcm=self.pcm(decoded)
            for shot in timing:
                start=round(shot['start_frame']/self.fps*self.rate)*2
                end=start+round(shot['voice_seconds']*self.rate)*2
                if not final_pcm[start:end] or pcm_rms(final_pcm[start:end])<40:
                    raise RuntimeError('Decoded final audio contains a silent required narration beat')
            blob=self.storage.put_blob(output.read_bytes(),'video/mp4')
            raw_voice=self.storage.put_blob(voice_path.read_bytes(),'audio/wav')
            from .editorial import input_fingerprint
            manifest={'input_sha':input_fingerprint(record),'version':'1.0','fps':self.fps,'frames':frame_start,'shots':timing,'source_sha':record['source_sha'],'voice_engines':sorted(engines),'voice_cache_hits':cache_hits,'clip_cache_hits':clip_cache_hits,'export_sha':blob['sha256'],'narration_sha':raw_voice['sha256'],'kind':kind}
            manifest_blob=self.storage.put_blob(json.dumps(manifest,sort_keys=True).encode(),'application/json')
            def stamp(seconds):
                ms=round(seconds*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02}.{ms%1000:03}'
            captions='WEBVTT\n\n'+''.join(f"{i+1}\n{stamp(s['start_frame']/self.fps)} --> {stamp(s['end_frame']/self.fps)}\n{html.escape(' '.join(s['spoken_text'].split()).replace('-->','—>'))}\n\n" for i,s in enumerate(timing))
            captions_blob=self.storage.put_blob(captions.encode(),'text/vtt')
            export=blob|{'mime_type':'video/mp4','size_bytes':output.stat().st_size,'duration_seconds':actual,'width':width,'height':height,'manifest':manifest,'manifest_blob':manifest_blob,'voice_blob':raw_voice,'captions_blob':captions_blob}
            qa={'status':'PASS','export_sha':blob['sha256'],'manifest_sha':manifest_blob['sha256'],'checks':['complete_ffmpeg_decode','video_and_audio_streams','duration_matches_manifest','every_required_beat_has_audible_pcm','all_shots_link_to_source_hashes'],'semantic_qa':'HUMAN_REVIEW_REQUIRED','creative_qa':'HUMAN_REVIEW_REQUIRED','limitations':['Voice quality, pronunciation and factual interpretation require human listening/source review.','No ASR or model semantic verdict was performed.']}
            return {'export':export,'qa':qa,'bucket':self.storage.settings.bucket}
