import os
import time
import requests
import shutil
from flask import Flask, render_template, request, jsonify, send_from_directory
import subprocess
import shlex

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'static/uploads'
PROCESSED_FOLDER = 'static/processed'
SSOCR_PATH = os.path.abspath('./ssocr') # Assuming ssocr is in the root

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/proxy-image')
def proxy_image():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # Save locally to serve
        filename = "downloaded_image.jpg"
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        with open(filepath, 'wb') as f:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, f)

        return jsonify({'url': f"/{filepath}", 'path': filepath})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/process', methods=['POST'])
def process():
    data = request.json
    image_path = data.get('image_path')

    # ssocr parameters
    # crop X Y W H
    crop = data.get('crop') # {'x':, 'y':, 'width':, 'height':}

    # Options
    threshold = data.get('threshold', -1)
    digits = data.get('digits', -1)
    invert = data.get('invert', False)
    extra_options = data.get('extra_options', '')
    extra_args = data.get('extra_args', '')
    grayscale = data.get('grayscale', True) # Default to True if not present (legacy safety)
    make_mono = data.get('make_mono', True)
    remove_isolated = data.get('remove_isolated', True)


    # Construct ssocr command
    # We will use temporary file for debug image if requested

    # Real ssocr execution
    if not os.path.exists(SSOCR_PATH):
         return jsonify({'error': 'ssocr binary missing'}), 500

    cmd = [SSOCR_PATH]

    # Insert user provided extra options safely at the beginning (e.g. flags)
    if extra_options:
        try:
            cmd.extend(shlex.split(extra_options))
        except Exception:
            pass

    if threshold != -1:
        cmd.extend(['-t', str(threshold)])

    if digits != -1:
        cmd.extend(['-d', str(digits)])

    # User requested modifier: -c digits
    cmd.extend(['-c', 'digits'])

    # Crop command
    if crop:
        # ssocr crop X Y W H
        crop_w = int(crop['width'])
        crop_h = int(crop['height'])
        cmd.extend(['crop', str(int(crop['x'])), str(int(crop['y'])), str(crop_w), str(crop_h)])



    # User requested modifiers: toggleable via UI
    if grayscale:
        cmd.append('grayscale')
    if make_mono:
        cmd.append('make_mono')
    if remove_isolated:
        cmd.append('remove_isolated')

    if invert:
        cmd.append('invert')

    # Append user provided extra arguments safely
    if extra_args:
        try:
            cmd.extend(shlex.split(extra_args))
        except Exception:
            pass # Ignore malformed strings for now, or could log warning

    # Process only to get debug image?
    # For visualization, we might want to get the processed image.
    # ssocr -D returns the image.
    # Let's say we want to see what ssocr sees.

    debug_filename = "debug_image.png"
    debug_path = os.path.join(PROCESSED_FOLDER, debug_filename)

    # We need to run ssocr to get the text AND the image.
    # ssocr writes image to file with -D <file> or -o <file>
    # If we use -o, it writes processed image.

    cmd.extend(['-o', debug_path])

    # Finally the input image
    cmd.append(image_path)

    try:
        # Run command
        result = subprocess.run(cmd, capture_output=True, text=True)

        text_output = result.stdout.strip()
        error_output = result.stderr.strip()

        response = {
            'text': text_output if text_output else "No text recognized",
            'command': ' '.join(cmd)
        }

        if os.path.exists(debug_path):
            response['debug_image'] = f"/{debug_path}"

        if result.returncode != 0:
             # ssocr failed or returned warning
             # If we have recognized text, we treat it as partial success and DO NOT return 'error' to UI
             # unless the text is empty.
             if not text_output:
                 response['error'] = 'ssocr returned error'
                 response['details'] = error_output

             # If text_output is present despite error, we just return it.
             # The UI uses presence of 'error' key to decide display style.
             return jsonify(response), 200 # Return 200 so UI can process the JSON response

        return jsonify(response)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
