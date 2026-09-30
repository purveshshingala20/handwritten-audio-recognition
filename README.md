# Handwritten Text & Audio Recognition System

Upload a handwritten image or an audio recording and get back recognized,
cleaned-up text. The backend runs the file through a pre-processing pipeline
and one of two OCR engines (for images) or a Whisper ASR model (for audio),
stores every result locally, and supports batch uploads.

```
CuriousClick_Project/
├── backend/                # Flask service
│   ├── app/
│   │   ├── main.py         # App factory, CORS, blueprint registration, error handler
│   │   ├── config.py       # Settings, allowed extensions, size limits
│   │   ├── database.py     # SQLite persistence (history)
│   │   ├── errors.py       # ApiError exception -> JSON error responses
│   │   ├── routers/
│   │   │   ├── recognition.py   # POST /api/recognition, /api/recognition/batch
│   │   │   └── history.py       # GET /api/history
│   │   └── services/
│   │       ├── validation.py           # File exists / type / size checks
│   │       ├── image_preprocessing.py  # OpenCV: grayscale, denoise, threshold
│   │       ├── audio_preprocessing.py  # Decode/resample, noise reduction, Silero VAD
│   │       ├── ocr_service.py          # PaddleOCR + Tesseract
│   │       ├── asr_service.py          # faster-whisper ASR
│   │       ├── text_postprocessing.py  # Cleanup, spacing, capitalization
│   │       └── pipeline.py             # Orchestrates the steps above
│   ├── storage/             # recognition.db (created at runtime)
│   ├── requirements.txt
│   ├── .env.example
│   └── run.py
├── frontend/                # Plain HTML/CSS/JS client
│   ├── index.html
│   ├── style.css
│   └── script.js
├── postman_collection.json  # Import into Postman to test all 3 endpoints
└── README.md
```

## Architecture / Pipeline

**Image files** (PNG, JPG, JPEG, BMP, TIFF)
1. Pre-processing (OpenCV): grayscale conversion → denoising (`fastNlMeansDenoising`) → adaptive thresholding.
2. Text extraction: **PaddleOCR** (default) or **Tesseract** (selectable per request).
3. Post-processing: whitespace/line cleanup, punctuation spacing, sentence capitalization.

**Audio files** (MP3, M4A, WAV, FLAC)
1. Decoding + resampling to 16kHz mono (PyAV — no system ffmpeg required).
2. Noise reduction (`noisereduce`, spectral gating).
3. Voice Activity Detection (**Silero VAD**) — trims non-speech, keeps only speech segments.
4. Text extraction: **faster-whisper** ASR (CPU, int8).
5. Post-processing: same cleanup/formatting step as images.

Every successful recognition (single or from a batch) is saved to a local
SQLite database (`backend/storage/recognition.db`) and is retrievable via
`/api/history`.

## Setup

### 1. Prerequisites
- Python 3.10+ (tested with 3.12)
- **Tesseract OCR binary** installed on your system (required only if you plan to use the `tesseract` model option):
  - Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
  - macOS: `brew install tesseract`
  - Windows: install from https://github.com/UB-Mannheim/tesseract/wiki and set `TESSERACT_CMD` in `backend/.env`

No system `ffmpeg` is required — audio decoding uses PyAV, which bundles its own codec libraries.

### 2. Backend environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # adjust WHISPER_MODEL_SIZE / TESSERACT_CMD if needed
```

> First run will download the PaddleOCR detection/recognition models, the
> Silero VAD model, and the Whisper model (`base` by default) — this needs
> an internet connection the first time only; models are then cached locally
> (typically under `~/.paddleocr`, `~/.cache/torch/hub`, and `~/.cache/huggingface`).

### 3. Run the backend

```bash
cd backend
source venv/bin/activate
python run.py
```

The API will be available at `http://localhost:8000` (Flask's built-in
development server, running with `debug=True` for auto-reload).

### 4. Run the frontend

The frontend is static HTML/CSS/JS — serve it with any static file server:

```bash
cd frontend
python3 -m http.server 5500
```

Open `http://localhost:5500` in your browser. The page has a field for the
API base URL (defaults to `http://localhost:8000`) — change it if your
backend runs elsewhere. CORS is enabled on the backend for all origins.

