"""Evidence-linked human findings. Never substitute a technical pass for editorial review."""
from datetime import datetime,timezone
from uuid import uuid4
from sqlalchemy import select,func
from fastapi import HTTPException
from .product_db import sha

class Findings:
    def __init__(self,db):self.db=db
    def list(self,pid):
        t=self.db.tables
        with self.db.engine.connect() as conn:
            self.db.load(conn,pid)
            return [dict(row)|{'kind':row['coverage']['kind'],'export_sha':row['coverage']['export_sha'],'beat_id':row['coverage']['beat_id'],'page_id':row['coverage']['page_id']} for row in conn.execute(select(t['qa_findings'],t['qa_reports'].c.coverage).join(t['qa_reports'],t['qa_reports'].c.id==t['qa_findings'].c.qa_report_id).where(t['qa_reports'].c.production_id==pid).order_by(t['qa_findings'].c.created_at.desc())).mappings()]
    def add(self,pid,body,key):
        def execute(conn):
            record=self.db.load(conn,pid,True);self.db.require_revision(record,body.revision)
            export=record.get('vertical_export' if body.kind=='vertical' else 'export')
            if not export:raise HTTPException(409,'A current video export is required for timestamped review')
            shot=next((s for s in export['manifest']['shots'] if s['beat_id']==str(body.beat_id)),None)
            if not shot:raise HTTPException(422,'The finding must reference a beat in this exact export')
            report_id,finding_id=uuid4(),uuid4();t=self.db.tables
            coverage={'kind':body.kind,'export_sha':export['sha256'],'beat_id':shot['beat_id'],'page_id':shot['page_id'],'input_sha':export['manifest']['input_sha']}
            conn.execute(t['qa_reports'].insert().values(id=report_id,production_id=pid,report_sha256=sha(coverage),check_version='human-finding-v1',status='FAIL',coverage=coverage,evaluator_kind='human'))
            fps=export['manifest']['fps']
            conn.execute(t['qa_findings'].insert().values(id=finding_id,qa_report_id=report_id,check_id=body.category,severity=body.severity,status='open',description=body.description,start_ms=round(shot['start_frame']/fps*1000),end_ms=round(shot['end_frame']/fps*1000)))
            record['vertical_review' if body.kind=='vertical' else 'review']=None
            if body.kind=='longform':record['status']='NEEDS_CHANGES'
            saved=self.db.save(conn,record,'human_quality_finding_added')
            return {'finding_id':str(finding_id),'revision':saved['revision']}
        return self.db.command('finding_add:'+str(pid),key,body.model_dump(mode='json'),execute)
    def resolve(self,pid,finding_id,body,key):
        def execute(conn):
            record=self.db.load(conn,pid,True);self.db.require_revision(record,body.revision);t=self.db.tables
            row=conn.execute(select(t['qa_findings'],t['qa_reports'].c.coverage).join(t['qa_reports'],t['qa_reports'].c.id==t['qa_findings'].c.qa_report_id).where(t['qa_findings'].c.id==finding_id,t['qa_reports'].c.production_id==pid).with_for_update(of=t['qa_findings'])).mappings().first()
            if not row:raise HTTPException(404,'Unknown finding for this episode')
            export=record.get('vertical_export' if row['coverage']['kind']=='vertical' else 'export')
            if not export:raise HTTPException(409,'Render and watch the current film before confirming a repair')
            if row['status']!='open':raise HTTPException(409,'This finding is already resolved')
            conn.execute(t['qa_findings'].update().where(t['qa_findings'].c.id==finding_id).values(status='verified_fixed',remediation=body.notes))
            record['vertical_review' if row['coverage']['kind']=='vertical' else 'review']=None
            record.setdefault('finding_resolutions',[]).append({'finding_id':str(finding_id),'export_sha':export['sha256'],'notes':body.notes,'reviewed_at':datetime.now(timezone.utc).isoformat()})
            return self.db.save(conn,record,'human_quality_repair_confirmed')
        return self.db.command('finding_resolve:'+str(pid)+':'+str(finding_id),key,body.model_dump(mode='json'),execute)

def require_no_critical_findings(db,conn,pid,kind):
    t=db.tables
    open_finding=conn.execute(select(t['qa_findings'].c.id).join(t['qa_reports'],t['qa_reports'].c.id==t['qa_findings'].c.qa_report_id).where(t['qa_reports'].c.production_id==pid,t['qa_reports'].c.coverage['kind'].astext==kind,t['qa_findings'].c.status=='open',t['qa_findings'].c.severity.in_(['P0','P1'])).limit(1)).scalar()
    if open_finding:raise HTTPException(409,'Resolve and retest open critical quality findings before approval')


def inherit_open_findings(db,conn,from_pid,to_pid):
    t=db.tables
    rows=conn.execute(select(t['qa_findings'],t['qa_reports'].c.coverage).join(t['qa_reports'],t['qa_reports'].c.id==t['qa_findings'].c.qa_report_id).where(t['qa_reports'].c.production_id==from_pid,t['qa_findings'].c.status=='open')).mappings().all()
    for row in rows:
        report_id=uuid4();coverage=dict(row['coverage'])|{'inherited_from_finding':str(row['id'])}
        conn.execute(t['qa_reports'].insert().values(id=report_id,production_id=to_pid,report_sha256=sha(coverage),check_version='inherited-human-finding-v1',status='FAIL',coverage=coverage,evaluator_kind='human'))
        conn.execute(t['qa_findings'].insert().values(id=uuid4(),qa_report_id=report_id,check_id=row['check_id'],severity=row['severity'],status='open',description=row['description'],start_ms=row['start_ms'],end_ms=row['end_ms']))
