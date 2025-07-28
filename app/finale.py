from paddleocr import LayoutDetection
import easyocr
import fitz 
import time
import glob
import json
import os
from PIL import Image

thresh = {
    0: 0.5,    # paragraph_title
    1: 1.0,    # image
    2: 1.0,    # text
    3: 1.0,    # number
    4: 1.0,    # abstract
    5: 1.0,    # content
    6: 1.0,    # figure_title
    7: 1.0,    # formula
    8: 1.0,    # table
    9: 0.5,    # table_title
    10: 1.0,   # reference
    11: 0.25,   # doc_title
    12: 1.0,   # footnote
    13: 1.0,   # header
    14: 1.0,   # algorithm
    15: 1.0,   # footer
    16: 1.0,   # seal
    17: 1.0,   # chart_title
    18: 1.0,   # chart
    19: 1.0,   # formula_number
    20: 1.0,   # header_image
    21: 1.0,   # footer_image
    22: 1.0    # aside_text
}

reader = easyocr.Reader(lang_list=['en', 'ch_sim'],
                        model_storage_directory='models',
                        detector=False 
                        )
model = LayoutDetection(model_name="PP-DocLayout-L",
                            threshold=thresh,
                            device= "cpu",
                            layout_nms=True,
                            layout_merge_bboxes_mode={11: "small"},
                            precision = "fp32",
                            layout_unclip_ratio	=[1.0,1.2],
                            model_dir="models/PP-DocLayout-L"
                            )
print("\n\n\n\n\n")

def extract_text_from_bbox(image, bbox_list, page):
    """
    bbox_list is a 2d list of 4 coord lists in format [[x1,y1,x2,y2], ...]
    """
    height = []
    horizontal_list = []
    for bbox in bbox_list:
        x1, y1, x2, y2 = map(int, bbox)
        horizontal_list.append([x1, x2, y1, y2])
        height.append(abs(y1 - y2))

    if not horizontal_list:
        return ""

    results = reader.recognize(image, horizontal_list=horizontal_list, free_list=[], detail=0)
    if results:
        outline = []
        for text, h in zip(results, height):
            outline.append({
                "level": h,
                "text": text,
                "page": page
            })
        return {"outline": outline}
    else:
        return ""

def extract_coordinates(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return [box["coordinate"] for box in data.get("boxes", [])]

def process_outline(outline):
    if not outline:
        return {}

    # Find the title (text with the highest level on page 0)
    title_entry = max((item for item in outline if item['page'] == 0), key=lambda x: x['level'], default=None)
    title = title_entry['text'] if title_entry else "Untitled"

    # Create a copy of the outline to modify for level calculation
    outline_for_levels = list(outline)
    if title_entry:
        outline_for_levels.remove(title_entry)

    # Separate levels and find min/max from the modified list
    levels = [item['level'] for item in outline_for_levels]
    if not levels:
        if title_entry:
            outline.remove(title_entry)
        return {"title": title, "outline": outline if title_entry else []}

    min_level = min(levels)
    max_level = max(levels)
    level_range = max_level - min_level if max_level > min_level else 1

    # Define the 3 sections for H1, H2, H3
    h1_threshold = min_level + (level_range / 2)
    h2_threshold = min_level + (level_range / 4)

    # Remove title from the original outline before assigning H1/H2/H3
    if title_entry:
        outline.remove(title_entry)

    # Assign H1, H2, H3 based on level
    for item in outline:
        if item['level'] >= h1_threshold:
            item['level'] = 'H1'
        elif item['level'] >= h2_threshold:
            item['level'] = 'H2'
        else:
            item['level'] = 'H3'

    return {"title": title, "outline": outline}


def main(pdf_folder_path, output_jsons_dir):

    pdf_paths  = glob.glob(os.path.join(pdf_folder_path, '*.pdf'))

    os.makedirs(output_jsons_dir, exist_ok=True)

    
    
    print(f"Processing PDFs: {pdf_paths}")
    output = model.predict(pdf_paths, batch_size=16)
    


    pdf_outlines = {}
    for res in output:

        pdf_path = res['input_path']
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]

        coords = [box['coordinate'] for box in res.json['res']['boxes']]
        page = res['page_index']

        text_data = extract_text_from_bbox(res['input_img'], coords, page)

        if pdf_path not in pdf_outlines:
            pdf_outlines[pdf_path] = []

        if text_data and 'outline' in text_data:
            pdf_outlines[pdf_path].extend(text_data['outline'])

    for pdf_path, outline in pdf_outlines.items():
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_json_path = os.path.join(output_jsons_dir, f"{pdf_name}_outline.json")
        
        processed_outline = process_outline(outline)

        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(processed_outline, f, ensure_ascii=False, indent=4)




if __name__ == "__main__":
    start_time = time.time()
    main("input", "output")
    end_time = time.time()
    print(f"titles processed in {end_time - start_time:.2f} seconds")





