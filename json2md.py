import json
import io
import copy
import os
import argparse
from PIL import Image
from pdf2image import convert_from_path
from mdutils.mdutils import MdUtils
from mdutils import Html

import pdb 

def parse_args():
    parser = argparse.ArgumentParser(description='parameters')
    parser.add_argument('--data_path', dest='data_path',
                        default='', type=str) 
    parser.add_argument('--output_path', dest='output_path',
                        default='', type=str) 
    parser.add_argument('--tmp_path', dest='tmp_path',
                        default='', type=str) 
    args = parser.parse_args()
    return args

def convert_to_target_format(data, md_filepath, tmp_path):

    mdFile = MdUtils(file_name=md_filepath)
    for i in data:
        if i == 'title':
            mdFile.new_header(level=1, title=data["title"])  # style is set 'atx' format by default.
        
        if "_parse" in i:
            for entry in data.get(i, {}).get("abstract", []):
                text = entry.get("text", "")
                mdFile.new_paragraph(text) 
            
            for entry in data.get(i, {}).get("body_text", []):
                text = entry.get("text", "")
                mdFile.new_paragraph(text) 

    for i in data["latex_parse"]["ref_entries"]:
        if data["latex_parse"]["ref_entries"][i]["type_str"] == "figure":
            temdir_path = tmp_path + '/latex' 
            paper_repath = data["latex_parse"]["ref_entries"][i]["uris"]
            image_path = os.path.join(temdir_path, data['paper_id'], ''.join(paper_repath))
            if image_path.lower().endswith('.pdf'):
                images = convert_from_path(image_path)
                image_path = os.path.splitext(image_path)[0] + ".png"
                images[0].save(image_path, 'PNG')

            if not os.path.isdir(image_path):
                image_text = ""
                mdFile.insert_code("mdFile.new_line(mdFile.new_inline_image(text='{}', path='{}'))".format(image_text, image_path))
                mdFile.new_line(mdFile.new_inline_image(text=image_text, path=image_path))

    mdFile.create_md_file()


if __name__ == '__main__':
    args = parse_args() 
    data_name = args.data_path.split('/')[-1] 

    convert_md_filepath = os.path.join(args.output_path, data_name)  

    json_path = args.data_path 
    with open(json_path, 'r') as file:
        data = json.load(file)
        convert_to_target_format(data, data_name[:-9], args.tmp_path)
 
