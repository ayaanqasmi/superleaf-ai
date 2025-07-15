import argparse
from grobid_client.grobid_client import GrobidClient
import os
import shutil

def clear_directory(directory_path):
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)

def generate_xml(input_file):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    configPath = os.path.join(script_dir, "config.json")
    client = GrobidClient(config_path=configPath)
    
    input_dir = os.path.dirname(input_file)
    output_dir = os.path.join(base_dir, "processed")

    # Clear the output directory before processing
    if os.path.exists(output_dir):
        clear_directory(output_dir)

    # Clear the input directory except for the specified file
    file_to_keep = os.path.basename(input_file)
    for filename in os.listdir(input_dir):
        if filename != file_to_keep:
            file_path = os.path.join(input_dir, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)

    print(f"Processing single file: {input_file}")

    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    client.process("processFulltextDocument", input_dir, output=output_dir, n=20)

    print(f"Output should be in: {output_dir}")
    print("done processing")
    return output_dir


