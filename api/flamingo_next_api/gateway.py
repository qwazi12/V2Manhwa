"""Deterministic fake provider. Mock units are never US dollars or real usage."""
from pydantic import BaseModel, ConfigDict, Field

class FakeResult(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    provider: str = Field(pattern='^deterministic-fake-v1$')
    units: int = Field(ge=0, le=5)
    summary: str = Field(min_length=1, max_length=256)

class FakeGateway:
    def execute(self, reservation):
        if reservation is None or reservation['reserved_units'] < 2 or reservation['settled_units'] is not None:
            raise ValueError('An unused mock budget reservation is required')
        return FakeResult.model_validate({'provider':'deterministic-fake-v1', 'units':2,
            'summary':'Original synthetic cover prepared. Story, voice and video production are not implemented.'})

# Entirely original geometric fixture. No third-party media or model calls.
PREVIEW = b'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="675" viewBox="0 0 1200 675">
<defs><linearGradient id="sky" x2="1" y2="1"><stop stop-color="#253c46"/><stop offset="1" stop-color="#071a20"/></linearGradient></defs>
<path fill="url(#sky)" d="M0 0h1200v675H0z"/><circle cx="835" cy="205" r="122" fill="#e7bb7e"/>
<path fill="#193d43" d="m0 490 230-310 290 340 195-180 235 190 250-250v395H0z"/>
<path fill="#10292e" d="m0 560 330-240 340 270 190-140 340 110v115H0z"/>
<path fill="#081f24" d="m490 675 40-150 22-170 38-25 29 25 19 170 90 150z"/>
<path stroke="#cfaa72" stroke-width="4" d="m680 650 40-280"/>
<text x="65" y="80" fill="#a1c1bf" font-family="sans-serif" font-size="18" letter-spacing="6">FLAMINGO ORIGINAL / SYNTHETIC FIXTURE</text>
<text x="65" y="560" fill="#f8f0df" font-family="serif" font-size="65">Beyond the last horizon.</text>
<text x="68" y="611" fill="#a1c1bf" font-family="sans-serif" font-size="19">LOCAL PREVIEW  /  NOT A VIDEO EXPORT</text></svg>'''