## API Reference

### 1. `POST /api/recognition` — Single file recognition

**Form-data body:**
| Field | Type | Required | Notes |
|---|---|---|---|
| `file` | file | yes | Image or audio file, max 5MB |
| `model` | text | no (default `paddleocr`) | `paddleocr` or `tesseract` — applies to images only |

**Validations:** file must be present, must have a supported extension
(PNG, JPG, JPEG, BMP, TIFF, MP3, M4A, WAV, FLAC), and must be ≤ 5MB.
Returns `400` on validation failure, `422` if the recognition pipeline itself fails.

**Response `200`:**
```json
{
  "id": 1,
  "filename": "note.jpg",
  "file_size": 84213,
  "file_type": "image",
  "model_used": "paddleocr",
  "recognized_text": "Meeting notes for Monday...",
  "confidence": 0.93,
  "timestamp": "2026-09-28T10:15:32.123456+00:00"
}
```

### 2. `GET /api/history` — Recognition history

Returns every stored recognition, most recent first.

**Response `200`:**
```json
[
  {
    "id": 1,
    "filename": "note.jpg",
    "recognized_text": "Meeting notes for Monday...",
    "confidence": 0.93,
    "timestamp": "2026-09-28T10:15:32.123456+00:00"
  }
]
```

### 3. `POST /api/recognition/batch` — Batch recognition

**Form-data body:**
| Field | Type | Required | Notes |
|---|---|---|---|
| `files` | file (repeat key for each file) | yes | Two or more files |
| `model` | text | no (default `paddleocr`) | Applied to every image file in the batch |

Each file is validated and processed independently; a failure in one file
does not stop the others. Failed files are recorded by filename.

**Response `200`:**
```json
{
  "processed_count": 2,
  "failed_count": 1,
  "results": [
    {
      "id": 2,
      "filename": "page1.png",
      "file_size": 51230,
      "file_type": "image",
      "model_used": "paddleocr",
      "recognized_text": "...",
      "confidence": 0.91,
      "timestamp": "2026-09-28T10:20:00.000000+00:00"
    },
    {
      "id": 3,
      "filename": "voice.wav",
      "file_size": 302144,
      "file_type": "audio",
      "model_used": "faster-whisper",
      "recognized_text": "...",
      "confidence": 0.88,
      "timestamp": "2026-09-28T10:20:04.000000+00:00"
    }
  ],
  "failed": ["corrupted.jpg"]
}
```

## Testing with Postman

Import `postman_collection.json` into Postman. It includes all three
endpoints with a `base_url` collection variable (default
`http://localhost:8000`). For file fields, select actual files from disk in
the Postman UI before sending (Postman collections cannot embed file bytes).

## Model selection

- **Images:** choose between `paddleocr` (default, generally more accurate
  on handwritten/varied layouts) and `tesseract` (faster, lighter, good for
  clean printed text) via the `model` form field, or the dropdown in the
  frontend.
- **Audio:** always uses `faster-whisper`; the `model` field is ignored for
  audio uploads.

## Confidence scores

- **PaddleOCR:** average of per-line recognition confidence scores.
- **Tesseract:** average of per-word confidence scores (from `image_to_data`), normalized to 0–1.
- **faster-whisper:** derived from each segment's average log-probability (`exp(avg_logprob)`), averaged across segments.

## Configuration (`backend/.env`)

| Variable | Default | Description |
|---|---|---|
| `WHISPER_MODEL_SIZE` | `base` | `tiny`, `base`, `small`, `medium`, `large-v3` — bigger is more accurate but slower |
| `TESSERACT_CMD` | *(unset)* | Path to the `tesseract` binary if it's not on your PATH |

## Troubleshooting

- **First request is slow:** models are being downloaded/loaded (PaddleOCR, Silero VAD, Whisper). Subsequent requests reuse the cached, in-memory models.
- **`tesseract` model errors:** make sure the Tesseract OCR binary is installed on the system (see Prerequisites) — `pytesseract` only wraps the binary, it doesn't ship it.
- **413/400 on upload:** file exceeds the 5MB limit or has an unsupported extension.
