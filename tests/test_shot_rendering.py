"""Real offline filter/decode checks on original art; no DB or accounts."""
import json
import shutil
from PIL import Image,ImageDraw
import pytest
from flamingo_next_api.media_engine import MediaEngine

@pytest.mark.parametrize('motion',['static','zoom_in','zoom_out','pan_left','pan_right','scroll_down'])
def test_panel_backdrop_and_all_motions_decode_with_real_pixels(tmp_path,motion):
    if not shutil.which('ffmpeg'):pytest.skip('ffmpeg required')
    image=Image.new('RGB',(240,480),'#1c5570');draw=ImageDraw.Draw(image)
    draw.rectangle((40,50,200,430),fill='#d66b44');draw.ellipse((65,80,175,190),fill='#e5e0d0')
    source=tmp_path/'original.png';image.save(source);output=tmp_path/'shot.mp4'
    engine=MediaEngine(None);filters=engine.shot_filters({'crop':[0,0,1,1],'motion':motion},320,180,12)
    engine.run(['ffmpeg','-v','error','-y','-loop','1','-framerate','24','-i',str(source),'-vf',filters,'-frames:v','12','-an','-c:v','libx264',str(output)])
    probe=json.loads(engine.run(['ffprobe','-v','error','-show_streams','-of','json',str(output)]))['streams'][0]
    assert (probe['width'],probe['height'],int(probe['nb_frames']))==(320,180,12)
    raw=tmp_path/'decoded.rgb'
    engine.run(['ffmpeg','-v','error','-y','-i',str(output),'-frames:v','1','-f','rawvideo','-pix_fmt','rgb24',str(raw)])
    frame=Image.frombytes('RGB',(320,180),raw.read_bytes())
    # Sidebars should contain subdued original imagery, not empty black padding.
    assert sum(frame.getpixel((5,90)))>20
    assert frame.getpixel((160,100))!=frame.getpixel((5,90))
