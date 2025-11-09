"""
ComfyUI Archive Output - Compression API
Server-side API for compressing PNG files to JPEG with metadata preservation.
Based on ComfyUI-Image-Saver methodology for workflow metadata transfer.
"""

import os
import json
from PIL import Image
from aiohttp import web
import folder_paths

# Try to import piexif, provide helpful error if missing
try:
    import piexif
    import piexif.helper
    PIEXIF_AVAILABLE = True
except ImportError:
    PIEXIF_AVAILABLE = False
    print("[Compress API] WARNING: piexif not installed. Metadata preservation will be disabled.")
    print("[Compress API] Install with: pip install piexif")


class CompressionService:
    """Service class for compressing images with metadata preservation."""

    MAX_EXIF_SIZE = 65535  # JPEG EXIF size limit

    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()

        # Progress tracking
        self.is_running = False
        self.cancel_requested = False
        self.progress = {
            "current": 0,
            "total": 0,
            "current_file": "",
            "compressed": 0,
            "errors": 0,
            "total_original_size": 0,
            "total_compressed_size": 0,
            "metadata_full": 0,
            "metadata_partial": 0,
            "metadata_none": 0
        }

    def _extract_png_metadata(self, png_image):
        """
        Extract ComfyUI workflow metadata from PNG image.

        Args:
            png_image: PIL Image object

        Returns:
            dict: Metadata containing 'prompt' and 'workflow' if available
        """
        metadata = {}

        try:
            # Extract PNG text chunks
            info = png_image.info

            if "prompt" in info:
                try:
                    metadata["prompt"] = json.loads(info["prompt"])
                except json.JSONDecodeError:
                    metadata["prompt"] = info["prompt"]

            if "workflow" in info:
                try:
                    metadata["workflow"] = json.loads(info["workflow"])
                except json.JSONDecodeError:
                    metadata["workflow"] = info["workflow"]

        except Exception as e:
            print(f"[Compress API] Error extracting PNG metadata: {e}")

        return metadata

    def _create_exif_with_metadata(self, metadata):
        """
        Create EXIF bytes with ComfyUI metadata embedded.
        Uses ComfyUI-Image-Saver methodology.

        Args:
            metadata: Dict with 'prompt' and 'workflow' keys

        Returns:
            tuple: (exif_bytes, metadata_status) where status is 'full', 'workflow_only', or 'none'
        """
        if not PIEXIF_AVAILABLE:
            return piexif.dump({}), 'none'

        try:
            # Prepare metadata for EXIF embedding
            exif_dict = {"0th": {}, "Exif": {}}
            metadata_status = 'none'

            # Try to embed workflow
            if "workflow" in metadata:
                workflow_str = f"workflow:{json.dumps(metadata['workflow'], separators=(',', ':'))}"
                exif_dict["0th"][piexif.ImageIFD.Make] = workflow_str.encode('utf-8')
                metadata_status = 'workflow_only'

            # Try to embed prompt
            if "prompt" in metadata:
                prompt_str = f"prompt:{json.dumps(metadata['prompt'], separators=(',', ':'))}"
                exif_dict["0th"][piexif.ImageIFD.Model] = prompt_str.encode('utf-8')
                if metadata_status == 'workflow_only':
                    metadata_status = 'full'

            # Create EXIF bytes
            exif_bytes = piexif.dump(exif_dict)

            # Check size limit and apply fallback strategy
            if len(exif_bytes) > self.MAX_EXIF_SIZE:
                print(f"[Compress API] Metadata too large ({len(exif_bytes)} bytes), removing prompt")
                # Fallback 1: Remove prompt, keep workflow only
                exif_dict["0th"].pop(piexif.ImageIFD.Model, None)
                exif_bytes = piexif.dump(exif_dict)
                metadata_status = 'workflow_only'

                if len(exif_bytes) > self.MAX_EXIF_SIZE:
                    print(f"[Compress API] Workflow still too large ({len(exif_bytes)} bytes), cannot embed")
                    # Fallback 2: Remove everything
                    exif_bytes = piexif.dump({})
                    metadata_status = 'none'

            return exif_bytes, metadata_status

        except Exception as e:
            print(f"[Compress API] Error creating EXIF metadata: {e}")
            return piexif.dump({}), 'none'

    def compress_image(self, png_path, quality=90, output_format="JPEG", delete_original=False):
        """
        Compress a single PNG image to JPEG/WebP with metadata preservation.

        Args:
            png_path: Path to source PNG file
            quality: Compression quality (1-100)
            output_format: 'JPEG' or 'WEBP'
            delete_original: Whether to delete the PNG after successful compression

        Returns:
            dict: Result with success status, file sizes, and metadata info
        """
        result = {
            "success": False,
            "original_path": png_path,
            "compressed_path": None,
            "original_size": 0,
            "compressed_size": 0,
            "savings_bytes": 0,
            "savings_percent": 0,
            "metadata_status": "none",
            "error": None
        }

        try:
            # Validate input file exists and is PNG
            if not os.path.exists(png_path):
                result["error"] = "File not found"
                return result

            if not png_path.lower().endswith('.png'):
                result["error"] = "Not a PNG file"
                return result

            # Get original file size
            result["original_size"] = os.path.getsize(png_path)

            # Load PNG image
            png_image = Image.open(png_path)

            # Extract metadata
            metadata = self._extract_png_metadata(png_image)

            # Convert to RGB (JPEG doesn't support transparency)
            if png_image.mode in ("RGBA", "LA", "P"):
                rgb_image = Image.new("RGB", png_image.size, (255, 255, 255))
                if png_image.mode == "RGBA":
                    rgb_image.paste(png_image, mask=png_image.split()[-1])
                else:
                    rgb_image.paste(png_image)
                png_image = rgb_image
            elif png_image.mode != "RGB":
                png_image = png_image.convert("RGB")

            # Create output path
            ext = ".jpg" if output_format == "JPEG" else ".webp"
            compressed_path = png_path.rsplit('.', 1)[0] + ext
            result["compressed_path"] = compressed_path

            # Save compressed image (initially without metadata)
            save_params = {
                "quality": quality,
                "optimize": True
            }

            if output_format == "WEBP":
                save_params["method"] = 6  # Better compression

            png_image.save(compressed_path, output_format, **save_params)

            # Embed metadata into EXIF (both JPEG and WebP)
            if PIEXIF_AVAILABLE and metadata:
                exif_bytes, metadata_status = self._create_exif_with_metadata(metadata)
                result["metadata_status"] = metadata_status

                if len(exif_bytes) > len(piexif.dump({})):  # If we have actual metadata
                    try:
                        piexif.insert(exif_bytes, compressed_path)
                    except Exception as e:
                        print(f"[Compress API] Error inserting EXIF: {e}")
                        result["metadata_status"] = "none"

            # Get compressed file size
            result["compressed_size"] = os.path.getsize(compressed_path)
            result["savings_bytes"] = result["original_size"] - result["compressed_size"]
            result["savings_percent"] = (result["savings_bytes"] / result["original_size"]) * 100 if result["original_size"] > 0 else 0

            # Delete original if requested
            if delete_original and result["compressed_size"] > 0:
                try:
                    os.remove(png_path)
                except Exception as e:
                    print(f"[Compress API] Warning: Could not delete original file: {e}")

            result["success"] = True
            print(f"[Compress API] Compressed {os.path.basename(png_path)}: {result['original_size']:,} → {result['compressed_size']:,} bytes ({result['savings_percent']:.1f}% saved)")

        except Exception as e:
            result["error"] = str(e)
            print(f"[Compress API] Error compressing {png_path}: {e}")

        return result

    def reset_progress(self):
        """Reset progress tracking"""
        self.progress = {
            "current": 0,
            "total": 0,
            "current_file": "",
            "compressed": 0,
            "errors": 0,
            "total_original_size": 0,
            "total_compressed_size": 0,
            "metadata_full": 0,
            "metadata_partial": 0,
            "metadata_none": 0
        }

    def request_cancel(self):
        """Request cancellation of current operation"""
        self.cancel_requested = True
        print("[Compress API] Cancellation requested")

    def compress_directory(self, config):
        """
        Compress all PNG files in a directory with progress tracking.

        Args:
            config: Dict with compression settings:
                - target_directory: Directory to scan (default: output directory)
                - quality: JPEG quality 1-100 (default: 90)
                - output_format: 'JPEG' or 'WEBP' (default: 'JPEG')
                - delete_original: Delete PNG after compression (default: False)
                - recursive: Scan subdirectories (default: True)

        Returns:
            dict: Summary of compression operation
        """
        # Check if already running
        if self.is_running:
            return {
                "success": False,
                "error": "Compression already in progress",
                "compressed": 0,
                "errors": 0
            }

        self.is_running = True
        self.cancel_requested = False
        self.reset_progress()

        print(f"\n[Compress API] ========== COMPRESSION PROCESS STARTED ==========")

        try:
            # Extract configuration
            target_dir_param = config.get("target_directory", "")
            quality = config.get("quality", 90)
            output_format = config.get("output_format", "JPEG").upper()
            delete_original = config.get("delete_original", False)
            recursive = config.get("recursive", True)

            # Determine target directory
            if target_dir_param and target_dir_param.strip():
                # User specified a custom directory
                target_dir_param = target_dir_param.strip()

                # Check if it's a relative path or absolute path
                if os.path.isabs(target_dir_param):
                    target_dir = target_dir_param
                else:
                    # Relative to output directory
                    target_dir = os.path.join(self.output_dir, target_dir_param)
            else:
                # Default to output directory
                target_dir = self.output_dir

            # Verify target directory exists
            if not os.path.exists(target_dir):
                return {
                    "success": False,
                    "error": f"Target directory does not exist: {target_dir}",
                    "compressed": 0,
                    "errors": 0
                }

            print(f"[Compress API] Target Directory: {target_dir}")
            print(f"[Compress API] Quality: {quality}%")
            print(f"[Compress API] Format: {output_format}")
            print(f"[Compress API] Delete Original: {delete_original}")
            print(f"[Compress API] Recursive: {recursive}")

            # Counters
            total_skipped = 0

            # Find all PNG files
            png_files = []

            if recursive:
                for root, dirs, files in os.walk(target_dir):
                    # No longer skip Archive folders - process everything!
                    for file in files:
                        if file.lower().endswith('.png'):
                            png_files.append(os.path.join(root, file))
            else:
                png_files = [os.path.join(target_dir, f) for f in os.listdir(target_dir)
                            if f.lower().endswith('.png') and os.path.isfile(os.path.join(target_dir, f))]

            # Update progress
            self.progress["total"] = len(png_files)
            print(f"[Compress API] Found {len(png_files)} PNG files to compress")

            # Compress each file
            for idx, png_path in enumerate(png_files):
                # Check for cancellation
                if self.cancel_requested:
                    print(f"[Compress API] Compression cancelled by user at {idx}/{len(png_files)}")
                    break

                # Update progress
                self.progress["current"] = idx + 1
                self.progress["current_file"] = os.path.basename(png_path)

                result = self.compress_image(png_path, quality, output_format, delete_original)

                if result["success"]:
                    self.progress["compressed"] += 1
                    self.progress["total_original_size"] += result["original_size"]
                    self.progress["total_compressed_size"] += result["compressed_size"]

                    # Track metadata preservation
                    if result["metadata_status"] == "full":
                        self.progress["metadata_full"] += 1
                    elif result["metadata_status"] == "workflow_only":
                        self.progress["metadata_partial"] += 1
                    else:
                        self.progress["metadata_none"] += 1
                else:
                    if result["error"]:
                        self.progress["errors"] += 1
                    else:
                        total_skipped += 1

            total_savings = self.progress["total_original_size"] - self.progress["total_compressed_size"]
            savings_percent = (total_savings / self.progress["total_original_size"] * 100) if self.progress["total_original_size"] > 0 else 0

            print(f"[Compress API] Compression complete:")
            print(f"[Compress API]   Compressed: {self.progress['compressed']}")
            print(f"[Compress API]   Errors: {self.progress['errors']}")
            print(f"[Compress API]   Total savings: {total_savings:,} bytes ({savings_percent:.1f}%)")
            print(f"[Compress API] ========== COMPRESSION PROCESS FINISHED ==========\n")

            return {
                "success": True,
                "cancelled": self.cancel_requested,
                "total_files": len(png_files),
                "compressed": self.progress["compressed"],
                "skipped": total_skipped,
                "errors": self.progress["errors"],
                "original_size_bytes": self.progress["total_original_size"],
                "compressed_size_bytes": self.progress["total_compressed_size"],
                "savings_bytes": total_savings,
                "savings_percent": savings_percent,
                "metadata_full": self.progress["metadata_full"],
                "metadata_partial": self.progress["metadata_partial"],
                "metadata_none": self.progress["metadata_none"],
                "piexif_available": PIEXIF_AVAILABLE
            }

        finally:
            self.is_running = False
            self.cancel_requested = False


