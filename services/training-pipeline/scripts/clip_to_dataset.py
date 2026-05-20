#!/usr/bin/env python3
"""
Event Clip to Dataset Converter
Platform 1.0 - AI기반 장애인직업재활시설 스마트안전시스템

Converts event video clips into training dataset (frames + annotations).

Usage:
    python clip_to_dataset.py --input <clips_dir> --output <dataset_dir>
    python clip_to_dataset.py --input datasets/raw/clips --output datasets/processed

Environment:
    Requires: opencv-python, numpy
"""

import argparse
import json
import os
import sys
import hashlib
import shutil
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict
from datetime import datetime

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("[WARN] opencv-python not installed. Running in dry-run/schema-only mode.")


# --- Constants ---
TARGET_WIDTH = 960
TARGET_HEIGHT = 544
SUPPORTED_FORMATS = ['.mp4', '.avi', '.mkv']
SPLIT_RATIO = {'train': 0.8, 'val': 0.1, 'test': 0.1}
FRAME_EXTRACTION_FPS = 5  # Extract 5 frames per second from clips


# --- Data Classes ---
@dataclass
class ClipMetadata:
    """Event clip metadata structure (from event-message-schema)"""
    event_id: str
    site_id: str
    camera_id: str
    event_type: str
    risk_level: str
    timestamp: str
    duration_sec: int = 60
    pre_event_sec: int = 30
    post_event_sec: int = 30
    fps: int = 30
    resolution: Dict[str, int] = field(default_factory=lambda: {"width": 1920, "height": 1080})
    model_version: Optional[str] = None


@dataclass
class DatasetStats:
    """Dataset statistics"""
    total_clips_processed: int = 0
    total_frames_extracted: int = 0
    total_annotations: int = 0
    by_class: Dict[str, int] = field(default_factory=dict)
    by_split: Dict[str, int] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


# --- Label Map ---
LABEL_MAP = {
    0: "person",
    1: "fall",
    2: "collapse",
    3: "fire",
    4: "intrusion",
    5: "hazardous_action"
}

EVENT_TYPE_TO_CLASS = {
    "FALL_DETECTED": "fall",
    "COLLAPSE_DETECTED": "collapse",
    "FIRE_DETECTED": "fire",
    "ZONE_INTRUSION": "intrusion",
    "HAZARDOUS_ACTION": "hazardous_action",
}


def load_clip_metadata(clip_dir: Path) -> Optional[ClipMetadata]:
    """Load metadata.json from clip directory."""
    meta_path = clip_dir / "metadata.json"
    if not meta_path.exists():
        print(f"  [WARN] No metadata.json in {clip_dir}")
        return None

    with open(meta_path, 'r') as f:
        data = json.load(f)

    return ClipMetadata(
        event_id=data.get("event_id", ""),
        site_id=data.get("site_id", "SITE-001"),
        camera_id=data.get("camera_id", "CAM-001"),
        event_type=data.get("event_type", ""),
        risk_level=data.get("risk_level", "NORMAL"),
        timestamp=data.get("timestamp", ""),
        duration_sec=data.get("duration_sec", 60),
        pre_event_sec=data.get("pre_event_sec", 30),
        post_event_sec=data.get("post_event_sec", 30),
        fps=data.get("fps", 30),
        resolution=data.get("resolution", {"width": 1920, "height": 1080}),
        model_version=data.get("model_version"),
    )


