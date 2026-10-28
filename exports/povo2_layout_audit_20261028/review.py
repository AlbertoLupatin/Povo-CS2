from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
root=Path(__file__).resolve().parents[2]
archive=root/'data/reference/povo_photos/walk_2026-10-27/wetransfer_image00001-jpeg_2026-10-27_1300'
sheet=Image.new('RGB',(1800,1500),'white'); draw=ImageDraw.Draw(sheet)
for i,n in enumerate((31,34,35,37,38,40,43,44,45)):
    im=ImageOps.exif_transpose(Image.open(archive/f'image{n:05}.jpeg'))
    im.thumbnail((590,465)); x=i%3*600; y=i//3*500
    sheet.paste(im,(x,y+25)); draw.text((x+8,y+5),f'27 October photo {n}',fill='black')
sheet.save(Path(__file__).parent/'reference_contact.jpg',quality=94)