# Global service instance
compression_service = CompressionService()


def setup_routes(routes):
    """
    Setup API routes for compression functionality.

    Args:
        routes: The PromptServer routes object
    """

    @routes.post("/compress/execute")
    async def execute_compress_endpoint(request):
        """Execute the compression operation in background."""
        try:
            # Check if already running
            if compression_service.is_running:
                return web.json_response({
                    "success": False,
                    "error": "Compression already in progress",
                    "compressed": 0,
                    "errors": 0
                }, status=400)

            json_data = await request.json()

            # Start compression in background thread
            import asyncio
            loop = asyncio.get_event_loop()
            loop.run_in_executor(None, compression_service.compress_directory, json_data)

            # Return immediately - client should poll for progress
            return web.json_response({
                "success": True,
                "message": "Compression started",
                "poll_progress": True
            })

        except Exception as e:
            print(f"[Compress API] Error in execute endpoint: {e}")
            return web.json_response({
                "success": False,
                "error": str(e),
                "compressed": 0,
                "errors": 1
            }, status=500)

    @routes.get("/compress/progress")
    async def get_compress_progress(request):
        """Get current compression progress."""
        try:
            progress = compression_service.progress.copy()
            progress["is_running"] = compression_service.is_running
            progress["cancel_requested"] = compression_service.cancel_requested

            # Calculate percentages and speeds
            if progress["total"] > 0:
                progress["percent"] = (progress["current"] / progress["total"]) * 100
            else:
                progress["percent"] = 0

            # Calculate savings
            if progress["total_original_size"] > 0:
                savings = progress["total_original_size"] - progress["total_compressed_size"]
                progress["savings_bytes"] = savings
                progress["savings_percent"] = (savings / progress["total_original_size"]) * 100
            else:
                progress["savings_bytes"] = 0
                progress["savings_percent"] = 0

            return web.json_response({
                "success": True,
                **progress
            })
        except Exception as e:
            print(f"[Compress API] Error in progress endpoint: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    @routes.post("/compress/cancel")
    async def cancel_compress_endpoint(request):
        """Cancel the current compression operation."""
        try:
            if not compression_service.is_running:
                return web.json_response({
                    "success": False,
                    "error": "No compression in progress"
                }, status=400)

            compression_service.request_cancel()

            return web.json_response({
                "success": True,
                "message": "Cancellation requested"
            })
        except Exception as e:
            print(f"[Compress API] Error in cancel endpoint: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    @routes.get("/compress/status")
    async def get_compress_status(request):
        """Get compression capability status."""
        try:
            output_dir = folder_paths.get_output_directory()

            # Count PNG files
            png_count = 0
            total_png_size = 0

            for root, dirs, files in os.walk(output_dir):
                if "Archive" in root or "archive" in root:
                    continue
                for file in files:
                    if file.lower().endswith('.png'):
                        png_count += 1
                        file_path = os.path.join(root, file)
                        try:
                            total_png_size += os.path.getsize(file_path)
                        except:
                            pass

            return web.json_response({
                "success": True,
                "piexif_available": PIEXIF_AVAILABLE,
                "png_count": png_count,
                "total_png_size_bytes": total_png_size,
                "output_directory": output_dir
            })
        except Exception as e:
            print(f"[Compress API] Error in status endpoint: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    print("[Compress API] Routes registered successfully")
    print("[Compress API] Available endpoints:")
    print("[Compress API]   POST /compress/execute - Start compression")
    print("[Compress API]   GET  /compress/progress - Get progress")
    print("[Compress API]   POST /compress/cancel - Cancel compression")
    print("[Compress API]   GET  /compress/status - Get status")
