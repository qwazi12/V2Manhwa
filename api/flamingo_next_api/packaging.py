"""Source-backed rule-based packaging proposals; never a CTR prediction or auto-overwrite."""
import io,json
from uuid import uuid4
from PIL import Image,ImageDraw,ImageFont,ImageOps
from sqlalchemy import select
from fastapi import HTTPException
from .editorial import input_fingerprint,require_internal_rights
from .ingestion import Ingestion
from .product_db import OWNER

class Packaging:
    def __init__(self,db,storage):self.db,self.storage=db,storage
    def list(self,pid):
        table=self.db.tables['packaging_candidates']
        with self.db.engine.connect() as conn:
            record=self.db.load(conn,pid)
            result=[]
            for row in conn.execute(select(table).where(table.c.production_id==pid).order_by(table.c.created_at.desc()).limit(12)).mappings():
                proposal=json.loads(row['concept'])
                result.append(proposal|{'id':str(row['id']),'asset_id':str(row['image_asset_id']),'stale':proposal['input_sha']!=input_fingerprint(record)})
            return result
    def propose(self,pid,body,key):
        def execute(conn):
            record=self.db.load(conn,pid,True);self.db.require_revision(record,body.revision)
            require_internal_rights(record)
            if not record['beats'] or not record['script_approval'] or record['script_approval']['input_sha']!=input_fingerprint(record):raise HTTPException(409,'Approve a source-linked script before creating packaging proposals')
            result=[];indices=[0,len(record['beats'])//2,len(record['beats'])-1]
            styles=[('Quiet discovery','#e6bf87','#173c3f'),('Story turning point','#f0ddd0','#4b3148'),('The final promise','#d7e3be','#314935')]
            for i,(index,(style,ink,background)) in enumerate(zip(indices,styles)):
                beat=record['beats'][index];page=next(p for p in record['pages'] if p['id']==beat['page_id'])
                table=self.db.tables['media_assets']
                asset=conn.execute(select(table).where(table.c.id==page['asset_id'])).mappings().one()
                data=self.storage.read_blob(asset['object_key'],asset['sha256'])
                with Image.open(io.BytesIO(data)) as original:
                    x,y,w,h=beat['crop'];left=min(original.width-1,round(x*original.width));top=min(original.height-1,round(y*original.height))
                    cropped=original.crop((left,top,max(left+1,round((x+w)*original.width)),max(top+1,round((y+h)*original.height))))
                    image=ImageOps.fit(cropped.convert('RGB'),(1280,720),centering=(.5,.4))
                    draw=ImageDraw.Draw(image);draw.rectangle((0,470,1280,720),fill=background)
                    try:font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Georgia.ttf',58)
                    except OSError:font=ImageFont.load_default(size=50)
                    headline=beat['event'][:42]
                    for font_size in range(50,15,-2):
                        font=ImageFont.load_default(size=font_size)
                        if draw.textbbox((0,0),headline,font=font)[2]<=1170:break
                    draw.text((55,520),headline,font=font,fill=ink)
                    draw.text((58,650),record['series_title'][:60],font=ImageFont.load_default(size=22),fill='#ffffff')
                    output=io.BytesIO();image.save(output,format='PNG')
                aid=Ingestion(self.db,self.storage).asset(conn,output.getvalue(),stage='thumbnail',width=1280,height=720)
                proposal={'input_sha':input_fingerprint(record),'title':beat['event'][:100],'style':style,'source_page_id':page['id'],'source_beat_id':beat['id'],'method':'rule-based source layout','performance_prediction':None}
                candidate_id=uuid4()
                conn.execute(self.db.tables['packaging_candidates'].insert().values(id=candidate_id,production_id=pid,candidate_type='thumbnail',concept=json.dumps(proposal),source_event_ids=[beat['id']],image_asset_id=aid))
                result.append(proposal|{'id':str(candidate_id),'asset_id':aid,'stale':False})
            self.db.audit(conn,'packaging_proposals_created',pid,{'revision':record['revision']})
            return result
        return self.db.command('packaging_propose:'+str(pid),key,body.model_dump(mode='json'),execute)
    def apply(self,pid,candidate_id,body,key):
        def execute(conn):
            record=self.db.load(conn,pid,True);self.db.require_revision(record,body.revision)
            table=self.db.tables['packaging_candidates']
            row=conn.execute(select(table).where(table.c.id==candidate_id,table.c.production_id==pid)).mappings().first()
            if not row:raise HTTPException(404,'Unknown packaging proposal')
            proposal=json.loads(row['concept'])
            if proposal['input_sha']!=input_fingerprint(record):raise HTTPException(409,'Packaging proposal is stale after source/script/canon edits')
            record['packaging']['title']=proposal['title'];record['packaging']['thumbnail_asset_id']=str(row['image_asset_id']);record['packaging']['title_locked']=True;record['review']=None;record['vertical_review']=None
            conn.execute(table.update().where(table.c.id==candidate_id).values(selected_by=OWNER))
            return self.db.save(conn,record,'owner_applied_packaging_proposal')
        return self.db.command('packaging_apply:'+str(pid)+':'+str(candidate_id),key,body.model_dump(mode='json'),execute)
