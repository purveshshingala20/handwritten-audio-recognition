"""Recognition endpoints: single file and batch."""
import logging

from flask import Blueprint, jsonify, request

from app import database
from app.errors import ApiError
from app.services import pipeline, validation

logger = logging.getLogger(__name__)

recognition_bp = Blueprint("recognition", __name__)


@recognition_bp.post("/api/recognition")
def recognize():
    file = request.files.get("file")
    model = request.form.get("model", "paddleocr")

    if file is None:
        raise ApiError("File must be provided.")

    contents = file.read()
    validation.validate_file(file.filename, contents, model)

    try:
        result = pipeline.run_pipeline(contents, file.filename, model=model)
    except Exception as exc:  # noqa: BLE001 - surfaced to the API caller
        logger.exception("Recognition failed for '%s'", file.filename)
        raise ApiError(f"Recognition failed for '{file.filename}': {exc}", status_code=422) from exc

    record = database.insert_recognition(
        filename=file.filename,
        file_size=len(contents),
        file_type=result["file_type"],
        model_used=result["model_used"],
        recognized_text=result["recognized_text"],
        confidence=result["confidence"],
    )
    return jsonify(record)


@recognition_bp.post("/api/recognition/batch")
def recognize_batch():
    files = request.files.getlist("files")
    model = request.form.get("model", "paddleocr")

    if not files:
        raise ApiError("At least one file must be provided.")

    results = []
    failed = []

    for upload in files:
        try:
            contents = upload.read()
            validation.validate_file(upload.filename, contents, model)
            result = pipeline.run_pipeline(contents, upload.filename, model=model)
            record = database.insert_recognition(
                filename=upload.filename,
                file_size=len(contents),
                file_type=result["file_type"],
                model_used=result["model_used"],
                recognized_text=result["recognized_text"],
                confidence=result["confidence"],
            )
            results.append(record)
        except Exception:  # noqa: BLE001 - failure is tracked per-file, not fatal
            logger.exception("Batch recognition failed for '%s'", upload.filename)
            failed.append(upload.filename)

    return jsonify(
        {
            "processed_count": len(results),
            "failed_count": len(failed),
            "results": results,
            "failed": failed,
        }
    )
