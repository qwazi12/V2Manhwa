"""Offline image safety checks; generated originals only, no account or database."""
import base64,io
from PIL import Image
from fastapi import HTTPException
import pytest
from flamingo_next_api.product_models import PageInput
from flamingo_next_api.ingestion import decode_page

def page(raw):return PageInput(order=1,filename='original.webp',data_base64=base64.b64encode(raw).decode())

def test_static_webp_preserves_original_and_normalizes_for_rendering():
    image=Image.new('RGB',(64,48),'#406a83');file=io.BytesIO();image.save(file,'WEBP',lossless=True);raw=file.getvalue()
    normalized,w,h,original,mime=decode_page(page(raw))
    assert original==raw and mime=='image/webp' and (w,h)==(64,48)
    with Image.open(io.BytesIO(normalized)) as decoded:assert decoded.format=='PNG' and decoded.getpixel((0,0))==(64,106,131)

def test_animated_webp_is_rejected():
    file=io.BytesIO();image=Image.new('RGB',(32,32),'white');image.save(file,'WEBP',save_all=True,append_images=[Image.new('RGB',(32,32),'black')],duration=200,loop=0)
    with pytest.raises(HTTPException,match='single-frame'):decode_page(page(file.getvalue()))

def test_transparent_source_uses_white_preview_without_modifying_original():
    file=io.BytesIO();Image.new('RGBA',(32,32),(0,0,0,0)).save(file,'PNG');raw=file.getvalue()
    normalized,_,_,original,_=decode_page(page(raw));assert original==raw
    with Image.open(io.BytesIO(normalized)) as decoded:assert decoded.getpixel((0,0))==(255,255,255)


def test_ocr_literal_quotes_do_not_swallow_tsv_rows(monkeypatch):
    from flamingo_next_api.source_analysis import SourceAnalyzer
    from flamingo_next_api.media_engine import MediaEngine
    import flamingo_next_api.source_analysis as module
    raw=io.BytesIO();Image.new('RGB',(32,32),'white').save(raw,'PNG')
    class Store:
        def read_blob(self,*args):return raw.getvalue()
    tsv='level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n5\t1\t1\t1\t1\t1\t1\t1\t5\t5\t90\t"\n5\t1\t2\t1\t1\t1\t2\t10\t20\t5\t95\tSECOND\n'
    monkeypatch.setattr(module.shutil,'which',lambda _: '/synthetic/tesseract')
    monkeypatch.setattr(MediaEngine,'run',lambda *args,**kwargs:tsv.encode())
    result=SourceAnalyzer(Store()).analyze({'pages':[{'id':'fixture-page','asset_id':'fixture-asset','text':'Owner text unchanged'}],'source_sha':'a'*64},{'fixture-asset':{'object_key':'fixture','sha256':'b'*64}})
    page=result['pages'][0]
    assert [w['text'] for w in page['words']]==['"','SECOND']
    assert page['proposed_text']=='"\nSECOND'
    assert page['owner_text']=='Owner text unchanged'


def test_pronunciation_is_literal_case_insensitive_and_non_recursive():
    from flamingo_next_api.pronunciation import for_speech
    text='Kim Seo-jun meets Seo-jun. NOTSEO-JUN is not his name.'
    result=for_speech(text,{'Kim Seo-jun':'Kim Suh Joon','Seo-jun':'Suh Joon','Joon':'unexpected recursive output'})
    assert result=='Kim Suh Joon meets Suh Joon. NOTSEO-JUN is not his name.'
    assert for_speech('KIM SEO-JUN',{'Kim Seo-jun':'Kim Suh Joon'})=='Kim Suh Joon'


def test_pronunciation_aliases_are_not_regular_expression_code():
    from flamingo_next_api.pronunciation import for_speech
    assert for_speech('A+B and ABC',{'A+B':'a plus bee'})=='a plus bee and ABC'

def test_conflicting_alias_pronunciations_are_excluded_regardless_of_query_order():
    from flamingo_next_api.pronunciation import unambiguous_map
    rows=[{'alias':'Lee','pronunciation':'Lee'}, {'alias':'LEE','pronunciation':'Lay'},
          {'alias':'Kim','pronunciation':'Gim'}, {'alias':'KIM','pronunciation':'Gim'}]
    assert unambiguous_map(rows)==unambiguous_map(list(reversed(rows)))=={'KIM':'Gim'}
