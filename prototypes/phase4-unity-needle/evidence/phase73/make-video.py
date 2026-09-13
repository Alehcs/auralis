from pathlib import Path
import subprocess
from PIL import Image,ImageDraw,ImageFont
p=Path(__file__).resolve().parent
label=Image.new('RGB',(2238,740),'#090b10');d=ImageDraw.Draw(label)
font='/System/Library/Fonts/Supplemental/Arial.ttf'
for x,t in [(24,'ANTES · FASE 7.2'),(1143,'DESPUÉS · FASE 7.3')]:d.text((x,12),t,font=ImageFont.truetype(font,25),fill='white')
d.text((24,704),'29 MAR 2022 · cámara fija · escala 1× · movimiento ilustrativo; último segundo pausado',font=ImageFont.truetype(font,23),fill='#d8bd8c');label.save(p/'video-label.png')
args=['ffmpeg','-y','-hide_banner','-loglevel','error']
for s in ['before','after']:args+=['-c:v','libvpx-vp9','-i',str(p/f'{s}-motion.webm')]
args+=['-loop','1','-framerate','30','-i',str(p/'video-label.png')]
f=[]
for i in range(2):
 f += [f'color=c=0x090b10:s=1119x660:r=30:d=10[bg{i}]',f'[bg{i}][{i}:v]overlay=shortest=1:format=auto,fps=30,tpad=stop_mode=clone:stop_duration=1,trim=duration=9,setpts=PTS-STARTPTS[v{i}]']
f+=['[v0][v1]hstack[pair];[2:v][pair]overlay=0:42:shortest=1,format=yuv420p[out]']
args+=['-filter_complex',';'.join(f),'-map','[out]','-an','-c:v','libx264','-crf','16','-preset','medium','-movflags','+faststart',str(p/'comparison-motion.mp4')]
subprocess.run(args,check=True)
