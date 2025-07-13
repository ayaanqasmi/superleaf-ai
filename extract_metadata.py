import xml.etree.ElementTree as ET
import json

def get_text(element, path, ns, default=None):
    """Safely get text from an element."""
    found_element = element.find(path, ns)
    if found_element is not None and found_element.text:
        return found_element.text.strip()
    return default

def get_attribute(element, path, attribute, ns, default=None):
    """Safely get an attribute from an element."""
    found_element = element.find(path, ns)
    if found_element is not None and attribute in found_element.attrib:
        return found_element.attrib[attribute].strip()
    return default

def get_all_text(element, path, ns):
    """Safely get all text from multiple elements."""
    return [el.text.strip() for el in element.findall(path, ns) if el.text]

def get_author_details(author_element, ns):
    """Extracts details for a single author."""
    pers_name = author_element.find('tei:persName', ns)
    if pers_name is None:
        return None

    first_name = get_text(pers_name, 'tei:forename[@type="first"]', ns, "")
    middle_name = get_text(pers_name, 'tei:forename[@type="middle"]', ns, "")
    surname = get_text(pers_name, 'tei:surname', ns, "")

    # Construct full name
    full_name = f"{first_name} {middle_name} {surname}".replace("  ", " ").strip()

    email = get_text(author_element, 'tei:email', ns)
    orcid = get_text(author_element, 'tei:idno[@type="ORCID"]', ns)

    affiliation_element = author_element.find('tei:affiliation', ns)
    affiliation = None
    if affiliation_element is not None:
        org_names = get_all_text(affiliation_element, 'tei:orgName', ns)
        address_element = affiliation_element.find('tei:address', ns)
        if address_element is not None:
            settlement = get_text(address_element, 'tei:settlement', ns)
            country = get_text(address_element, 'tei:country', ns)
            org_names.extend([settlement, country])
        affiliation = ", ".join(filter(None, org_names))


    author_info = {'full_name': full_name}
    if email:
        author_info['email'] = email
    if orcid:
        author_info['orcid'] = orcid
    if affiliation:
        author_info['affiliation'] = affiliation

    return author_info

def main():
    # Define the namespace
    ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

    # Load and parse the XML file
    xml_path = r"C:\Users\ayaan\projects\current\superleaf\ai\processed\RIS-Empowered_Ambient_Backscatter_Communication_Systems[1].grobid.tei.xml"
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # --- Paper Details ---
    title = get_text(root, './/tei:titleStmt/tei:title', ns)
    publication_date_raw = get_attribute(root, './/tei:publicationStmt/tei:date[@type="published"]', 'when', ns)
    publication_date = publication_date_raw.split('-')[0] if publication_date_raw else None
    keywords = get_all_text(root, './/tei:profileDesc/tei:textClass/tei:keywords/tei:term', ns)
    doi = get_text(root, './/tei:fileDesc/tei:sourceDesc/tei:biblStruct/tei:idno[@type="DOI"]', ns)


    # --- Main Authors ---
    main_authors = []
    analytic = root.find('.//tei:sourceDesc/tei:biblStruct/tei:analytic', ns)
    if analytic:
        for author_element in analytic.findall('tei:author', ns):
            author_details = get_author_details(author_element, ns)
            if author_details:
                main_authors.append(author_details)


    # --- References ---
    references = []
    references_list = root.find('.//tei:back/tei:div[@type="references"]/tei:listBibl', ns)
    if references_list is not None:
        for bibl_struct in references_list.findall('tei:biblStruct', ns):
            ref_title = get_text(bibl_struct, './/tei:title[@level="a"]', ns) or \
                        get_text(bibl_struct, './/tei:title[@level="m"]', ns)

            ref_date_raw = get_attribute(bibl_struct, './/tei:date[@type="published"]', 'when', ns)
            ref_date = ref_date_raw.split('-')[0] if ref_date_raw else None
            
            ref_journal = get_text(bibl_struct, './/tei:title[@level="j"]', ns) or \
                          get_text(bibl_struct, './/tei:title[@level="m"]', ns)


            ref_authors = []
            for author_element in bibl_struct.findall('.//tei:author', ns):
                author_details = get_author_details(author_element, ns)
                if author_details:
                    ref_authors.append(author_details)

            reference_info = {}
            if ref_title:
                reference_info['title'] = ref_title
            if ref_authors:
                reference_info['authors'] = ref_authors
            if ref_date:
                reference_info['date'] = ref_date
            if ref_journal and ref_journal != ref_title:
                reference_info['journal'] = ref_journal

            if reference_info:
                references.append(reference_info)


    # --- Final JSON Structure ---
    metadata = {
        'paper_title': title,
        'doi': doi,
        'publication_date': publication_date,
        'keywords': keywords,
        'authors': main_authors,
        'references': references
    }

    # Write to JSON file
    with open("metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print("Metadata extraction complete. Output saved to metadata.json")

if __name__ == "__main__":
    main()