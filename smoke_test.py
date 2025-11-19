"""Headless smoke test for SnapProof.

This creates a simple test image in memory, calls the helper to produce a PDF,
writes the PDF to disk, and checks that the output looks like a PDF.
"""
from PIL import Image, ImageDraw
import io
import os
from utils import generate_proof_pdf


def make_test_image(width=800, height=400, color=(220, 100, 100)) -> bytes:
    img = Image.new("RGB", (width, height), color=color)
    draw = ImageDraw.Draw(img)
    draw.text((20, 20), "SnapProof Smoke Test", fill=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def run_smoke_test():
    img_bytes = make_test_image()
    pdf_bytes = generate_proof_pdf(img_bytes, "test.jpg", "Smoke test: generate proof")

    # Write PDF to disk for manual inspection
    out_pdf = "smoke_test_proof.pdf"
    with open(out_pdf, "wb") as f:
        f.write(pdf_bytes)

    # Basic validation
    if pdf_bytes[:4] == b"%PDF":
        print("SMOKE TEST OK: PDF generated and saved to", out_pdf)
    else:
        print("SMOKE TEST FAILED: Output does not look like a PDF")


if __name__ == "__main__":
    run_smoke_test()
