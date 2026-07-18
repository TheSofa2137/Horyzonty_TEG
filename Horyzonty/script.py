import xml.etree.ElementTree as ET
import mwparserfromhell
import os


def extract_cities(xml_path, cities_to_find, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Starting XML scan: {xml_path}...")

    # Open regular XML file instead of bz2
    with open(xml_path, "rb") as f:
        # Iterate through XML element by element
        context = ET.iterparse(f, events=("end",))

        for event, elem in context:
            if elem.tag.endswith("page"):
                title_elem = elem.find("{*}title")
                if title_elem is not None:
                    title = title_elem.text

                    if title in cities_to_find:
                        print(f"City found: {title}")
                        revision = elem.find("{*}revision")
                        if revision is not None:
                            text_elem = revision.find("{*}text")
                            if text_elem is not None and text_elem.text:
                                # Parse Wiki content
                                wikicode = mwparserfromhell.parse(text_elem.text)
                                clean_text = wikicode.strip_code()

                                # Save to .txt file
                                file_path = os.path.join(output_dir, f"{title.replace(' ', '_')}.txt")
                                with open(file_path, "w", encoding="utf-8") as out_f:
                                    out_f.write(clean_text)
                                print(f"Saved to: {file_path}")

                # Clear element from RAM
                elem.clear()


# --- CONFIGURATION ---
BASE_DIR = r"/Users/natalia.nazarczuk/PycharmProjects/Horyzonty"
# Removed .bz2 extension based on folder scan
input_file = os.path.join(BASE_DIR, "data", "unprocessed", "enwikivoyage-20251001-pages-articles-multistream.xml")
cities = ["Lisbon", "Porto", "Algarve"]
output_folder = os.path.join(BASE_DIR, "data", "processed")

if not os.path.exists(input_file):
    print(f"File not found: {input_file}")
else:
    extract_cities(input_file, cities, output_folder)