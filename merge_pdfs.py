import pikepdf
from pathlib import Path

pdf_directories = [
    "./edpb_documents",
    "./oss_documents"
]

MAX_MB = 50
MAX_BYTES = MAX_MB * 1024 * 1024

def get_pdf_sizes(pdf_files):
    """Gibt ein Dictionary mit Pfad -> Dateigröße in Bytes zurück."""
    return {str(pdf): pdf.stat().st_size for pdf in pdf_files}

def save_merged_pdf(pdf_list, output_path):
    with pikepdf.Pdf.new() as merged:
        for pdf_path in pdf_list:
            with pikepdf.open(pdf_path) as src:
                merged.pages.extend(src.pages)
        merged.save(output_path)
    print(f"PDF gespeichert: {output_path} ({output_path.stat().st_size / 1024 / 1024:.2f} MB)")

def merge_pdfs_by_size(directory):
    pdf_dir = Path(directory)
    if not pdf_dir.is_dir():
        print(f"Übersprungen: {directory} ist kein Verzeichnis.")
        return

    pdf_files = sorted([p for p in pdf_dir.glob("*.pdf") if p.is_file()])
    if not pdf_files:
        print(f"Keine PDFs gefunden in {directory}.")
        return

    print(f"\nVerarbeite Verzeichnis: {pdf_dir} ({len(pdf_files)} PDF-Dateien)")
    size_cache = get_pdf_sizes(pdf_files)
    total_size = sum(size_cache.values()) / 1024 / 1024
    print(f"Gesamtgröße: {total_size:.2f} MB")

    group = []
    current_size = 0
    group_index = 1
    file_index = 0
    output_dir = pdf_dir / "merged"
    output_dir.mkdir(exist_ok=True)

    for pdf in pdf_files:
        file_index += 1
        pdf_path = str(pdf)
        pdf_size = size_cache[pdf_path]
        pdf_size_mb = pdf_size / 1024 / 1024

        print(f"{file_index}/{len(pdf_files)}: {pdf.name} ({pdf_size_mb:.2f} MB)")

        if current_size + pdf_size <= MAX_BYTES:
            group.append(pdf_path)
            current_size += pdf_size
            print(f"  Hinzugefügt zur Gruppe (aktuelle Größe: {current_size / 1024 / 1024:.2f} MB)")
        else:
            if group:
                output_file = output_dir / f"{pdf_dir.name}_part{group_index}.pdf"
                print(f"  Gruppengröße erreicht. Speichere {output_file.name} ...")
                save_merged_pdf(group, output_file)
                group_index += 1
            group = [pdf_path]
            current_size = pdf_size
            print(f"  Neue Gruppe gestartet mit: {pdf.name}")

    if group:
        output_file = output_dir / f"{pdf_dir.name}_part{group_index}.pdf"
        print(f"Letzte Gruppe speichern: {output_file.name} ...")
        save_merged_pdf(group, output_file)

    print(f"Fertig mit {pdf_dir.name}: {group_index} Datei(en) erzeugt\n")

for folder in pdf_directories:
    merge_pdfs_by_size(folder)
