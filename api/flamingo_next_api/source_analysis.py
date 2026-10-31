"""Local heuristic panel proposals and Tesseract observations, never verified canon."""
import csv
import io
import shutil
import tempfile
from pathlib import Path
from PIL import Image
from .media_engine import MediaEngine

class SourceAnalyzer:
    def __init__(self,storage,heartbeat=lambda:True):self.storage,self.heartbeat=storage,heartbeat
    def panels(self,data):
        with Image.open(io.BytesIO(data)) as image:
            width,height=image.size
            gray=image.convert('L');height=min(height,12000);small=gray.resize((min(width,192),height))
            # White gutters are only proposals, preserving every source row.
            cuts=[];start=None
            for y in range(height):
                row=list(small.crop((0,y,small.width,y+1)).get_flattened_data())
                white=sum(v>245 for v in row)/len(row)>.97
                if white and start is None:start=y
                if not white and start is not None:
                    if y-start>=max(12,height*.008) and start>height*.06 and y<height*.94:cuts.append((start+y)//2)
                    start=None
            cuts=[0]+cuts[:29]+[height]
            if len(cuts)>2 and any(b-a<height*.03 for a,b in zip(cuts,cuts[1:])):cuts=[0,height]
            return [{'order':i+1,'crop':[0,a/height,1,(b-a)/height],'classification':'unknown','confidence':'heuristic-unreviewed'} for i,(a,b) in enumerate(zip(cuts,cuts[1:]))]
    def analyze(self,record,assets):
        if not shutil.which('tesseract'):raise RuntimeError('Install Tesseract for local OCR; no external OCR fallback is allowed')
        runner=MediaEngine(self.storage,self.heartbeat);pages=[]
        with tempfile.TemporaryDirectory(prefix='fns-ocr-') as folder:
            for page in record['pages']:
                if not self.heartbeat():raise RuntimeError('Source analysis cancelled')
                asset=assets[page['asset_id']];data=self.storage.read_blob(asset['object_key'],asset['sha256'])
                path=Path(folder)/'page.png';path.write_bytes(data)
                output=runner.run(['tesseract',str(path),'stdout','-l','eng','--psm','11','tsv'],timeout=90).decode(errors='replace')
                words=[]
                for row in csv.DictReader(io.StringIO(output),delimiter='\t',quoting=csv.QUOTE_NONE):
                    value=(row.get('text') or '').strip()
                    if not value:continue
                    words.append({'text':value,'confidence':max(0,float(row.get('conf','-1')))/100,'box':[int(row[k]) for k in ('left','top','width','height')],'line_ref':f"{row.get('block_num')}.{row.get('par_num')}.{row.get('line_num')}"})
                lines={}
                for word in words:lines.setdefault(word['line_ref'],[]).append(word['text'])
                pages.append({'page_id':page['id'],'source_asset_sha':asset['sha256'],'panels':self.panels(data),'words':words,'proposed_text':'\n'.join(' '.join(v) for v in lines.values()),'owner_text':page['text'],'speaker':'unknown','review_status':'unreviewed'})
        return {'version':'1.0','provider':'local-tesseract-english','source_sha':record['source_sha'],'pages':pages,'status':'HUMAN_REVIEW_REQUIRED','limitations':['Reading order, bubble-only panels and speaker identity require source review.','Heuristic gutter regions never delete or replace source pixels.','English OCR data is installed; other languages require separately installed local language data.']}
