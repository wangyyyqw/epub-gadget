import argparse
import sys
import os
import json
import zipfile
import shutil
import tempfile
import uuid
import re
from xml.etree import ElementTree as ET
from PIL import Image
from core.plugin_base import BasePlugin

NAMESPACES = {
    'opf': 'http://www.idpf.org/2007/opf',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'container': 'urn:oasis:names:tc:opendocument:xmlns:container',
}

for prefix, uri in NAMESPACES.items():
    ET.register_namespace(prefix, uri)

NSMAP = {
    'dc': 'http://purl.org/dc/elements/1.1/',
    'opf': 'http://www.idpf.org/2007/opf',
}


class MetadataEditPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "metadata_edit"

    @property
    def description(self) -> str:
        return "Edit EPUB metadata: title, author, cover, etc."

    def register_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument("--action", choices=["read", "write"], required=True, help="Action: read or write metadata")
        parser.add_argument("--epub", required=True, help="Path to EPUB file")
        parser.add_argument("--output", help="Output path for write action")
        parser.add_argument("--metadata", help="JSON string of metadata fields")
        parser.add_argument("--cover", help="Path to cover image")
        parser.add_argument("--remove-cover", action="store_true", help="Remove existing cover")

    def run(self, args: argparse.Namespace):
        if not os.path.exists(args.epub):
            print(f"ERROR: EPUB file not found: {args.epub}", file=sys.stderr)
            sys.exit(1)

        if args.action == "read":
            self._read_metadata(args.epub)
        elif args.action == "write":
            if not args.output:
                print("ERROR: --output is required for write action", file=sys.stderr)
                sys.exit(1)
            if not args.metadata:
                print("ERROR: --metadata is required for write action", file=sys.stderr)
                sys.exit(1)
            metadata = json.loads(args.metadata)
            self._write_metadata(args.epub, args.output, metadata, args.cover, args.remove_cover)

    def _read_metadata(self, epub_path: str):
        metadata = {
            "title": "",
            "author": "",
            "language": "zh-CN",
            "publisher": "",
            "description": "",
            "identifier": "",
            "rights": "",
            "cover": ""
        }

        try:
            with zipfile.ZipFile(epub_path, 'r') as zf:
                container_xml = zf.read('META-INF/container.xml')
                root = ET.fromstring(container_xml)
                rootfile = root.find('.//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile')
                if rootfile is not None:
                    opf_path = rootfile.get('full-path')
                    opf_content = zf.read(opf_path)
                    opf_root = ET.fromstring(opf_content)

                    def get_text(elem, tag):
                        found = opf_root.find(f'.//{{{NAMESPACES["dc"]}}}{tag}')
                        return found.text if found is not None and found.text else ""

                    metadata["title"] = get_text(opf_root, "title")
                    metadata["author"] = get_text(opf_root, "creator")
                    metadata["language"] = get_text(opf_root, "language")
                    metadata["publisher"] = get_text(opf_root, "publisher")
                    metadata["description"] = get_text(opf_root, "description")
                    metadata["identifier"] = get_text(opf_root, "identifier")
                    metadata["rights"] = get_text(opf_root, "rights")

                    opf_dir = os.path.dirname(opf_path)

                    meta_cover = opf_root.find('.//opf:meta[@name="cover"]', NSMAP)
                    if meta_cover is not None:
                        cover_id = meta_cover.get('content')
                        cover_item = opf_root.find(f'.//opf:item[@id="{cover_id}"]', NSMAP)
                        if cover_item is not None:
                            cover_href = cover_item.get('href')
                            cover_full_path = os.path.join(opf_dir, cover_href) if opf_dir else cover_href
                            try:
                                cover_data = zf.read(cover_full_path)
                                import base64
                                metadata["cover"] = f"data:image/{cover_full_path.split('.')[-1]};base64,{base64.b64encode(cover_data).decode()}"
                            except:
                                pass

                    if not metadata["cover"]:
                        for item in opf_root.findall('.//opf:item', NSMAP):
                            href = item.get('href', '').lower()
                            if 'cover' in href and any(href.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                                cover_full_path = os.path.join(opf_dir, item.get('href')) if opf_dir else item.get('href')
                                try:
                                    cover_data = zf.read(cover_full_path)
                                    import base64
                                    metadata["cover"] = f"data:image/{href.split('.')[-1]};base64,{base64.b64encode(cover_data).decode()}"
                                    break
                                except:
                                    pass

        except Exception as e:
            print(f"ERROR: Failed to read metadata: {e}", file=sys.stderr)

        print(json.dumps(metadata, ensure_ascii=False))

    def _write_metadata(self, epub_path: str, output_path: str, metadata: dict, cover_path: str = None, remove_cover: bool = False):
        tmp_dir = tempfile.mkdtemp()
        tmp_epub = os.path.join(tmp_dir, 'output.epub')

        try:
            with zipfile.ZipFile(epub_path, 'r') as zf:
                zf.extractall(tmp_dir)

            container_xml = os.path.join(tmp_dir, 'META-INF', 'container.xml')
            root = ET.parse(container_xml).getroot()
            rootfile = root.find('.//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile')
            if rootfile is None:
                print("ERROR: Invalid EPUB: container.xml missing rootfile", file=sys.stderr)
                sys.exit(1)

            opf_path = os.path.join(tmp_dir, rootfile.get('full-path'))
            opf_dir = os.path.dirname(opf_path)

            tree = ET.parse(opf_path)
            opf_root = tree.getroot()

            dc_tags = ['title', 'creator', 'language', 'publisher', 'description', 'identifier', 'rights']
            for tag in dc_tags:
                uri = f'{{{NAMESPACES["dc"]}}}{tag}'
                existing = opf_root.find(f'.//{uri}')
                if existing is None:
                    existing = ET.SubElement(opf_root.find('.//{http://www.idpf.org/2007/opf}metadata'), uri)
                if tag in metadata:
                    existing.text = metadata[tag]

            if cover_path and os.path.exists(cover_path):
                self._update_cover(opf_root, opf_path, opf_dir, cover_path)
            elif remove_cover:
                self._remove_cover(opf_root, opf_path, opf_dir)

            tree.write(opf_path, encoding='utf-8', xml_declaration=True)

            self._repack_epub(tmp_dir, tmp_epub)
            shutil.copy2(tmp_epub, output_path)

            print(f"SUCCESS: Metadata written to {output_path}", file=sys.stderr)

        except Exception as e:
            print(f"ERROR: Failed to write metadata: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            sys.exit(1)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def _update_cover(self, opf_root, opf_path, opf_dir, cover_path):
        img = Image.open(cover_path)
        ext = img.format.lower()
        if ext == 'jpeg':
            ext = 'jpg'
        new_cover_name = f'cover.{ext}'
        images_dir = os.path.join(opf_dir, 'Images')
        os.makedirs(images_dir, exist_ok=True)
        dest_cover = os.path.join(images_dir, new_cover_name)
        shutil.copy2(cover_path, dest_cover)

        mime_types = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 'webp': 'image/webp', 'gif': 'image/gif'}
        mime = mime_types.get(ext, 'image/jpeg')

        manifest = opf_root.find('.//{http://www.idpf.org/2007/opf}manifest')
        cover_id = 'cover-image'

        for item in manifest.findall('{http://www.idpf.org/2007/opf}item'):
            if item.get('id') == cover_id:
                manifest.remove(item)
            href = item.get('href', '')
            if 'cover' in href.lower() and any(href.endswith(e) for e in ['.jpg', '.jpeg', '.png', '.webp']):
                manifest.remove(item)

        cover_item = ET.SubElement(manifest, '{http://www.idpf.org/2007/opf}item')
        cover_item.set('id', cover_id)
        cover_item.set('href', f'Images/{new_cover_name}')
        cover_item.set('media-type', mime)
        if ext in ('jpg', 'jpeg'):
            cover_item.set('properties', 'cover-image')

        spine = opf_root.find('.//{http://www.idpf.org/2007/opf}spine')
        if spine is not None:
            spine.set('cover', cover_id)

        metadata = opf_root.find('.//{http://www.idpf.org/2007/opf}metadata')
        for meta in metadata.findall('{http://www.idpf.org/2007/opf}meta'):
            if meta.get('name') == 'cover':
                metadata.remove(meta)

        meta = ET.SubElement(metadata, '{http://www.idpf.org/2007/opf}meta')
        meta.set('name', 'cover')
        meta.set('content', cover_id)

    def _remove_cover(self, opf_root, opf_path, opf_dir):
        manifest = opf_root.find('.//{http://www.idpf.org/2007/opf}manifest')
        if manifest is not None:
            items_to_remove = []
            for item in manifest.findall('{http://www.idpf.org/2007/opf}item'):
                href = item.get('href', '')
                item_id = item.get('id', '')
                if 'cover' in href.lower() or item_id == 'cover-image':
                    items_to_remove.append(item)
            for item in items_to_remove:
                manifest.remove(item)

        spine = opf_root.find('.//{http://www.idpf.org/2007/opf}spine')
        if spine is not None and spine.get('cover'):
            del spine.attrib['cover']

        metadata = opf_root.find('.//{http://www.idpf.org/2007/opf}metadata')
        if metadata is not None:
            for meta in metadata.findall('{http://www.idpf.org/2007/opf}meta'):
                if meta.get('name') == 'cover':
                    metadata.remove(meta)

    def _repack_epub(self, source_dir: str, output_epub: str):
        with zipfile.ZipFile(output_epub, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_dir)
                    if arcname == 'mimetype':
                        zf.write(file_path, arcname, compress_type=zipfile.ZIP_STORED)
                    else:
                        zf.write(file_path, arcname)


if __name__ == "__main__":
    plugin = MetadataEditPlugin()
    parser = argparse.ArgumentParser(description=plugin.description)
    plugin.register_arguments(parser)
    args = parser.parse_args()
    plugin.run(args)