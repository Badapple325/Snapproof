"""Quick test to validate that generated multipage PDF contains internal anchors and comments.
This test is lightweight: it builds a small set of in-memory photos, calls
`generate_multipage_proof_pdf` and then scans the returned PDF bytes for
expected anchor names (e.g., "photo_1") and for a sample comment string.

This is intentionally permissive: some PDF generators may obfuscate exact
anchor text, but in ReportLab platypus anchors the anchor name appears in
PDF text streams. We look for the anchor id and the comment text as plain
byte substrings.
"""

import io
from PIL import Image
from utils import generate_multipage_proof_pdf


def make_test_image(color=(200, 100, 50), size=(200, 160)):
    im = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    im.save(buf, format="JPEG")
    return buf.getvalue()


def test_pdf_contains_anchors_and_comments():
    print("Starting anchor validation test")
    photos = []
    for i in range(3):
        photos.append({
            "bytes": make_test_image(color=(50 + i * 30, 100, 150)),
            "filename": f"img_{i+1}.jpg",
            "timestamp": "2025-11-20 12:00:00",
            "comment": f"This is comment for photo {i+1}",
        })

    statement = "Here are Photo 1 and Photo 2 referenced in the statement."
    photo_comments = {i: p.get("comment", "") for i, p in enumerate(photos)}

    pdf_bytes = generate_multipage_proof_pdf(photos, statement, photo_comments=photo_comments)

    assert isinstance(pdf_bytes, (bytes, bytearray))
    # quick header check
    assert pdf_bytes[:4] == b"%PDF", "Not a PDF"

    # Search for at least one anchor id (photo_1) and one comment text
    found_anchor = b"photo_1" in pdf_bytes or b"photo_2" in pdf_bytes
    found_comment = b"This is comment for photo 1" in pdf_bytes or b"This is comment for photo 2" in pdf_bytes

    print(f"anchor_found={found_anchor}, comment_found={found_comment}")

    assert found_anchor, "No photo anchor identifiers found in PDF bytes"
    assert found_comment, "No photo comments found in PDF bytes"


if __name__ == "__main__":
    test_pdf_contains_anchors_and_comments()
    print("Anchor validation test passed")
