"""Manual research and first-party analytics imports with explicit provenance."""
from datetime import datetime,timezone
from uuid import uuid4
from sqlalchemy import select,func
from fastapi import HTTPException

class Insights:
    def __init__(self,db):self.db=db
    def add_observation(self,body,key):
        if body.observed_at.astimezone(timezone.utc)>datetime.now(timezone.utc):raise HTTPException(422,'Observation time cannot be in the future')
        def execute(conn):
            t=self.db.tables
            rows=conn.execute(select(t['research_observations']).where(t['research_observations'].c.provider=='manual',t['research_observations'].c.native_id==body.video_id)).mappings().all()
            candidate=rows[0]['candidate_id'] if rows else uuid4()
            if not rows:conn.execute(t['research_candidates'].insert().values(id=candidate,proposed_title=body.title,status='needs_evidence'))
            if any(r['observed_at']==body.observed_at for r in rows):raise HTTPException(409,'This video already has an observation at that time')
            conn.execute(t['research_observations'].insert().values(candidate_id=candidate,provider='manual',native_id=body.video_id,source_url=body.source_url,observation_type='view_count',metric_name='views',metric_value=body.views,metric_unit='views',scope={'title':body.title,'genre':body.genre,'notes':body.notes,'provenance':'owner_supplied_unverified'},observed_at=body.observed_at,confidence='unverified'))
            self.db.audit(conn,'research_observation_added',candidate)
            return {'candidate_id':str(candidate),'provenance':'owner_supplied_unverified'}
        return self.db.command('research_observation',key,body.model_dump(mode='json'),execute)
    def research(self):
        t=self.db.tables
        with self.db.engine.connect() as conn:
            result=[]
            for candidate in conn.execute(select(t['research_candidates']).order_by(t['research_candidates'].c.discovered_at.desc())).mappings():
                observations=[dict(r) for r in conn.execute(select(t['research_observations']).where(t['research_observations'].c.candidate_id==candidate['id']).order_by(t['research_observations'].c.observed_at)).mappings()]
                velocity=None; interval=None; flags=[]
                if len(observations)>=2:
                    first,last=observations[-2:];interval=(last['observed_at']-first['observed_at']).total_seconds()/3600
                    delta=float(last['metric_value']-first['metric_value'])
                    if interval>0 and delta>=0:velocity=round(delta/interval,2)
                    else:flags.append('Counts decreased or observation interval is invalid; velocity unavailable.')
                if observations and (datetime.now(timezone.utc)-observations[-1]['observed_at']).days>7:flags.append('Latest observation is more than seven days old.')
                result.append(dict(candidate)|{'observations':observations,'views_per_hour':velocity,'interval_hours':interval,'confidence':'UNVERIFIED','competition':'unknown','demand':'unknown','flags':flags,'methodology':'Delta between the two latest owner-entered observations; no independent platform verification.'})
            return result
    def add_metric(self,body,key):
        if body.clicks>body.impressions:raise HTTPException(422,'Clicks cannot exceed impressions')
        if body.observed_at.astimezone(timezone.utc)>datetime.now(timezone.utc):raise HTTPException(422,'Metrics cannot be dated in the future')
        def execute(conn):
            record=self.db.load(conn,body.production_id)
            channels=self.db.tables['channels']
            channel=conn.execute(select(channels.c.id).where(channels.c.platform=='manual-analytics',channels.c.provider_channel_id=='owner-import')).scalar()
            if not channel:
                channel=uuid4();conn.execute(channels.insert().values(id=channel,platform='manual-analytics',provider_channel_id='owner-import',display_name='Manual owner analytics',status='disconnected'))
            conn.execute(self.db.tables['analytics_observations'].insert().values(channel_id=channel,provider='manual',metric_name='episode_snapshot',value=body.views,unit='views',dims=body.model_dump(mode='json')|{'provenance':'owner_supplied_unverified'},period_start=body.observed_at,period_end=body.observed_at))
            self.db.audit(conn,'manual_analytics_added',body.production_id)
            return {'production_id':str(body.production_id),'status':'saved','provenance':'owner_supplied_unverified'}
        return self.db.command('manual_metric',key,body.model_dump(mode='json'),execute)
    def analytics(self):
        t=self.db.tables['analytics_observations']
        with self.db.engine.connect() as conn:
            result=[]
            for row in conn.execute(select(t).where(t.c.provider=='manual').order_by(t.c.observed_at.desc()).limit(200)).mappings():
                item=dict(row['dims']);record=self.db.load(conn,item['production_id'])
                duration=record.get('export',{}).get('duration_seconds') if record.get('export') else None
                item['ctr']=item['clicks']/item['impressions'] if item['impressions'] else None
                item['timeline']=[{'seconds':round(i/(len(item['retention'])-1)*duration,2) if duration and len(item['retention'])>1 else None,'ratio':ratio} for i,ratio in enumerate(item['retention'])]
                item['episode_title']=record['title'];result.append(item)
            return result
