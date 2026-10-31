"""Explicit owner-reviewed Series Bible, source-scoped evidence and invalidation."""
from uuid import uuid4
from sqlalchemy import select,func,text
from sqlalchemy.dialects.postgresql import insert
from fastapi import HTTPException
from .product_db import OWNER

class Canon:
    def __init__(self,db):self.db=db
    def get(self,wid):
        t=self.db.tables
        with self.db.engine.connect() as conn:
            work=conn.execute(select(t['works']).where(t['works'].c.id==wid)).mappings().first()
            if not work:raise HTTPException(404,'Unknown series')
            characters=[]
            for row in conn.execute(select(t['characters']).where(t['characters'].c.work_id==wid)).mappings():
                aliases=[dict(r) for r in conn.execute(select(t['character_aliases']).where(t['character_aliases'].c.character_id==row['id'])).mappings()]
                characters.append(dict(row)|{'aliases':aliases})
            facts=[dict(r) for r in conn.execute(select(t['canon_claims']).where(t['canon_claims'].c.work_id==wid).order_by(t['canon_claims'].c.created_at)).mappings()]
            return {'series_id':str(wid),'revision':work['latest_canon_revision'],'characters':characters,'facts':facts}
    def approve(self,wid,body,key):
        def execute(conn):
            t=self.db.tables;self.db.owner(conn)
            work=conn.execute(select(t['works']).where(t['works'].c.id==wid).with_for_update()).mappings().first()
            if not work:raise HTTPException(404,'Unknown series')
            if work['latest_canon_revision']!=body.revision:raise HTTPException(409,'The Series Bible changed. Refresh before approving.')
            page=conn.execute(select(t['source_pages'],t['source_panels'].c.id.label('panel_id')).join(t['source_panels'],t['source_panels'].c.page_id==t['source_pages'].c.id).join(t['source_revisions'],t['source_revisions'].c.id==t['source_pages'].c.source_revision_id).join(t['episodes'],t['episodes'].c.id==t['source_revisions'].c.episode_id).join(t['editions'],t['editions'].c.id==t['episodes'].c.edition_id).where(t['source_pages'].c.id==body.character.evidence_page_id,t['editions'].c.work_id==wid)).mappings().first()
            if not page:raise HTTPException(422,'The character evidence page must belong to this exact series')
            characters=t['characters'];character_id=body.character.id or uuid4();old=None
            if body.character.id:
                old=conn.execute(select(characters).where(characters.c.id==character_id,characters.c.work_id==wid)).mappings().first()
                if not old:raise HTTPException(422,'Character belongs to another series or does not exist')
                conn.execute(characters.update().where(characters.c.id==character_id).values(canonical_name=body.character.name,identity_status='approved',notes=body.character.notes))
            else:conn.execute(characters.insert().values(id=character_id,work_id=wid,canonical_name=body.character.name,identity_status='approved',notes=body.character.notes))
            for alias in dict.fromkeys([body.character.name]+body.character.aliases):
                conn.execute(insert(t['character_aliases']).values(character_id=character_id,alias=alias,locale=work['original_language'],pronunciation=body.character.pronunciation,status='approved',evidence={'page_id':str(page['id'])}).on_conflict_do_update(index_elements=['character_id','alias','locale'],set_={'pronunciation':body.character.pronunciation,'status':'approved'}))
            revision_id=uuid4();revision=body.revision+1
            conn.execute(t['canon_revisions'].insert().values(id=revision_id,work_id=wid,revision=revision,reviewed_by=OWNER,reason='Explicit local owner source review'))
            if body.fact:
                evidence_id,claim_id=uuid4(),uuid4()
                conn.execute(t['evidence_refs'].insert().values(id=evidence_id,evidence_kind='source_panel',panel_id=page['panel_id'],source_asset_id=page['asset_id'],rights_scope='internal-authorized',description='Owner-selected source page'))
                conn.execute(t['canon_claims'].insert().values(id=claim_id,work_id=wid,revision_id=revision_id,subject_character_id=character_id,predicate='owner_reviewed_fact',value={'text':body.fact},truth_class='approved_canon',status='approved'))
                conn.execute(t['canon_claim_evidence'].insert().values(claim_id=claim_id,evidence_id=evidence_id,support_type='supports'))
            conn.execute(t['works'].update().where(t['works'].c.id==wid).values(latest_canon_revision=revision))
            # Update only productions whose script contains affected identity terms.
            invalidated=[];terms=[body.character.name]+body.character.aliases+([old['canonical_name']] if old else [])
            episodes=t['studio_episodes']
            for row in conn.execute(select(episodes).join(t['productions'],t['productions'].c.id==episodes.c.production_id).where(t['productions'].c.work_id==wid).with_for_update(of=episodes)).mappings():
                record=dict(row['payload']);spoken=' '.join(b['spoken_text'] for b in record['beats']).casefold()
                if body.fact or any(term.casefold() in spoken for term in terms if term):
                    from .pronunciation import approved_map
                    record['pronunciations']=approved_map(self.db,conn,wid)
                    record.update(canon_revision=revision,script_approval=None,export=None,vertical_export=None,vertical_qa=None,vertical_review=None,qa=None,review=None,status='SCRIPT_REVIEW')
                    self.db.save(conn,record,'canon_change_invalidated_dependencies');invalidated.append(record['id'])
            self.db.audit(conn,'canon_approved',wid,{'revision':revision,'character_id':str(character_id)})
            return {'series_id':str(wid),'revision':revision,'character_id':str(character_id),'invalidated_production_ids':invalidated}
        return self.db.command('canon_approve:'+str(wid),key,body.model_dump(mode='json'),execute)
