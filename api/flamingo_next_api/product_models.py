"""Strict editing/import contracts. All source and provider text is data."""
from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True, allow_inf_nan=False)

class SeriesInput(Strict):
    title: str = Field(min_length=1,max_length=160)
    language: str = Field(default='en',min_length=2,max_length=16)
    aliases: list[str] = Field(default_factory=list,max_length=30)

class RightsInput(Strict):
    basis: Literal['original','licensed','public_domain','reviewed_exception','unknown']
    rightsholder: str = Field(min_length=1,max_length=200)
    evidence: str = Field(min_length=1,max_length=2000)
    allow_internal: bool = False
    allow_distribution: bool = False
    expires_at: AwareDatetime | None = None

class PageInput(Strict):
    order: int = Field(ge=1,le=80)
    filename: str = Field(min_length=1,max_length=128)
    data_base64: str = Field(min_length=4,max_length=7_000_000)
    text: str = Field(default='',max_length=12000)
    kind: Literal['story','cover','credit','advert','divider','unknown'] = 'story'

class SourceInput(Strict):
    series_id: UUID
    chapter_key: str = Field(min_length=1,max_length=80)
    title: str = Field(min_length=1,max_length=160)
    rights: RightsInput
    pages: list[PageInput] = Field(min_length=1,max_length=80)

class BeatInput(Strict):
    id: UUID
    page_id: UUID
    spoken_text: str = Field(min_length=1,max_length=1600)
    event: str = Field(min_length=1,max_length=600)
    crop: tuple[float,float,float,float] = (0,0,1,1)
    motion: Literal['static','zoom_in','zoom_out','pan_left','pan_right','scroll_down'] = 'static'
    @field_validator('crop')
    @classmethod
    def valid_crop(cls, value):
        x,y,w,h=value
        if min(x,y)<0 or min(w,h)<=0 or max(x+w,y+h)>1.000001:
            raise ValueError('Crop must be inside the original source image')
        return value
    @field_validator('spoken_text')
    @classmethod
    def reject_assistant_output(cls,value):
        if any(s in value.casefold() for s in ('would you like me','as an ai','here is your script','ignore previous instructions')):
            raise ValueError('Assistant instructions cannot enter narration')
        return value

class EditInput(Strict):
    revision: int = Field(ge=1)
    beats: list[BeatInput] = Field(min_length=1,max_length=100)
    notes: str = Field(default='',max_length=4000)
    voice: Literal['system-default','kokoro-am_michael-v1','kokoro-bm_george-v1','kokoro-af_heart-v1'] = 'system-default'

class RevisionInput(Strict):
    revision: int = Field(ge=1)

class ScriptApproval(RevisionInput):
    confirmed_source_review: Literal[True]

class PackageInput(RevisionInput):
    title: str = Field(min_length=1,max_length=100)
    description: str = Field(min_length=1,max_length=5000)
    tags: list[str] = Field(default_factory=list,max_length=30)
    title_locked: bool = True
    description_locked: bool = True

class RightsRevisionInput(RevisionInput):
    rights: RightsInput

class ReviewInput(RevisionInput):
    kind: Literal['longform','vertical'] = 'longform'
    confirmed_watched: Literal[True]
    confirmed_rights: Literal[True]
    decision: Literal['approve','needs_changes']
    notes: str = Field(min_length=1,max_length=2000)

class ResearchInput(Strict):
    title: str = Field(min_length=1,max_length=160)
    source_url: str = Field(min_length=8,max_length=1000)
    video_id: str = Field(min_length=1,max_length=80)
    observed_at: AwareDatetime
    views: int = Field(ge=0)
    genre: str = Field(default='',max_length=80)
    notes: str = Field(default='',max_length=2000)
    @field_validator('source_url')
    @classmethod
    def public_url(cls,value):
        from urllib.parse import urlparse
        import ipaddress
        parsed=urlparse(value)
        if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.hostname in ('localhost','metadata.google.internal') or '.' not in parsed.hostname:
            raise ValueError('Use a public HTTPS evidence URL; the app does not fetch it')
        try:
            if not ipaddress.ip_address(parsed.hostname).is_global:
                raise ValueError('Private addresses are not evidence URLs')
        except ValueError as e:
            if 'Private' in str(e): raise
        return value

class MetricInput(Strict):
    production_id: UUID
    observed_at: AwareDatetime
    impressions: int = Field(ge=0)
    clicks: int = Field(ge=0)
    views: int = Field(ge=0)
    average_view_seconds: float = Field(ge=0)
    retention: list[float] = Field(default_factory=list,max_length=100)
    @field_validator('retention')
    @classmethod
    def retention_range(cls,v):
        if any(not 0 <= p <= 1 for p in v): raise ValueError('Retention ratios must be 0..1')
        return v


class RestoreInput(RevisionInput):
    restore_revision: int = Field(ge=1)

class CharacterInput(Strict):
    id: UUID | None = None
    name: str = Field(min_length=1,max_length=100)
    aliases: list[str] = Field(default_factory=list,max_length=20)
    pronunciation: str = Field(default='',max_length=180)
    notes: str = Field(default='',max_length=2000)
    evidence_page_id: UUID

class CanonInput(Strict):
    revision: int = Field(ge=0)
    confirmed_source_review: Literal[True]
    character: CharacterInput
    fact: str = Field(default='',max_length=1000)

class FindingInput(RevisionInput):
    kind: Literal['longform','vertical'] = 'longform'
    beat_id: UUID
    category: Literal['story','voice','visual','timing','rights','packaging']
    severity: Literal['P0','P1','P2','P3']
    description: str = Field(min_length=1,max_length=2000)

class FindingResolution(RevisionInput):
    confirmed_retest: Literal[True]
    notes: str = Field(min_length=1,max_length=2000)
