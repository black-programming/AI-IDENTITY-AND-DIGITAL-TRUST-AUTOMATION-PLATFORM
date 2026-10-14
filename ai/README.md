# AI, OCR & Synthetic Data Guidelines

## 1. Zero Real PII Rule
In accordance with Master Roadmap Rule 6:
> **"Use synthetic identity documents during development."**

Under no circumstances should real passports, national IDs, or driver's licenses be uploaded or committed to this repository. All tests and demonstration datasets must use generated synthetic documents containing visible watermarks.

## 2. Supported Synthetic Document Types
1. **National ID (`SYNTH_NAT_ID_V1`):** Specimen `SYNTH_NAT_ID_SAMPLE_01` in `synthetic_data/spec_templates.json`.
2. **Driver's License (`SYNTH_DL_V1`):** Specimen `SYNTH_DL_VALID_01`.
3. **Passport Bio-Data (`SYNTH_PASS_TD3`):** MRZ TD3 formatted specimen.

## 3. OCR Pipeline Integration Roadmap (Phase 8)
- `PaddleOCR` and `Tesseract` will process synthetic images loaded from Supabase quarantine storage.
- Extracted text will be matched against document field schemas with confidence scoring ($0.0 - 1.0$) and bounding boxes.
- Low-confidence extractions ($< 0.85$) will escalate to the Human Reviewer queue (`Under Review`).
