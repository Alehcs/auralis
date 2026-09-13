"""Compose native PNGs; identical framing, no sharpening or color grading."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
p=Path(__file__).resolve().parent
font='/System/Library/Fonts/Supplemental/Arial.ttf'
W,H=1119,660
out=Image.new('RGB',(W*2,H*2+140),'#090b10');draw=ImageDraw.Draw(out)
for col,label in enumerate(['ANTES · FASE 7.1 / REV. 4','DESPUÉS · FASE 7.2']):
 draw.text((col*W+24,18),label,font=ImageFont.truetype(font,27),fill='#eee6d9')
for row,view in enumerate(['full','close']):
 for col,side in enumerate(['before','after']):
  im=Image.open(p/f'{side}-{view}.png').convert('RGBA');assert im.size==(W,H)
  bg=Image.new('RGBA',im.size,'#090b10');bg.alpha_composite(im)
  out.paste(bg,(col*W,60+row*H))
  if side=='after':bg.convert('RGB').save(p/f'hero-{view}.png')
 draw.text((24,60+row*H+12),'DISCO COMPLETO' if row==0 else 'DETALLE · MISMA CÁMARA EN AMBOS LADOS',font=ImageFont.truetype(font,18),fill='#bbada0')
draw.text((24,H*2+82),'HMI 29 MAR 2022 · 00:00:53 UTC · ESCALA 1× · SUPERFICIE PAUSADA',font=ImageFont.truetype(font,23),fill='#d8bd8c')
draw.text((24,H*2+114),'Recreación 3D guiada por HMI. El detalle visual no aumenta la resolución de la observación.',font=ImageFont.truetype(font,20),fill='#aab0bc')
out.save(p/'comparison.png')