def extract_frames(clip_path: Path, output_dir: Path, target_fps: int = FRAME_EXTRACTION_FPS) -> List[Path]:
    """Extract frames from video clip at target FPS."""
    if not CV2_AVAILABLE:
        print(f"  [DRY-RUN] Would extract frames from {clip_path}")
        return []

    cap = cv2.VideoCapture(str(clip_path))
    if not cap.isOpened():
        print(f"  [ERROR] Cannot open video: {clip_path}")
        return []

    source_fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(source_fps / target_fps) if source_fps > target_fps else 1
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    output_dir.mkdir(parents=True, exist_ok=True)
    extracted = []
    frame_idx = 0
    saved_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % frame_interval == 0:
            # Resize to target dimensions
            resized = cv2.resize(frame, (TARGET_WIDTH, TARGET_HEIGHT))
            filename = f"frame_{saved_idx:06d}.jpg"
            output_path = output_dir / filename
            cv2.imwrite(str(output_path), resized)
            extracted.append(output_path)
            saved_idx += 1

        frame_idx += 1

    cap.release()
    print(f"  Extracted {saved_idx} frames from {total_frames} total (interval={frame_interval})")
    return extracted


def create_kitti_annotation(class_name: str, bbox: Dict[str, float] = None) -> str:
    """
    Create KITTI format annotation line.
    
    If bbox is None, creates a placeholder annotation for the event class.
    Actual bounding boxes should come from annotation tools or AI pre-labeling.
    """
    if bbox is None:
        # Placeholder - center of frame
        xmin, ymin, xmax, ymax = 0.3 * TARGET_WIDTH, 0.3 * TARGET_HEIGHT, 0.7 * TARGET_WIDTH, 0.7 * TARGET_HEIGHT
    else:
        xmin = bbox.get("x", 0.3) * TARGET_WIDTH
        ymin = bbox.get("y", 0.3) * TARGET_HEIGHT
        xmax = (bbox.get("x", 0.3) + bbox.get("w", 0.4)) * TARGET_WIDTH
        ymax = (bbox.get("y", 0.3) + bbox.get("h", 0.4)) * TARGET_HEIGHT

    # KITTI format: class truncated occluded alpha xmin ymin xmax ymax h w l x y z ry
    return f"{class_name} 0.0 0 0.0 {xmin:.2f} {ymin:.2f} {xmax:.2f} {ymax:.2f} 0.0 0.0 0.0 0.0 0.0 0.0 0.0"


def assign_split(index: int, total: int) -> str:
    """Assign frame to train/val/test split based on ratio."""
    train_end = int(total * SPLIT_RATIO['train'])
    val_end = train_end + int(total * SPLIT_RATIO['val'])

    if index < train_end:
        return 'train'
    elif index < val_end:
        return 'val'
    else:
        return 'test'


