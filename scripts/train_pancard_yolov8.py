#!/usr/bin/env python3
"""PAN Card YOLOv8 Entity Detection Training & Dataset Download Script.

Downloads the Roboflow dataset 'panocr/ocr-qaxqg' (version 5) in YOLOv8 format
and fine-tunes an object detection model to detect:
  1. pan_number
  2. name
  3. father_name
  4. dob

Usage:
    # 1. Dry run check / help
    python scripts/train_pancard_yolov8.py --dry-run

    # 2. Download dataset only
    python scripts/train_pancard_yolov8.py --api-key YOUR_ROBOFLOW_KEY --download-only

    # 3. Train on GPU/CPU and export weights
    python scripts/train_pancard_yolov8.py --api-key YOUR_ROBOFLOW_KEY --epochs 50 --batch 16
"""

import argparse
import os
import shutil
import sys

ROBOFLOW_WORKSPACE_DEFAULT = "panocr"
ROBOFLOW_PROJECT_DEFAULT = "ocr-qaxqg"
ROBOFLOW_VERSION_DEFAULT = 5
DEFAULT_OUTPUT_WEIGHTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "backend",
    "app",
    "models",
    "weights",
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train YOLOv8 on PAN Card Entity Detection dataset (Roboflow panocr/ocr-qaxqg v5)"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=os.getenv("ROBOFLOW_API_KEY", ""),
        help="Roboflow API key (can also be supplied via ROBOFLOW_API_KEY env var)",
    )
    parser.add_argument(
        "--workspace",
        type=str,
        default=ROBOFLOW_WORKSPACE_DEFAULT,
        help="Roboflow workspace name (default: panocr)",
    )
    parser.add_argument(
        "--project",
        type=str,
        default=ROBOFLOW_PROJECT_DEFAULT,
        help="Roboflow project slug (default: ocr-qaxqg)",
    )
    parser.add_argument(
        "--version",
        type=int,
        default=ROBOFLOW_VERSION_DEFAULT,
        help="Roboflow dataset version (default: 5)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="yolov8n.pt",
        help="Pretrained YOLO model checkpoint to fine-tune (yolov8n.pt, yolov8s.pt, yolov8m.pt)",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=50,
        help="Number of training epochs (default: 50)",
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=16,
        help="Training batch size (default: 16)",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Image size for training and inference (default: 640)",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="",
        help="Compute device (e.g. '0', 'cpu', 'cuda'). Defaults to auto-detect.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=DEFAULT_OUTPUT_WEIGHTS_DIR,
        help=f"Target directory for exported weights (default: {DEFAULT_OUTPUT_WEIGHTS_DIR})",
    )
    parser.add_argument(
        "--export-onnx",
        action="store_true",
        help="Export best trained weights to ONNX format for lightweight deployment",
    )
    parser.add_argument(
        "--download-only",
        action="store_true",
        help="Download the dataset in YOLOv8 format and exit without training",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate parameters and environment configuration without executing download or training",
    )
    return parser.parse_args()


def check_dependencies() -> bool:
    """Verify that ultralytics and roboflow packages are installed."""
    missing = []
    try:
        import roboflow  # noqa: F401
    except ImportError:
        missing.append("roboflow")

    try:
        import ultralytics  # noqa: F401
    except ImportError:
        missing.append("ultralytics")

    if missing:
        print("[!] Missing required training packages: " + ", ".join(missing))
        print("    Install them using: pip install " + " ".join(missing))
        return False
    return True


def run_training_pipeline(args: argparse.Namespace) -> int:
    print("=================================================================")
    print("[*] PAN CARD ENTITY DETECTION TRAINING PIPELINE (YOLOv8)")
    print("=================================================================")
    print(f"  Dataset:      {args.workspace}/{args.project} (v{args.version})")
    print(f"  Base Model:   {args.model}")
    print(f"  Epochs:       {args.epochs}")
    print(f"  Batch Size:   {args.batch}")
    print(f"  Image Size:   {args.imgsz}x{args.imgsz}")
    print(f"  Target Dir:   {args.output_dir}")
    print("=================================================================")

    if args.dry_run:
        print("[i] Dry-run mode enabled.")
        print("    Configuration syntax valid.")
        print("    Target entities: ['pan_number', 'name', 'father_name', 'dob']")
        print(">>> DRY RUN CHECK COMPLETED SUCCESSFULLY.")
        return 0

    if not check_dependencies():
        return 1

    if not args.api_key:
        print("[ERROR] Roboflow API key required to download dataset.")
        print("        Provide via --api-key <YOUR_KEY> or set ROBOFLOW_API_KEY environment variable.")
        return 1

    from roboflow import Roboflow  # type: ignore

    print(f"[*] Authenticating with Roboflow and fetching dataset v{args.version}...")
    rf = Roboflow(api_key=args.api_key)
    project = rf.workspace(args.workspace).project(args.project)
    dataset = project.version(args.version).download("yolov8")

    dataset_location = dataset.location
    data_yaml_path = os.path.join(dataset_location, "data.yaml")
    print(f"[+] Dataset downloaded to: {dataset_location}")
    print(f"[+] Dataset configuration: {data_yaml_path}")

    if args.download_only:
        print("[+] Download complete (--download-only specified). Exiting.")
        return 0

    from ultralytics import YOLO  # type: ignore

    print(f"[*] Initializing base model '{args.model}'...")
    model = YOLO(args.model)

    print(f"[*] Starting training for {args.epochs} epochs...")
    train_kwargs = {
        "data": data_yaml_path,
        "epochs": args.epochs,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "plots": True,
    }
    if args.device:
        train_kwargs["device"] = args.device

    train_results = model.train(**train_kwargs)
    print(f"[+] Training completed. Results saved to: {train_results.save_dir}")

    # Locate best.pt
    best_weights_path = os.path.join(train_results.save_dir, "weights", "best.pt")
    if not os.path.exists(best_weights_path):
        print(f"[!] Warning: best.pt not found at expected path: {best_weights_path}")
        return 1

    os.makedirs(args.output_dir, exist_ok=True)
    target_weights_path = os.path.join(args.output_dir, "pancard_yolov8.pt")
    shutil.copy2(best_weights_path, target_weights_path)
    print(f"[+] Copied trained weights to platform repository:")
    print(f"    --> {target_weights_path}")

    # Optional ONNX export
    if args.export_onnx:
        print("[*] Exporting model to ONNX format...")
        onnx_path = model.export(format="onnx")
        print(f"[+] ONNX export generated: {onnx_path}")

    print("=================================================================")
    print(">>> SUCCESS: PAN Card Entity Detection Model Trained & Deployed <<<")
    print("=================================================================")
    return 0


if __name__ == "__main__":
    cli_args = parse_arguments()
    sys.exit(run_training_pipeline(cli_args))
