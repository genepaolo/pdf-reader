"""Stamp the depiction-asterisk on a portrait: top-right corner, white * with black outline.
Usage: py -3.12 mark_depiction.py <image path>   (edits in place)"""
from PIL import Image, ImageDraw, ImageFont
import sys
p = sys.argv[1]
im = Image.open(p).convert('RGB')
w, h = im.size
size = max(48, round(w * 0.16))
font = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', size)
d = ImageDraw.Draw(im)
bb = d.textbbox((0, 0), '*', font=font)
tw = bb[2] - bb[0]
x = w - tw - round(w * 0.035) - bb[0]
y = round(w * 0.01) - bb[1]
d.text((x, y), '*', font=font, fill=(255, 255, 255), stroke_width=max(3, size // 16), stroke_fill=(20, 20, 20))
im.save(p, optimize=True)
print('marked', p, im.size)
