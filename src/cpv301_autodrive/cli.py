import argparse
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

from cpv301_autodrive.config import PROJECT_ROOT, get_settings
from cpv301_autodrive.evaluation import evaluate_classifier
from cpv301_autodrive.inference import ModelService


def project_info() -> int:
    settings = get_settings()
    payload = {
        "project_root": str(PROJECT_ROOT),
        "model_path": str(settings.model_path),
        "model_exists": settings.model_path.is_file(),
        "confidence_threshold": settings.confidence_threshold,
        "notebooks": sorted(path.name for path in (PROJECT_ROOT / "notebooks").glob("*.ipynb")),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["model_exists"] else 1


def predict_file(image_path: Path) -> int:
    settings = get_settings()
    service = ModelService(settings.model_path, settings.confidence_threshold)
    with Image.open(image_path) as image:
        result = service.predict(image)
    print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
    return 0


def serve_web(host: str, port: int, headless: bool) -> int:
    app_path = Path(__file__).with_name("web_app.py")
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.address",
        host,
        "--server.port",
        str(port),
        "--server.headless",
        str(headless).lower(),
    ]
    return subprocess.call(command)


def evaluate_model(split_path: Path, output_dir: Path, batch_size: int) -> int:
    settings = get_settings()
    summary = evaluate_classifier(
        settings.model_path,
        split_path,
        output_dir,
        batch_size=batch_size,
        threshold=settings.confidence_threshold,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="cpv301")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("info", help="Show local artifact status")
    predict_parser = subparsers.add_parser(
        "predict",
        help="Classify one cropped traffic-sign image",
    )
    predict_parser.add_argument("image", type=Path)
    serve_parser = subparsers.add_parser("serve", help="Run the local FastAPI service")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", default=8000, type=int)
    web_parser = subparsers.add_parser("web", help="Run the Streamlit simulation webapp")
    web_parser.add_argument("--host", default="127.0.0.1")
    web_parser.add_argument("--port", default=8501, type=int)
    web_parser.add_argument("--headless", action="store_true")
    evaluate_parser = subparsers.add_parser(
        "evaluate",
        help="Evaluate the classifier on a trusted GTSRB pickle split",
    )
    evaluate_parser.add_argument(
        "--split",
        type=Path,
        default=PROJECT_ROOT / "data" / "processed" / "test.p",
    )
    evaluate_parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "results" / "evaluation" / "gtsrb_test_baseline",
    )
    evaluate_parser.add_argument("--batch-size", type=int, default=256)

    args = parser.parse_args()
    if args.command == "info":
        return project_info()
    if args.command == "predict":
        return predict_file(args.image)
    if args.command == "web":
        return serve_web(args.host, args.port, args.headless)
    if args.command == "evaluate":
        return evaluate_model(args.split, args.output, args.batch_size)

    import uvicorn

    uvicorn.run("cpv301_autodrive.api:app", host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
