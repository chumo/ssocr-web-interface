# SSOCR Web Interface

A web-based interface for **SSOCR** (Seven Segment Optical Character Recognition), allowing users to process images of seven-segment displays and extract digits.

## Features
- **Interactive UI**: Upload images or load from URL.
- **Image Preprocessing**: Crop, threshold, and inverting.
- **SSOCR integration**: Full control over ssocr commands (Grayscale, Mono, etc).
- **Dockerized**: Easy deployment.

## Running with Docker

You can run the application using Docker Compose.

### Prerequisites
- Docker
- Docker Compose

### Steps

1.  **Build and Run**:
    ```bash
    docker compose up --build
    ```

2.  **Access the App**:
    Open your browser and navigate to: [http://localhost:5000](http://localhost:5000)

3.  **Stop**:
    Press `Ctrl+C` or run:
    ```bash
    docker compose down
    ```

## Development

To run locally without Docker:

1.  **Install system dependencies** (`ssocr` build requirements):
    ```bash
    sudo apt-get install libimlib2-dev libx11-dev build-essential
    ```

2.  **Install Python dependencies**:
    ```bash
    pip install flask requests sh
    ```

3.  **Run**:
    ```bash
    python app.py
    ```
