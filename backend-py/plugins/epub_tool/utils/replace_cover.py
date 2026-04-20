import os
import sys
import shutil
import tempfile
import zipfile
import argparse
from PIL import Image
from xml.etree import ElementTree as ET

NAMESPACES = {
    'opf': 'http://www.idpf.org/2007/opf',
    'dc': 'http://purl.org/dc/elements/1.1/',
}

for prefix, uri in NAMESPACES.items():
    ET.register_namespace(prefix, uri)


def _repack_epub(source_dir: str, output_epub: str):
    with zipfile.ZipFile(output_epub, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                if arcname == 'mimetype':
                    zf.write(file_path, arcname, compress_type=zipfile.ZIP_STORED)
                else:
                    zf.write(file_path, arcname)


def run(input_path: str, output_dir: str, cover_path: str) -> int:
    """
    Replace the cover image of an EPUB file.
    Returns 0 on success, non-zero on failure.
    """
    tmp_dir = tempfile.mkdtemp()
    try:
        with zipfile.ZipFile(input_path, 'r') as zf:
            zf.extractall(tmp_dir)

        container_xml = os.path.join(tmp_dir, 'META-INF', 'container.xml')
        root = ET.parse(container_xml).getroot()
        rootfile = root.find('.//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile')
        if rootfile is None:
            print(f"ERROR: Invalid EPUB: container.xml missing rootfile", file=sys.stderr)
            return 1

        opf_path = os.path.join(tmp_dir, rootfile.get('full-path'))
        opf_dir = os.path.dirname(opf_path)

        tree = ET.parse(opf_path)
        opf_root = tree.getroot()

        opf_ns = NAMESPACES["opf"]

        # Determine new cover extension
        img = Image.open(cover_path)
        ext = img.format.lower()
        if ext == 'jpeg':
            ext = 'jpg'
        new_cover_name = f'cover.{ext}'

        # Copy new cover to Images/
        images_dir = os.path.join(opf_dir, 'Images')
        os.makedirs(images_dir, exist_ok=True)
        dest_cover = os.path.join(images_dir, new_cover_name)
        shutil.copy2(cover_path, dest_cover)

        mime_types = {
            'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
            'png': 'image/png', 'webp': 'image/webp', 'gif': 'image/gif'
        }
        mime = mime_types.get(ext, 'image/jpeg')

        manifest = opf_root.find(f'.//{{{opf_ns}}}manifest')
        if manifest is None:
            print("ERROR: manifest not found in OPF", file=sys.stderr)
            return 1

        # Remove old cover items from manifest
        old_cover_ids = []
        for item in list(manifest.findall(f'{{{opf_ns}}}item')):
            item_id = item.get('id', '')
            href = item.get('href', '')
            if item_id == 'cover-image' or 'cover' in href.lower():
                old_cover_ids.append(href)
                manifest.remove(item)

        # Remove old cover files from filesystem
        for old_href in old_cover_ids:
            old_path = os.path.join(tmp_dir, old_href)
            if os.path.exists(old_path):
                os.remove(old_path)

        # Add new cover item
        cover_item = ET.SubElement(manifest, f'{{{opf_ns}}}item')
        cover_item.set('id', 'cover-image')
        cover_item.set('href', f'Images/{new_cover_name}')
        cover_item.set('media-type', mime)
        if ext in ('jpg', 'jpeg'):
            cover_item.set('properties', 'cover-image')

        # Update spine
        spine = opf_root.find(f'.//{{{opf_ns}}}spine')
        if spine is not None:
            spine.set('cover', 'cover-image')

        # Update metadata
        metadata = opf_root.find(f'.//{{{opf_ns}}}metadata')
        if metadata is not None:
            # Remove old cover meta
            for meta in list(metadata.findall(f'{{{opf_ns}}}meta')):
                if meta.get('name') == 'cover':
                    metadata.remove(meta)
            # Add new cover meta
            meta = ET.SubElement(metadata, f'{{{opf_ns}}}meta')
            meta.set('name', 'cover')
            meta.set('content', 'cover-image')

        # Write updated OPF
        tree.write(opf_path, encoding='utf-8', xml_declaration=True)

        # Repack EPUB
        filename = os.path.basename(input_path)
        stem = os.path.splitext(filename)[0]
        output_epub = os.path.join(output_dir, f"{stem}_cover.epub")
        _repack_epub(tmp_dir, output_epub)

        print(f"Cover replaced: {output_epub}", file=sys.stderr)
        return 0

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Replace EPUB cover image')
    parser.add_argument('--input-path', required=True, help='Input EPUB file')
    parser.add_argument('--output-dir', required=True, help='Output directory')
    parser.add_argument('--cover-path', required=True, help='New cover image path')
    args = parser.parse_args()

    result = run(args.input_path, args.output_dir, args.cover_path)
    sys.exit(result)
