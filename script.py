import xml.etree.ElementTree as ET
import mwparserfromhell
import os


def extract_cities(xml_path, cities_to_find, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Rozpoczynam skanowanie bazy XML: {xml_path}...")

    # Otwieramy zwykły plik XML zamiast bz2
    with open(xml_path, "rb") as f:
        # Iterujemy przez XML element po elemencie
        context = ET.iterparse(f, events=("end",))

        for event, elem in context:
            if elem.tag.endswith("page"):
                title_elem = elem.find("{*}title")
                if title_elem is not None:
                    title = title_elem.text

                    if title in cities_to_find:
                        print(f"Znaleziono miasto: {title}")
                        revision = elem.find("{*}revision")
                        if revision is not None:
                            text_elem = revision.find("{*}text")
                            if text_elem is not None and text_elem.text:
                                # Parsowanie treści Wiki
                                wikicode = mwparserfromhell.parse(text_elem.text)
                                clean_text = wikicode.strip_code()

                                # Zapis do pliku .txt
                                file_path = os.path.join(output_dir, f"{title.replace(' ', '_')}.txt")
                                with open(file_path, "w", encoding="utf-8") as out_f:
                                    out_f.write(clean_text)
                                print(f"Zapisano do: {file_path}")

                # Czyścimy element z pamięci RAM
                elem.clear()


# --- KONFIGURACJA ---
BASE_DIR = r"C:\Users\zuzan\Desktop\Horyzonty"
# Usunięto końcówkę .bz2 zgodnie z Twoim skanem folderu
input_file = os.path.join(BASE_DIR, "data", "unprocessed", "enwikivoyage-20251001-pages-articles-multistream.xml")
cities = ["Lisbon", "Porto", "Algarve"]
output_folder = os.path.join(BASE_DIR, "data", "processed")

if not os.path.exists(input_file):
    print(f"brak: {input_file}")
else:
    extract_cities(input_file, cities, output_folder)