import traceback
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

print('Starting multi-photo PDF test')
try:
    from utils import generate_multipage_proof_pdf

    # create 3 in-memory test photos (colored rectangles with labels)
    photos = []
    for i, color in enumerate([(200, 50, 50), (50, 200, 50), (50, 50, 200)], start=1):
        img = Image.new('RGB', (1200, 800), color=color)
        d = ImageDraw.Draw(img)
        text = f'Test Photo {i}'
        try:
            # try a default font (may vary by system)
            font = ImageFont.load_default()
        except Exception:
            font = None
        d.text((50, 50), text, fill=(255, 255, 255), font=font)
        b = BytesIO()
        img.save(b, format='JPEG')
        photos.append({'bytes': b.getvalue(), 'filename': f'test_photo_{i}.jpg', 'timestamp': datetime.now().isoformat()})

    statement = 'This is an automated multi-photo PDF test.'
    pdf_bytes = generate_multipage_proof_pdf(photos, statement)
    out_path = 'multi_test_proof.pdf'
    with open(out_path, 'wb') as f:
        f.write(pdf_bytes)

    # quick header check
    ok = pdf_bytes[:4] == b'%PDF'
    print('Generated', out_path, 'header_ok=', ok)
except Exception:
    print('Exception during multi-photo PDF test:')
    traceback.print_exc()
