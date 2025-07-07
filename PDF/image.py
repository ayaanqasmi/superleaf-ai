import fitz  # PyMuPDF
from PIL import Image
import io
import os

def extract_images_and_captions(pdf_path, output_dir="extracted_images"):
    """
    Extracts images and associated captions from a PDF file.

    Args:
        pdf_path (str): Path to the PDF file.
        output_dir (str): Directory to save extracted images.

    Returns:
        List of dicts: Each containing image path and its caption.
    """
    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    results = []

    for page_number, page in enumerate(doc):
        text_blocks = page.get_text("blocks")  # Get text blocks with coordinates
        images = page.get_images(full=True)

        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            image = Image.open(io.BytesIO(image_bytes))

            image_filename = f"page{page_number + 1}_img{img_index + 1}.{image_ext}"
            image_path = os.path.join(output_dir, image_filename)
            image.save(image_path)

            # Get the rectangle of the image on the page
            img_rects = [r for r in page.get_image_rects(xref)]
            caption_text = None

            for rect in img_rects:
                # Heuristic: look for text directly below or above the image
                possible_captions = []
                for block in text_blocks:
                    bx, by, bx1, by1, text, *_ = block
                    # Check if it's below the image
                    if bx1 > rect.x0 and bx < rect.x1:
                        if rect.y1 <= by <= rect.y1 + 50:  # Below
                            possible_captions.append((by, text.strip()))
                        elif rect.y0 - 50 <= by1 <= rect.y0:  # Above
                            possible_captions.append((by1, text.strip()))

                if possible_captions:
                    # Pick the closest one vertically
                    caption_text = sorted(possible_captions, key=lambda t: abs(t[0] - rect.y1))[0][1]
                    break  # We found caption for this image rect

            results.append({
                "page": page_number + 1,
                "image_path": image_path,
                "caption": caption_text or "No caption found"
            })

    return results

if __name__ == "__main__":
    pdf_file = "test.pdf"
    data = extract_images_and_captions(pdf_file)

    for item in data:
        print(f"Page {item['page']}:")
        print(f"Image saved at: {item['image_path']}")
        print(f"Caption: {item['caption']}")
        print("-" * 40)
