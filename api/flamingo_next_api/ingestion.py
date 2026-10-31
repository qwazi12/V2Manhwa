"""Bounded local PNG/JPEG/WebP ingestion. No archives, URLs or automatic rights choices."""
import base64
import binascii
import hashlib
import io
import unicodedata
from datetime import datetime, timezone
from uuid import uuid4
from PIL import Image, ImageOps, UnidentifiedImageError
from fastapi import HTTPException
from sqlalchemy import select, update, func, text
from sqlalchemy.dialects.postgresql import insert
from .product_db import ProductDB, OWNER, sha
from .product_models import SeriesInput, SourceInput

Image.MAX_IMAGE_PIXELS=16_000_000

def normalize(value): return ' '.join(unicodedata.normalize('NFKC',value).casefold().split())

def decode_page(page):
    if '/' in page.filename or '\\' in page.filename or '..' in page.filename:
        raise HTTPException(422,'Page filenames cannot contain paths')
    try:
        raw=base64.b64decode(page.data_base64,validate=True)
        if len(raw)>5_000_000: raise ValueError('Each source page is limited to 5 MB')
        with Image.open(io.BytesIO(raw)) as image:
            if image.format not in ('PNG','JPEG','WEBP') or getattr(image,'n_frames',1)!=1:
                raise ValueError('Only single-frame PNG/JPEG/WebP pages are supported')
            if min(image.size)<16 or image.width*image.height>16_000_000:
                raise ValueError('Source dimensions exceed limits')
            image.load()
            # Decode and normalize bytes; strip metadata, preserve visual pixels.
            oriented=ImageOps.exif_transpose(image)
            if 'A' in oriented.getbands():
                normalized=Image.alpha_composite(Image.new('RGBA',oriented.size,'white'),oriented.convert('RGBA')).convert('RGB')
            else:normalized=oriented.convert('RGB')
            output=io.BytesIO(); normalized.save(output,format='PNG')
            result=output.getvalue()
            if len(result)>12_000_000:raise ValueError('Decoded page exceeds 12 MB')
            return result,normalized.width,normalized.height,raw,{'PNG':'image/png','JPEG':'image/jpeg','WEBP':'image/webp'}[image.format]
    except (ValueError,binascii.Error,UnidentifiedImageError,OSError,Image.DecompressionBombError,Image.DecompressionBombWarning) as e:
        raise HTTPException(422,f'Invalid image page: {str(e)[:180]}') from e

