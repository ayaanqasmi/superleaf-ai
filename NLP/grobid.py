from grobid_client.grobid_client import GrobidClient
import os

configPath = r"C:\Users\ayaan\projects\current\superleaf\ai\NLP\config.json"
client = GrobidClient(config_path=configPath)
input_dir = r"C:\Users\ayaan\projects\current\superleaf\ai\pdf_input"
output_dir = r"C:\Users\ayaan\projects\current\superleaf\ai\processed"

# Create the output directory if it doesn't exist
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

client.process("processFulltextDocument", input_dir, output=output_dir, n=20)

print(f"Output should be in: {output_dir}")

print("done processinh")