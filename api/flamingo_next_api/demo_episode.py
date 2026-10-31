"""Original geometric gold fixture; no copied artwork, model or external media."""
import base64
import io
from uuid import uuid5,NAMESPACE_URL
from PIL import Image,ImageDraw,ImageFont
from .product_models import SourceInput,SeriesInput,EditInput

STORY=[
 ('The beacon wakes','At dawn, a lone keeper notices a light in the abandoned beacon. She takes her lantern and starts toward the cliffs.'),
 ('Across the crossing','The old crossing has fallen into the sea. The keeper finds a narrow path between the rocks and continues on foot.'),
 ('A signal returned','At the beacon, she raises her lantern. A second light answers from beyond the horizon. Someone is still out there.'),
]

def fixture_pages():
    result=[]
    for i,(title,text) in enumerate(STORY):
        image=Image.new('RGB',(1280,720),(18+i*8,42+i*4,48+i*6));draw=ImageDraw.Draw(image)
        draw.ellipse((810,75,1040,305),fill=(228,186-i*12,126))
        draw.polygon([(0,650),(285,220+i*25),(700,650)],fill=(48,86,88))
        draw.polygon([(450,720),(880,250),(1280,720)],fill=(29,64,69))
        draw.rectangle((580,300,620,560),fill=(8,28,33));draw.ellipse((574,270,626,322),fill=(8,28,33))
        draw.rectangle((650,335,678,380),fill=(236,188,110));draw.line((610,325,650,350),fill=(8,28,33),width=12)
        try:font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Georgia.ttf',42)
        except OSError:font=ImageFont.load_default(size=42)
        draw.text((65,600),title,font=font,fill=(242,234,215));draw.text((65,45),'FLAMINGO ORIGINAL / AUTHORED FIXTURE',fill=(170,196,183),font=ImageFont.load_default(size=18))
        output=io.BytesIO();image.save(output,format='PNG')
        result.append({'order':i+1,'filename':f'page-{i+1:02}.png','data_base64':base64.b64encode(output.getvalue()).decode(),'text':text,'kind':'story'})
    return result

def create_demo(ingestion,editorial,key):
    key=str(uuid5(NAMESPACE_URL,key))
    series=ingestion.series(SeriesInput(title='The Last Beacon',aliases=['마지막 등대']),key+'-series')
    record=ingestion.import_source(SourceInput.model_validate({'series_id':series['id'],'chapter_key':'original-1','title':'The Last Beacon — A Signal Returned','rights':{'basis':'original','rightsholder':'Flamingo local fixture authors','evidence':'Geometric art and narrative authored inside this repository for offline testing.','allow_internal':True,'allow_distribution':False},'pages':fixture_pages()}),key+'-source')
    beats=[{'id':str(uuid5(NAMESPACE_URL,p['id'])), 'page_id':p['id'],'spoken_text':STORY[i][1],'event':STORY[i][0],'crop':[0,0,1,1]} for i,p in enumerate(record['pages'])]
    return editorial.edit(record['id'],EditInput.model_validate({'revision':record['revision'],'beats':beats}),key+'-script')
