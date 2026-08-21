"""
CLI script to extract multiple characters from a manga panel image.
"""
import argparse
import sys
import os

# Add root directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.pipeline import MangaSeparationPipeline, CharacterTarget


def parse_char_args(chars_str: str):
    """
    Parse string like 'gojo:100,50,400,600;hanami:450,120,800,700'
    Format: name:x1,y1,x2,y2
    """
    targets = []
    for item in chars_str.split(";"):
        item = item.strip()
        if not item:
            continue
        parts = item.split(":")
        name = parts[0].strip()
        box = None
        if len(parts) > 1 and parts[1]:
            coords = [int(v.strip()) for v in parts[1].split(",")]
            if len(coords) == 4:
                box = tuple(coords)
        targets.append(CharacterTarget(name=name, box=box))
    return targets


def main():
    parser = argparse.ArgumentParser(description="Extract characters from manga panel to transparent PNGs.")
    parser.add_argument("--image", required=True, help="Path to input manga panel image")
    parser.add_argument("--chars", required=True, help="Character specs, e.g. 'gojo:100,50,400,600;hanami:450,120,800,700'")
    parser.add_argument("--output", default="output", help="Output directory")
    parser.add_argument("--panel-id", default="panel_01", help="Panel identifier prefix")
    parser.add_argument("--no-bg", action="store_true", help="Skip clean plate background generation")
    parser.add_argument("--crop", action="store_true", help="Crop character PNGs to bounding box")

    args = parser.parse_args()

    targets = parse_char_args(args.chars)
    if not targets:
        print("Error: No character targets specified.")
        sys.exit(1)

    print(f"[*] Processing image: {args.image}")
    print(f"[*] Extracting {len(targets)} character(s): {[t.name for t in targets]}")

    pipeline = MangaSeparationPipeline()
    result = pipeline.process(
        image_path=args.image,
        targets=targets,
        output_dir=args.output,
        panel_id=args.panel_id,
        generate_bg=not args.no_bg,
        crop_characters=args.crop,
    )

    print("\n[OK] Extraction completed successfully!")
    print(f"  - Clean Background: {result.clean_plate_path}")
    for name, path in result.character_paths.items():
        print(f"  - Character [{name}]: {path}")
    print(f"  - Manifest (for animation tools): {result.manifest_path}\n")


if __name__ == "__main__":
    main()
