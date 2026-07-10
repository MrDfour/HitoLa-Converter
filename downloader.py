import os
import re
import time
import shutil
import zipfile
import json
import requests
from PIL import Image

class HitomiResolver:
    def __init__(self):
        self.gg_b = "1783659601/"  # default fallback
        self.cases_set = set()      # default fallback
        self.update_gg()

    def update_gg(self):
        url = "https://ltn.gold-usergeneratedcontent.net/gg.js"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://hitomi.la/"
        }
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                js_content = r.text
                
                # Parse gg.b
                b_match = re.search(r"b:\s*'([^']+)'", js_content)
                if b_match:
                    self.gg_b = b_match.group(1)
                
                # Parse case values
                cases = re.findall(r"case\s+(\d+):", js_content)
                self.cases_set = set(int(c) for c in cases)
            else:
                print(f"Warning: Failed to fetch gg.js (HTTP {r.status_code}). Using fallback.")
        except Exception as e:
            print(f"Warning: Error updating gg.js resolver: {e}. Using fallback.")

    def gg_m(self, g):
        return 0 if g in self.cases_set else 1

    def gg_s(self, h):
        match = re.search(r"(..)(.)$", h)
        if not match:
            return ""
        hex_str = match.group(2) + match.group(1)
        return str(int(hex_str, 16))

    def full_path_from_hash(self, hash_str):
        return self.gg_b + self.gg_s(hash_str) + "/" + hash_str

    def subdomain_from_url(self, url, base=None, dir_type=None):
        retval = ""
        if not base:
            if dir_type == "webp":
                retval = "w"
            elif dir_type == "avif":
                retval = "a"
        
        match = re.search(r"/([0-9a-f]{61})([0-9a-f]{2})([0-9a-f])", url)
        if not match:
            return retval
            
        g = int(match.group(3) + match.group(2), 16)
        if base:
            retval = chr(97 + self.gg_m(g)) + base
        else:
            retval = retval + str(1 + self.gg_m(g))
            
        return retval

    def url_from_url(self, url, base=None, dir_type=None):
        subdomain = self.subdomain_from_url(url, base, dir_type)
        pattern = r"\/\/..?\.(?:gold-usergeneratedcontent\.net|hitomi\.la)\/"
        replacement = f"//{subdomain}.gold-usergeneratedcontent.net/"
        return re.sub(pattern, replacement, url)

    def url_from_hash(self, image, dir_type="webp", ext="webp"):
        path_dir = "" if dir_type in ("webp", "avif") else f"{dir_type}/"
        full_path = self.full_path_from_hash(image["hash"])
        return f"https://a.gold-usergeneratedcontent.net/{path_dir}{full_path}.{ext}"

    def get_image_url(self, image, dir_type="webp", ext="webp", base=None):
        raw_url = self.url_from_hash(image, dir_type, ext)
        return self.url_from_url(raw_url, base, dir_type)

