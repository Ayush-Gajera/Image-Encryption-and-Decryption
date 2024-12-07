from flask import Flask, render_template, request, send_file, jsonify
import os
import cv2
import numpy as np
from PIL import Image
import io
from werkzeug.utils import secure_filename
import zipfile

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

key_storage = {}  # Dictionary to store keys for encryption and decryption


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/encrypt', methods=['POST'])
def encrypt_image():
    try:
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Save uploaded image
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Read the image and encrypt
        image_input = cv2.imread(filepath, 0)  # Grayscale
        (x1, y) = image_input.shape
        image_input = image_input.astype(float) / 255.0

        mu, sigma = 0, 0.1
        key = np.random.normal(mu, sigma, (x1, y)) + np.finfo(float).eps
        encrypted_image = image_input / key

        # Save encrypted image
        encrypted_filepath = os.path.join(app.config['OUTPUT_FOLDER'], 'encrypted_image.jpg')
        cv2.imwrite(encrypted_filepath, encrypted_image * 255)

        # Save key as a binary file
        key_filepath = os.path.join(app.config['OUTPUT_FOLDER'], 'key.bin')
        with open(key_filepath, 'wb') as key_file:
            key_file.write(key.tobytes())

        # Create a ZIP file
        zip_filepath = os.path.join(app.config['OUTPUT_FOLDER'], 'encrypted_package.zip')
        with zipfile.ZipFile(zip_filepath, 'w') as zipf:
            zipf.write(encrypted_filepath, 'encrypted_image.jpg')
            zipf.write(key_filepath, 'key.bin')

        # Send the ZIP file as response
        return send_file(zip_filepath, as_attachment=True, download_name='encrypted_package.zip')

    except Exception as e:
        return jsonify({'error': f'Encryption failed: {str(e)}'}), 500





@app.route('/decrypt', methods=['POST'])
def decrypt_image():
    try:
        file = request.files['encrypted_image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        key_input = request.form.get('key')
        if not key_input:
            return jsonify({'error': 'Key is missing'}), 400

        # Save uploaded encrypted image
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Convert key from string back to numpy array
        key = np.fromstring(key_input, dtype=float)

        # Read and decrypt
        encrypted_image = cv2.imread(filepath, 0).astype(float) / 255.0
        decrypted_image = encrypted_image * key
        decrypted_image *= 255.0

        # Save decrypted image
        decrypted_filepath = os.path.join(app.config['OUTPUT_FOLDER'], 'decrypted_image.jpg')
        cv2.imwrite(decrypted_filepath, decrypted_image)

        return send_file(decrypted_filepath, as_attachment=True, download_name='decrypted_image.jpg')
    except Exception as e:
        return jsonify({'error': f'Decryption failed: {str(e)}'}), 500


@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    return send_file(file_path, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
