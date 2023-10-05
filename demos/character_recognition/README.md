- Text extraction plugins are responsible for extracting text from images. Each plugin implements a different text extraction method or algorithm.

Example plugins:
- OCR Plugin: Utilizes Optical Character Recognition (OCR) to extract text from images.
- Template Matching Plugin: Performs template matching to locate specific patterns of text.
- Deep Learning Plugin: Uses deep learning models for text recognition.
- Handwritten Text Recognition Plugin: Specialized for recognizing handwritten text.

Each plugin provides a standardized interface with methods like initialize, extract_text, and cleanup.