"""Literal owner-approved pronunciation substitutions; no SSML or instructions."""
import re
from sqlalchemy import select

def unambiguous_map(rows):
    """Conflicting case-insensitive aliases keep their original spoken spelling."""
    grouped={}
    for row in rows:
        if row['pronunciation']:
            grouped.setdefault(row['alias'].casefold(),[]).append(row)
    return {min(row['alias'] for row in group):group[0]['pronunciation']
            for group in grouped.values()
            if len({row['pronunciation'] for row in group})==1}

def approved_map(db,conn,wid):
    t=db.tables
    rows=conn.execute(select(t['character_aliases'].c.alias,t['character_aliases'].c.pronunciation).join(t['characters'],t['characters'].c.id==t['character_aliases'].c.character_id).where(t['characters'].c.work_id==wid,t['characters'].c.identity_status=='approved',t['character_aliases'].c.status=='approved')).mappings()
    return unambiguous_map(rows)

def for_speech(text,mapping):
    if not mapping:return text
    # Longer names win; one regex pass prevents recursive replacement of output.
    aliases=sorted(mapping,key=len,reverse=True);lookup={alias.casefold():mapping[alias] for alias in aliases}
    pattern=re.compile(r'(?<!\w)('+ '|'.join(re.escape(alias) for alias in aliases)+r')(?!\w)',re.IGNORECASE)
    return pattern.sub(lambda match:lookup[match.group(0).casefold()],text)
