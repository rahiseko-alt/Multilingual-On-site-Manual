"""
Unit tests and runtime verification for character extraction pipeline.
"""
import os
import shutil
import pytest
import numpy as np
from PIL import Image, ImageDraw

from src.core.segmenter import SAMSegmenter, create_transparent_png
from src.core.inpaint import generate_clean_plate
from src.core.pipeline import MangaSeparationPipeline, CharacterTarget


@pytest.fixture
def sample_manga_panel(tmp_path):
    """
    Create a synthetic 600x400 manga-like panel with two characters.
    """
    img = Image.new("RGB", (600, 400), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Background speed lines
    for x in range(0, 600, 30):
        draw.line([(x, 0), (300, 200)], fill=(200, 200, 200), width=1)

    # Character 1: Left (e.g. Gojo - rectangle/circle figure)
    draw.rectangle([50, 80, 220, 350], fill=(50, 50, 50), outline=(0, 0, 0), width=2)
    draw.ellipse([80, 40, 190, 120], fill=(240, 240, 240), outline=(0, 0, 0), width=2)

    # Character 2: Right (e.g. Hanami - rectangle/circle figure)
    draw.rectangle([350, 100, 520, 360], fill=(80, 80, 80), outline=(0, 0, 0), width=2)
    draw.ellipse([380, 50, 490, 130], fill=(120, 120, 120), outline=(0, 0, 0), width=2)

    panel_path = os.path.join(tmp_path, "sample_panel.png")
    img.save(panel_path)
    return panel_path


def test_segmenter_fallback(sample_manga_panel):
    img = Image.open(sample_manga_panel)
    segmenter = SAMSegmenter()
    
    # Test bounding box segment
    box = (50, 40, 220, 350)
    mask = segmenter.segment(image=img, box=box)
    assert mask.shape == (400, 600)
    assert np.any(mask > 0)


def test_clean_plate_inpaint(sample_manga_panel):
    img = Image.open(sample_manga_panel)
    mask = np.zeros((400, 600), dtype=np.uint8)
    mask[80:350, 50:220] = 255  # Mask left character

    clean_bg = generate_clean_plate(img, mask)
    assert clean_bg.size == (600, 400)
    assert clean_bg.mode == "RGB"


def test_full_pipeline_execution(sample_manga_panel, tmp_path):
    output_dir = os.path.join(tmp_path, "output")
    pipeline = MangaSeparationPipeline()

    targets = [
        CharacterTarget(name="gojo", box=(40, 30, 230, 360)),
        CharacterTarget(name="hanami", box=(340, 40, 530, 370)),
    ]

    result = pipeline.process(
        image_path=sample_manga_panel,
        targets=targets,
        output_dir=output_dir,
        panel_id="panel_001",
        generate_bg=True,
    )

    # Assert outputs exist
    assert "gojo" in result.character_paths
    assert "hanami" in result.character_paths
    assert os.path.exists(result.character_paths["gojo"])
    assert os.path.exists(result.character_paths["hanami"])
    assert os.path.exists(result.clean_plate_path)
    assert os.path.exists(result.manifest_path)

    # Check RGBA transparency
    gojo_img = Image.open(result.character_paths["gojo"])
    assert gojo_img.mode == "RGBA"
