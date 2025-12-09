This project performs Optical Character Recognition (OCR) and Layout Analysis on documents (images) to extract text, tables, and figures.
It uses **Tesseract** for text extraction and **PaddleOCR/PaddleX** for layout analysis (detecting and cropping tables, charts, images).

## Features

- **Text Extraction**: Extracts text from images using Tesseract with adaptive thresholding for better results on colored backgrounds.
- **Layout Analysis**: Detects non-text elements (Tables, Charts, Figures, Formulas).
- **Layout-Aware Masking**: Automatically masks out non-text elements before OCR to prevent garbage text generation from tables/charts.
- **Element Extraction**: Saves detected tables, charts, and images as separate files.

## Prerequisites

### 1. System Dependencies (Tesseract OCR)
**macOS:**
```bash
brew install tesseract
brew install tesseract-lang  
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-vie  
```

**Windows:**
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

### 2. Python Environment

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/endy1002/CS418-KnowledgeGraph.git
    cd CS418-KnowledgeGraph
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # mac/Linux
    # .venv\Scripts\activate   # Win
    ```

3.  **Install Python dependencies:**
    ```bash
    pip install pytesseract pillow opencv-python paddlepaddle paddleocr "paddlex[ocr]"
    ```
    *Note: `paddlepaddle` installation may vary based on your OS/GPU. See [PaddlePaddle website](https://www.paddlepaddle.org.cn/en) if issues arise.*

## Usage

### Running the Main Script

The main script processes all images found in `assets/test/`.

1.  **Place images** you want to process in `assets/test/`.
2.  **Run the script:**
    ```bash
    python src/main.py
    ```

### Output

Results are saved in the `results/` directory, organized by filename:

```text
results/
  ├── [filename]/
  │     ├── [filename].txt            # Cleaned extracted text
  │     └── extracted_images/         # Extracted tables, charts, figures
  │           ├── region_0_img_0.jpg
  │           ├── region_0_table_0.html
  │           └── ...
```