class HitomiDownloader:
    def __init__(self, url, output_dir, format_type="pdf", progress_callback=None, throttle_seconds=1.0):
        self.url = url.strip()
        self.output_dir = output_dir
        self.format_type = format_type.lower()
        self.progress_callback = progress_callback
        self.throttle_seconds = throttle_seconds
        self.resolver = None
        self.is_cancelled = False

    def update_progress(self, message, progress):
        if self.progress_callback:
            self.progress_callback(message, progress)

    def cancel(self):
        self.is_cancelled = True

    def sanitize_filename(self, filename):
        # Replace characters that are invalid in Windows filenames
        return re.sub(r'[\\/*?:"<>|]', "_", filename)

    def extract_gallery_id(self):
        if self.url.isdigit():
            return self.url
        
        match = re.search(r"(\d+)\.html", self.url)
        if match:
            return match.group(1)
        
        match = re.search(r"(\d+)$", self.url)
        if match:
            return match.group(1)
            
        raise ValueError("Could not extract a valid Gallery ID from the URL/input.")

    def get_alternative_urls(self, resolved_url):
        alternatives = []
        match = re.search(r"//([wa])(\d)\.gold-usergeneratedcontent\.net/", resolved_url)
        if match:
            prefix = match.group(1)
            current_num = match.group(2)
            for num in ["1", "2", "3"]:
                if num != current_num:
                    alt_url = resolved_url.replace(f"//{prefix}{current_num}.", f"//{prefix}{num}.")
                    alternatives.append(alt_url)
        return alternatives

    def download_url_with_fallback(self, resolved_url, headers):
        # Try primary URL
        try:
            res = requests.get(resolved_url, headers=headers, timeout=15)
            if res.status_code == 200:
                return res.content
        except Exception as e:
            print(f"Primary URL failed: {e}")

        # Try alternative subdomains (fallback)
        alternatives = self.get_alternative_urls(resolved_url)
        for alt_url in alternatives:
            if self.is_cancelled:
                break
            print(f"Trying fallback URL: {alt_url}")
            try:
                res = requests.get(alt_url, headers=headers, timeout=15)
                if res.status_code == 200:
                    return res.content
            except Exception as e:
                print(f"Fallback URL failed: {e}")
        
        return None

    def download(self):
        try:
            gallery_id = self.extract_gallery_id()
        except ValueError as e:
            self.update_progress(f"Error: {e}", 0.0)
            return False

        self.update_progress("Initializing resolver and fetching gg.js...", 0.05)
        self.resolver = HitomiResolver()
        if self.is_cancelled:
            self.update_progress("Cancelled", 0.0)
            return False

        self.update_progress(f"Fetching metadata for gallery {gallery_id}...", 0.1)
        meta_url = f"https://ltn.gold-usergeneratedcontent.net/galleries/{gallery_id}.js"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": f"https://hitomi.la/reader/{gallery_id}.html"
        }
        
        try:
            r = requests.get(meta_url, headers=headers, timeout=15)
            if r.status_code != 200:
                self.update_progress(f"Error: Gallery metadata not found (HTTP {r.status_code})", 0.0)
                return False
            
            # Extract JSON
            js_content = r.text
            match = re.search(r"var\s+galleryinfo\s*=\s*(\{.*\});?", js_content, re.DOTALL)
            if not match:
                self.update_progress("Error: Could not parse gallery metadata response", 0.0)
                return False
            
            galleryinfo = json.loads(match.group(1))
        except Exception as e:
            self.update_progress(f"Error fetching metadata: {e}", 0.0)
            return False

        if self.is_cancelled:
            self.update_progress("Cancelled", 0.0)
            return False

        title = galleryinfo.get("title", f"hitomi_{gallery_id}")
        sanitized_title = self.sanitize_filename(title)
        
        # Create temp folder for downloads
        temp_dir = os.path.join(self.output_dir, f"temp_{gallery_id}")
        os.makedirs(temp_dir, exist_ok=True)

        files_list = galleryinfo.get("files", [])
        total_files = len(files_list)
        if total_files == 0:
            self.update_progress("Error: Gallery contains no files", 0.0)
            shutil.rmtree(temp_dir, ignore_errors=True)
            return False

        self.update_progress(f"Found {total_files} pages. Starting download...", 0.15)
        downloaded_paths = []

        try:
            for idx, img_info in enumerate(files_list):
                if self.is_cancelled:
                    self.update_progress("Cancelled", 0.0)
                    return False
                
                temp_filepath = os.path.join(temp_dir, f"{idx+1:03d}.webp")
                img_url = self.resolver.get_image_url(img_info, dir_type="webp", ext="webp")
                self.update_progress(f"Downloading page {idx+1}/{total_files}...", 0.15 + (idx / total_files) * 0.7)

                # Retry loop with fallback
                success = False
                for attempt in range(3):
                    if self.is_cancelled:
                        break
                    try:
                        img_headers = {
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                            "Referer": f"https://hitomi.la/reader/{gallery_id}.html",
                            "Origin": "https://hitomi.la"
                        }
                        content = self.download_url_with_fallback(img_url, img_headers)
                        if content:
                            with open(temp_filepath, "wb") as f:
                                f.write(content)
                            downloaded_paths.append(temp_filepath)
                            success = True
                            break
                        else:
                            print(f"Page {idx+1} download attempt {attempt+1} failed")
                    except Exception as e:
                        print(f"Page {idx+1} download attempt {attempt+1} error: {e}")
                    
                    time.sleep(1.0) # sleep before retry

                if not success:
                    if self.is_cancelled:
                        return False
                    self.update_progress(f"Error: Failed to download page {idx+1}", 0.0)
                    return False

                # Throttle delay to avoid DDoS flags
                if idx < total_files - 1:
                    time.sleep(self.throttle_seconds)

            if self.is_cancelled:
                return False

            self.update_progress("Downloads complete. Compiling output file...", 0.9)
            
            if self.format_type == "pdf":
                output_path = os.path.join(self.output_dir, f"{sanitized_title}.pdf")
                self.compile_pdf(downloaded_paths, output_path)
            else:
                output_path = os.path.join(self.output_dir, f"{sanitized_title}.cbz")
                self.compile_cbz(downloaded_paths, output_path)

            self.update_progress(f"Success! Saved to {os.path.basename(output_path)}", 1.0)
            return True

        except Exception as e:
            self.update_progress(f"Compilation error: {e}", 0.0)
            return False
        finally:
            # Clean up temp files
            shutil.rmtree(temp_dir, ignore_errors=True)

    def compile_pdf(self, images_paths, pdf_path):
        images = []
        for path in images_paths:
            img = Image.open(path)
            if img.mode != "RGB":
                img = img.convert("RGB")
            images.append(img)
        
        if images:
            images[0].save(pdf_path, save_all=True, append_images=images[1:])
            for img in images:
                img.close()

    def compile_cbz(self, images_paths, cbz_path):
        with zipfile.ZipFile(cbz_path, 'w', zipfile.ZIP_DEFLATED) as cbz:
            for idx, path in enumerate(images_paths):
                arcname = f"page_{idx+1:03d}.webp"
                cbz.write(path, arcname=arcname)
