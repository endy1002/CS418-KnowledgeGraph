### Installing Tesseract OCR
**macOS:**
```bash
brew install tesseract
brew install tesseract-lang  # For Vietnamese language support
```
**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-vie  # Vietnamese language data
```
**Windows:**
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/endy1002/CS418-KnowledgeGraph.git
   cd CS418-KnowledgeGraph
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv .venv
   ```

3. **Activate the virtual environment:**
   **macOS/Linux:**
   ```bash
   source .venv/bin/activate
   ```

   **Windows:**
   ```bash
   .venv\Scripts\activate
   ```

4. **Install required Python packages:**
   ```bash
   pip install pytesseract pillow
   ```

## Usage

Run the OCR model on an image:

```bash
python src/model.py [filename]
```

**Examples:**
```bash
# Process a specific image from the assets folder
python src/model.py 2.png
```