class Ingestion:
    def __init__(self,db:ProductDB,storage): self.db,self.storage=db,storage
    def list_series(self):
        t=self.db.tables
        with self.db.engine.connect() as conn:
            rows=[]
            for work in conn.execute(select(t['works']).order_by(t['works'].c.created_at.desc())).mappings():
                aliases=conn.execute(select(t['work_aliases'].c.alias).where(t['work_aliases'].c.work_id==work['id'])).scalars().all()
                rows.append(dict(work)|{'aliases':aliases})
            return rows
    def series(self,body:SeriesInput,key):
        def execute(conn):
            t=self.db.tables; self.db.owner(conn); wid=uuid4()
            conn.execute(t['works'].insert().values(id=wid,canonical_title=body.title,original_language=body.language,status='active'))
            for alias in dict.fromkeys([body.title]+body.aliases):
                if not normalize(alias) or len(alias)>160: raise HTTPException(422,'Invalid alias')
                conn.execute(insert(t['work_aliases']).values(work_id=wid,alias=alias,normalized_alias=normalize(alias),locale=body.language,status='verified',evidence_ref='Owner entered locally').on_conflict_do_nothing())
            self.db.audit(conn,'series_created',wid,{'title':body.title})
            return {'id':str(wid),'canonical_title':body.title,'aliases':[body.title]+body.aliases,'language':body.language}
        return self.db.command('series_create',key,body.model_dump(mode='json'),execute)
    def asset(self,conn,data,mime='image/png',stage='source',width=None,height=None):
        blob=self.storage.put_blob(data,mime)
        t=self.db.tables['media_assets']
        conn.execute(insert(t).values(id=uuid4(),bucket=self.storage.settings.bucket,object_key=blob['key'],sha256=blob['sha256'],size_bytes=len(data),mime_type=mime,width=width,height=height,stage=stage,rights_scope='internal-authorized').on_conflict_do_nothing(index_elements=['bucket','object_key']))
        row=conn.execute(select(t).where(t.c.bucket==self.storage.settings.bucket,t.c.object_key==blob['key'])).mappings().one()
        return str(row['id'])
    def import_source(self,body:SourceInput,key):
        if body.rights.basis=='unknown' or not body.rights.allow_internal:
            raise HTTPException(403,'An explicit rights basis and internal-use permission are required')
        if body.rights.expires_at and body.rights.expires_at.astimezone(timezone.utc)<=datetime.now(timezone.utc):
            raise HTTPException(403,'Source rights have expired')
        if [p.order for p in body.pages]!=list(range(1,len(body.pages)+1)):
            raise HTTPException(422,'Pages must be supplied once in consecutive reading order')
        decoded=[];total=0
        for page in body.pages:
            decoded.append(decode_page(page));total+=len(decoded[-1][0])+len(decoded[-1][3])
            if total>256_000_000:raise HTTPException(413,'Source bundle exceeds 256 MB decoded plus originals')
        def execute(conn):
            t=self.db.tables; self.db.owner(conn)
            conn.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:id,0))'),{'id':str(body.series_id)+body.chapter_key})
            work=conn.execute(select(t['works']).where(t['works'].c.id==body.series_id)).mappings().first()
            if not work: raise HTTPException(404,'Unknown series')
            # Canonical edition belongs to the work UUID, never its title/slug.
            editions=t['editions']
            edition=conn.execute(select(editions).where(editions.c.work_id==body.series_id,editions.c.provider=='manual')).mappings().first()
            if not edition:
                edition={'id':uuid4()}
                conn.execute(editions.insert().values(id=edition['id'],work_id=body.series_id,format='comic',provider='manual',provider_native_id=str(body.series_id),language=work['original_language'] or 'en',title=work['canonical_title']))
            ep=t['episodes']
            episode=conn.execute(select(ep).where(ep.c.edition_id==edition['id'],ep.c.chapter_key==body.chapter_key)).mappings().first()
            if episode:
                raise HTTPException(409,'This chapter already has a production. Open it instead of remaking it.')
            rights_id=uuid4()
            conn.execute(t['rights_manifests'].insert().values(id=rights_id,basis=body.rights.basis,rightsholder=body.rights.rightsholder,allowed_actions={'internal':True,'distribution':body.rights.allow_distribution},reviewer_id=OWNER,reviewed_at=func.now(),expires_at=body.rights.expires_at,notes=body.rights.evidence))
            episode_id,source_id,pid=uuid4(),uuid4(),uuid4()
            conn.execute(ep.insert().values(id=episode_id,edition_id=edition['id'],chapter_key=body.chapter_key,title=body.title,latest_source_revision=1))
            manifest=[{'order':p.order,'sha256':hashlib.sha256(raw).hexdigest(),'kind':p.kind} for p,(data,w,h,raw,mime) in zip(body.pages,decoded)]
            conn.execute(t['source_revisions'].insert().values(id=source_id,episode_id=episode_id,revision=1,manifest_sha256=sha(manifest),page_count=len(body.pages),status='inspected',import_method='manual-authorized-pages',rights_manifest_id=rights_id,imported_by=OWNER))
            pages=[]
            for page,(data,width,height,raw,mime) in zip(body.pages,decoded):
                original_aid=self.asset(conn,raw,mime=mime,width=width,height=height)
                aid=self.asset(conn,data,width=width,height=height); page_id,panel_id=uuid4(),uuid4()
                conn.execute(t['source_pages'].insert().values(id=page_id,source_revision_id=source_id,page_order=page.order,asset_id=original_aid,page_kind=page.kind,quality_json={'width':width,'height':height,'text_origin':'owner-transcribed'}))
                conn.execute(t['source_panels'].insert().values(id=panel_id,page_id=page_id,panel_order=1,box={'x':0,'y':0,'width':1,'height':1},panel_kind='unknown',source_crop_asset_id=aid,evidence_sha256=hashlib.sha256(raw).hexdigest()))
                for i,line in enumerate(page.text.splitlines(),1):
                    if line.strip(): conn.execute(t['ocr_lines'].insert().values(panel_id=panel_id,line_order=i,raw_text=line,classification='other',confidence=None,review_status='owner_transcribed'))
                pages.append({'id':str(page_id),'asset_id':aid,'original_asset_id':original_aid,'panel_id':str(panel_id),'order':page.order,'filename':page.filename,'text':page.text,'kind':page.kind,'width':width,'height':height})
            conn.execute(t['productions'].insert().values(id=pid,work_id=body.series_id,format='single',is_qa_only=False,status='SOURCE_REVIEW',rights_manifest_id=rights_id,created_by=OWNER))
            conn.execute(t['production_episodes'].insert().values(production_id=pid,episode_id=episode_id,ordinal=1))
            record={'id':str(pid),'series_id':str(body.series_id),'series_title':work['canonical_title'],'episode_id':str(episode_id),'chapter_key':body.chapter_key,'title':body.title,'revision':1,'source_id':str(source_id),'source_sha':sha(manifest),'rights_id':str(rights_id),'rights':body.rights.model_dump(mode='json'),'pages':pages,'beats':[],'script_approval':None,'status':'SOURCE_REVIEW','export':None,'qa':None,'review':None,'packaging':{'title':body.title,'description':'','tags':[],'title_locked':True,'description_locked':True},'notes':'','voice':'system-default','provider':'manual-editorial','created_at':datetime.now(timezone.utc).isoformat()}
            from .pronunciation import approved_map
            record['canon_revision']=work['latest_canon_revision'];record['pronunciations']=approved_map(self.db,conn,body.series_id)
            return self.db.save(conn,record,'source_imported',new=True)
        return self.db.command('source_import',key,body.model_dump(mode='json'),execute)
