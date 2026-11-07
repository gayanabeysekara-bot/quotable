#!/bin/bash
# usage: tools/sheet.sh <ep> <count>  -> out/<ep>/sheet.jpg (evenly spaced stills)
ep=$1; n=${2:-16}
T=$(python3 -c "import json;print(json.load(open('out/$ep/timings.json'))['total'])")
TS=$(python3 -c "print(','.join(str(round(($T-0.5)*(i+.5)/$n,2)) for i in range($n)))")
rm -rf out/$ep/stills; node tools/render.js $ep --still $TS || exit 1
python3 - "$ep" <<'PY'
import sys,glob; from PIL import Image
ep=sys.argv[1]; fs=sorted(glob.glob(f'out/{ep}/stills/*.jpg'),key=lambda f:float(f.split('/t')[-1][:-4]))
ims=[Image.open(f).resize((270,480)) for f in fs]; cols=8; rows=(len(ims)+7)//8
S=Image.new('RGB',(cols*270,rows*480)); [S.paste(im,((i%cols)*270,(i//cols)*480)) for i,im in enumerate(ims)]
S.save(f'out/{ep}/sheet.jpg',quality=85)
PY