def process_clips(input_dir: Path, output_dir: Path, dry_run: bool = False) -> DatasetStats:
    """Process all event clips and create dataset."""
    stats = DatasetStats(
        by_class={c: 0 for c in LABEL_MAP.values()},
        by_split={'train': 0, 'val': 0, 'test': 0},
    )

    # Ensure output structure
    for split in ['train', 'val', 'test']:
        (output_dir / split / 'images').mkdir(parents=True, exist_ok=True)
        (output_dir / split / 'labels').mkdir(parents=True, exist_ok=True)

    clips_dir = input_dir
    if not clips_dir.exists():
        print(f"[ERROR] Clips directory not found: {clips_dir}")
        return stats

    # Collect all clip directories
    clip_dirs = [d for d in sorted(clips_dir.iterdir()) if d.is_dir()]
    if not clip_dirs:
        print("[INFO] No clip directories found. Creating sample structure only.")
        return stats

    global_frame_idx = 0
    total_expected_frames = len(clip_dirs) * 30  # Estimate

    for clip_dir in clip_dirs:
        print(f"\nProcessing: {clip_dir.name}")

        # Load metadata
        metadata = load_clip_metadata(clip_dir)
        if metadata is None:
            stats.errors.append(f"No metadata: {clip_dir.name}")
            continue

        # Determine class from event_type
        class_name = EVENT_TYPE_TO_CLASS.get(metadata.event_type, "person")

        # Find video file
        clip_file = None
        for fmt in SUPPORTED_FORMATS:
            candidate = clip_dir / f"clip{fmt}"
            if candidate.exists():
                clip_file = candidate
                break

        if clip_file is None and not dry_run:
            print(f"  [WARN] No video file in {clip_dir}")
            stats.errors.append(f"No video: {clip_dir.name}")
            continue

        # Extract frames
        if dry_run or not CV2_AVAILABLE:
            print(f"  [DRY-RUN] Would extract frames for event: {metadata.event_id}")
            frame_count = 15  # Simulated
        else:
            frames_out = input_dir.parent / "frames" / metadata.event_id
            extracted = extract_frames(clip_file, frames_out)
            frame_count = len(extracted)

        # Distribute frames to splits
        for i in range(frame_count):
            split = assign_split(global_frame_idx, total_expected_frames)
            img_name = f"img_{global_frame_idx:06d}.jpg"
            label_name = f"img_{global_frame_idx:06d}.txt"

            if not dry_run and CV2_AVAILABLE and clip_file:
                # Copy frame to split directory
                src_frame = input_dir.parent / "frames" / metadata.event_id / f"frame_{i:06d}.jpg"
                dst_frame = output_dir / split / "images" / img_name
                if src_frame.exists():
                    shutil.copy2(str(src_frame), str(dst_frame))

            # Create annotation
            annotation = create_kitti_annotation(class_name)
            label_path = output_dir / split / "labels" / label_name
            if not dry_run:
                with open(label_path, 'w') as f:
                    f.write(annotation + "\n")

            stats.by_class[class_name] = stats.by_class.get(class_name, 0) + 1
            stats.by_split[split] += 1
            stats.total_annotations += 1
            global_frame_idx += 1

        stats.total_clips_processed += 1
        stats.total_frames_extracted += frame_count

    return stats


def update_manifest(output_dir: Path, stats: DatasetStats):
    """Update dataset_manifest.json with processing statistics."""
    manifest_path = output_dir.parent / "manifests" / "dataset_manifest.json"
    if manifest_path.exists():
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
    else:
        manifest = {
            "schema_version": "1.0",
            "dataset_id": "ds-v1.0",
        }

    manifest["updated_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
    manifest["statistics"] = {
        "total_images": stats.total_frames_extracted,
        "total_annotations": stats.total_annotations,
        "by_class": stats.by_class,
        "by_split": stats.by_split,
    }

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"\n[INFO] Updated manifest: {manifest_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert event clips to training dataset"
    )
    parser.add_argument("--input", required=True, help="Input clips directory path")
    parser.add_argument("--output", required=True, help="Output processed dataset directory path")
    parser.add_argument("--fps", type=int, default=FRAME_EXTRACTION_FPS, help="Frame extraction FPS (default: 5)")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (no actual file operations)")

    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)

    print("=" * 60)
    print(" Event Clip → Dataset Converter")
    print(f" Input:  {input_dir}")
    print(f" Output: {output_dir}")
    print(f" FPS:    {args.fps}")
    print(f" Mode:   {'DRY-RUN' if args.dry_run else 'LIVE'}")
    print("=" * 60)

    # Update frame extraction FPS from argument
    frame_extraction_fps = args.fps

    stats = process_clips(input_dir, output_dir, dry_run=args.dry_run)
    update_manifest(output_dir, stats)

    print("\n" + "=" * 60)
    print(" Conversion Summary")
    print("=" * 60)
    print(f"  Clips processed:   {stats.total_clips_processed}")
    print(f"  Frames extracted:  {stats.total_frames_extracted}")
    print(f"  Annotations:       {stats.total_annotations}")
    print(f"  By class: {json.dumps(stats.by_class, indent=4)}")
    print(f"  By split: {json.dumps(stats.by_split, indent=4)}")
    if stats.errors:
        print(f"  Errors: {len(stats.errors)}")
        for err in stats.errors:
            print(f"    - {err}")
    print("=" * 60)


if __name__ == "__main__":
    main()
