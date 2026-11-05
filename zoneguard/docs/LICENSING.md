# Commercial Licensing Review — Dependencies & Models

> Engineering review only. **Have counsel confirm before commercial launch.** Licences were taken from
> each project's published licence for the versions pinned in this repository.

## AI models & data

| Asset | Licence | Use in ZoneGuard | Commercial SaaS notes |
|---|---|---|---|
| **YOLOX** code & official ONNX weights (Megvii, release 0.1.1rc0: nano / tiny / s) | **Apache-2.0** | Person detection (and the generic COCO "knife" class in the experimental weapon mode) | Permissive. Keep the licence and NOTICE, state changes. Weights are downloaded at install time and SHA-256 verified; they are not committed. |
| COCO 2017 (training data of the YOLOX weights) | Annotations CC BY 4.0; images under individual Flickr licences | Not redistributed; only the trained weights are used | ⚖ Industry practice treats COCO-trained weights as usable commercially, but this is unsettled; obtain legal view, and consider retraining/fine-tuning on owned data for production. |
| **Not used:** Ultralytics YOLOv5/v8/v11 | AGPL-3.0 (or paid enterprise licence) | — | Deliberately avoided: AGPL network-use clause could require releasing SaaS source. |
| Weapon / face-covering models | — | **None bundled.** Interfaces accept customer-supplied ONNX models | Any future model needs licence + training-data provenance review and documented validation. |
| `samples/vtest.avi` (OpenCV sample clip, downloaded by script) | Provenance/licence **not documented** by OpenCV | Local development & automated tests only | ⚖ Do not redistribute, demo publicly or ship. Replace with owned, consented footage. |

## Python (backend, vision, edge)

| Package | Version | Licence | Notes |
|---|---|---|---|
| fastapi | 0.115.12 | MIT | |
| starlette | 0.46.2 | BSD-3-Clause | |
| uvicorn | 0.34.2 | BSD-3-Clause | |
| pydantic / pydantic-settings | 2.11.4 / 2.9.1 | MIT | |
| SQLAlchemy | 2.0.40 | MIT | |
| alembic | 1.15.2 | MIT | |
| **psycopg / psycopg-binary** | 3.2.9 | **LGPL-3.0** (binary wheel bundles libpq — PostgreSQL licence — and OpenSSL — Apache-2.0) | Used unmodified as a dynamically imported library: generally compatible with proprietary SaaS. If distributing images to customers, include the LGPL text and allow replacement of the library (it is a separate, replaceable package). |
| argon2-cffi | 23.1.0 | MIT | |
| cryptography | 44.0.3 | Apache-2.0 OR BSD-3-Clause | |
| pyotp | 2.9.0 | MIT | |
| python-multipart | 0.0.20 | Apache-2.0 | |
| email-validator | 2.2.0 | Unlicense | |
| psutil | 7.0.0 | BSD-3-Clause | |
| tzdata | 2025.2 | Apache-2.0 | |
| numpy | 2.5.4 | BSD-3-Clause | |
| **opencv-python-headless** | 5.0.0.93 | OpenCV: Apache-2.0; **wheel bundles FFmpeg (LGPL-2.1+)** | The edge agent image is distributed to customer premises → include FFmpeg LGPL notices and source offer/links per LGPL; do not statically relink a modified FFmpeg. ⚖ Confirm no GPL-only codecs are enabled in the wheel build. |
| onnxruntime | 1.31.1 | MIT | |
| httpx | 0.28.1 | BSD-3-Clause | |
| *dev:* pytest (MIT), aiosmtpd (Apache-2.0) | | | Not shipped. |

## JavaScript (dashboard)

| Package | Licence |
|---|---|
| next 15.5.29 | MIT |
| react / react-dom 19.1.10 | MIT |
| tailwindcss 3.4.19 | MIT |
| shadcn/ui patterns (components re-implemented in `src/components/ui`) | MIT |
| @radix-ui/react-slot | MIT |
| class-variance-authority | Apache-2.0 |
| clsx, tailwind-merge | MIT |
| lucide-react | ISC |
| *dev:* typescript (Apache-2.0), vitest (MIT), @testing-library/* (MIT), jsdom (MIT), @playwright/test (Apache-2.0) | Not shipped to browsers. |

## Infrastructure

| Component | Licence | Notes |
|---|---|---|
| PostgreSQL 16 | PostgreSQL Licence (permissive) | |
| Mailpit | MIT | Development only. |
| Docker base images (python:3.12-slim, node:22-alpine, postgres:16-alpine) | Various OSS (Debian/Alpine packages) | Generate an SBOM (e.g. `syft`) per release; review GPL components in base layers before distributing images. |

## Actions before commercial launch

1. Generate SBOMs for every image; add `THIRD_PARTY_NOTICES` to the edge-agent image (Apache NOTICE for YOLOX/ONNX Runtime, LGPL for FFmpeg/psycopg).
2. Legal opinion on COCO-trained weights; plan for a model trained on owned / licensed data.
3. Replace `vtest.avi` with owned, consented staged footage.
4. Re-run this review whenever dependencies or models change (CI licence scanning recommended).
