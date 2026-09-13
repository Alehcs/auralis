#!/usr/bin/env python3
"""Compose native canvas captures with unchanged time, color and crop per pair."""
import subprocess
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
P=Path(__file__).resolve().parent
font='/System/Library/Fonts/Supplemental/Arial.ttf'
for view in ('full','close'):
    args=['ffmpeg','-y','-hide_banner','-loglevel','error']
    for revision in ('before','after'):
        args += ['-c:v','libvpx-vp9','-i',str(P/f'{revision}-{view}.webm')]
    title='DISCO COMPLETO' if view=='full' else 'VISTA CERCANA'
    label=Image.new('RGB',(1712,962),'#090b10');d=ImageDraw.Draw(label)
    def text(x,y,t,size,color):d.text((x,y),t,font=ImageFont.truetype(font,size),fill=color)
    text(24,16,'ANTES · REVISIÓN 2',22,'white');text(880,16,'DESPUÉS · REVISIÓN 4',22,'white')
    text(24,49,title+' · HMI 24 MAR 2022 · CÁMARA FIJA · VELOCIDAD 1×',17,'#d8bd8c')
    text(24,938,'Movimiento ilustrativo. Regiones HMI ancladas. Último segundo pausado.',16,'#aab0bc')
    label.save(P/f'label-{view}.png')
    args += ['-loop','1','-framerate','30','-i',str(P/f'label-{view}.png')]
    filters=[]
    for i in range(2):
        filters += [f'color=c=0x090b10:s=1206x855:r=30:d=10[bg{i}]',f'[bg{i}][{i}:v]overlay=shortest=1:format=auto,crop=854:854:176:0,scale=856:856,fps=30,tpad=stop_mode=clone:stop_duration=1,trim=duration=9,setpts=PTS-STARTPTS[v{i}]']
    filters += ['[v0][v1]hstack[pair];[2:v][pair]overlay=0:80:shortest=1,format=yuv420p[out]']
    args += ['-filter_complex',';'.join(filters),'-map','[out]','-an','-c:v','libx264','-crf','16','-preset','medium','-movflags','+faststart',str(P/f'comparison-{view}.mp4')]
    subprocess.run(args,check=True)
(P/'concat.txt').write_text("file 'comparison-full.mp4'\nfile 'comparison-close.mp4'\n")
subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-f','concat','-safe','0','-i',str(P/'concat.txt'),'-c','copy','-movflags','+faststart',str(P/'comparison-18s.mp4')],check=True)
