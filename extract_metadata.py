import xmltodict
import json

# Load the GROBID TEI XML file
grobidOutputXmlPath=r"C:\Users\ayaan\projects\current\superleaf\ai\processed\RIS-Empowered_Ambient_Backscatter_Communication_Systems[1].grobid.tei.xml"
with open(grobidOutputXmlPath, "r", encoding="utf-8") as f:
    xml_content = f.read()

# Convert XML to Python dict
data_dict = xmltodict.parse(xml_content)

# Convert dict to JSON
json_data = json.dumps(data_dict, indent=2)

# Optionally, write to file
with open("grobid_output.json", "w", encoding="utf-8") as f:
    f.write(json_data)

print("Conversion complete.")
