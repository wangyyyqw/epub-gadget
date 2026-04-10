import argparse
import sys
import os
import json
import zipfile
import shutil
import tempfile
import uuid
import re
import base64
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
            "subtitle": "",
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

                    dc_ns = NAMESPACES["dc"]
                    opf_ns = NAMESPACES["opf"]

                    def get_dc_text(tag):
                        found = opf_root.find(f'.//{{{dc_ns}}}{tag}')
                        return found.text if found is not None and found.text else ""

                    all_titles = opf_root.findall(f'.//{{{dc_ns}}}title')
                    for title_elem in all_titles:
                        title_text = title_elem.text or ""
                        title_id = title_elem.get('id', '')

                        title_type = None
                        if title_id:
                            refine_meta = opf_root.find(f'.//{{{opf_ns}}}meta[@refines="#{title_id}"][@property="title-type"]')
                            if refine_meta is not None:
                                title_type = refine_meta.text

                        if title_type == 'main':
                            metadata["title"] = title_text
                        elif title_type == 'subtitle':
                            metadata["subtitle"] = title_text
                        elif not metadata["title"] and title_text:
                            metadata["title"] = title_text

                    metadata["author"] = get_dc_text("creator")
                    metadata["language"] = get_dc_text("language") or "zh-CN"
                    metadata["publisher"] = get_dc_text("publisher")
                    metadata["description"] = get_dc_text("description")
                    metadata["identifier"] = get_dc_text("identifier")
                    metadata["rights"] = get_dc_text("rights")

                    opf_dir = os.path.dirname(opf_path)

                    meta_cover = opf_root.find(f'.//{{{opf_ns}}}meta[@name="cover"]')
                    if meta_cover is not None:
                        cover_id = meta_cover.get('content')
                        cover_item = opf_root.find(f'.//{{{opf_ns}}}item[@id="{cover_id}"]')
                        if cover_item is not None:
                            cover_href = cover_item.get('href')
                            cover_full_path = os.path.join(opf_dir, cover_href) if opf_dir else cover_href
                            try:
                                cover_data = zf.read(cover_full_path)
                                ext = cover_full_path.split('.')[-1].lower()
                                if ext == 'jpeg':
                                    ext = 'jpg'
                                metadata["cover"] = f"data:image/{ext};base64,{base64.b64encode(cover_data).decode()}"
                            except:
                                pass

                    if not metadata["cover"]:
                        manifest = opf_root.find(f'.//{{{opf_ns}}}manifest')
                        if manifest is not None:
                            for item in manifest.findall(f'{{{opf_ns}}}item'):
                                href = item.get('href', '').lower()
                                if 'cover' in href and any(href.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                                    cover_full_path = os.path.join(opf_dir, item.get('href')) if opf_dir else item.get('href')
                                    try:
                                        cover_data = zf.read(cover_full_path)
                                        ext = href.split('.')[-1].lower()
                                        if ext == 'jpeg':
                                            ext = 'jpg'
                                        metadata["cover"] = f"data:image/{ext};base64,{base64.b64encode(cover_data).decode()}"
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

            dc_ns = NAMESPACES["dc"]
            opf_ns = NAMESPACES["opf"]
            metadata_elem = opf_root.find(f'.//{{{opf_ns}}}metadata')

            def set_dc_element(tag, text):
                uri = f'{{{dc_ns}}}{tag}'
                existing = opf_root.find(f'.//{uri}')
                if existing is None:
                    existing = ET.SubElement(metadata_elem, uri)
                existing.text = text

            def get_or_create_dc_element(tag):
                uri = f'{{{dc_ns}}}{tag}'
                existing = opf_root.find(f'.//{uri}')
                if existing is None:
                    existing = ET.SubElement(metadata_elem, uri)
                return existing

            def remove_refines_meta(opf_root, element_id, property_name):
                metadata_elem = opf_root.find(f'.//{{{opf_ns}}}metadata')
                if metadata_elem is not None:
                    to_remove = []
                    for meta in metadata_elem.findall(f'{{{opf_ns}}}meta'):
                        if meta.get('refines') == f'#{element_id}' and meta.get('property') == property_name:
                            to_remove.append(meta)
                    for meta in to_remove:
                        metadata_elem.remove(meta)

            existing_title = opf_root.find(f'.//{{{dc_ns}}}title')
            if existing_title is not None:
                title_id = existing_title.get('id')
                if title_id:
                    remove_refines_meta(opf_root, title_id, 'title-type')
                existing_title.text = metadata.get('title', '')

                if metadata.get('subtitle'):
                    subtitle_id = 'subtitle-id'
                    existing_subtitle = opf_root.find(f'.//{{{dc_ns}}}title[@id="{subtitle_id}"]')
                    if existing_subtitle is None:
                        existing_subtitle = ET.SubElement(metadata_elem, f'{{{dc_ns}}}title')
                        existing_subtitle.set('id', subtitle_id)
                    existing_subtitle.text = metadata.get('subtitle', '')

                    subtitle_meta = ET.SubElement(metadata_elem, f'{{{opf_ns}}}meta')
                    subtitle_meta.set('refines', f'#{subtitle_id}')
                    subtitle_meta.set('property', 'title-type')
                    subtitle_meta.text = 'subtitle'

                    if not existing_title.get('id'):
                        existing_title.set('id', 'main-title-id')
                    title_meta = ET.SubElement(metadata_elem, f'{{{opf_ns}}}meta')
                    title_meta.set('refines', '#' + existing_title.get('id'))
                    title_meta.set('property', 'title-type')
                    title_meta.text = 'main'
            else:
                set_dc_element('title', metadata.get('title', ''))
                if metadata.get('subtitle'):
                    set_dc_element('title', metadata.get('subtitle', ''))

            simple_fields = {
                'creator': metadata.get('author', ''),
                'language': metadata.get('language', 'zh-CN'),
                'publisher': metadata.get('publisher', ''),
                'description': metadata.get('description', ''),
                'identifier': metadata.get('identifier', ''),
                'rights': metadata.get('rights', ''),
            }
            for tag, value in simple_fields.items():
                if tag != 'title':
                    set_dc_element(tag, value)

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

        manifest = opf_root.find(f'.//{{{NAMESPACES["opf"]}}}manifest')
        cover_id = 'cover-image'

        for item in manifest.findall(f'{{{NAMESPACES["opf"]}}}item'):
            if item.get('id') == cover_id:
                manifest.remove(item)
            href = item.get('href', '')
            if 'cover' in href.lower() and any(href.endswith(e) for e in ['.jpg', '.jpeg', '.png', '.webp']):
                manifest.remove(item)

        cover_item = ET.SubElement(manifest, f'{{{NAMESPACES["opf"]}}}item')
        cover_item.set('id', cover_id)
        cover_item.set('href', f'Images/{new_cover_name}')
        cover_item.set('media-type', mime)
        if ext in ('jpg', 'jpeg'):
            cover_item.set('properties', 'cover-image')

        spine = opf_root.find(f'.//{{{NAMESPACES["opf"]}}}spine')
        if spine is not None:
            spine.set('cover', cover_id)

        metadata = opf_root.find(f'.//{{{NAMESPACES["opf"]}}}metadata')
        for meta in metadata.findall(f'{{{NAMESPACES["opf"]}}}meta'):
            if meta.get('name') == 'cover':
                metadata.remove(meta)

        meta = ET.SubElement(metadata, f'{{{NAMESPACES["opf"]}}}meta')
        meta.set('name', 'cover')
        meta.set('content', cover_id)

    def _remove_cover(self, opf_root, opf_path, opf_dir):
        manifest = opf_root.find(f'.//{{{NAMESPACES["opf"]}}}manifest')
        if manifest is not None:
            items_to_remove = []
            for item in manifest.findall(f'{{{NAMESPACES["opf"]}}}item'):
                href = item.get('href', '')
                item_id = item.get('id', '')
                if 'cover' in href.lower() or item_id == 'cover-image':
                    items_to_remove.append(item)
            for item in items_to_remove:
                manifest.remove(item)

        spine = opf_root.find(f'.//{{{NAMESPACES["opf"]}}}spine')
        if spine is not None and spine.get('cover'):
            del spine.attrib['cover']

        metadata = opf_root.find(f'.//{{{NAMESPACES["opf"]}}}metadata')
        if metadata is not None:
            for meta in metadata.findall(f'{{{NAMESPACES["opf"]}}}meta'):
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