# backend/app.py

import io
import json
from flask import Flask, request, send_file
from flask_cors import CORS, cross_origin
from PIL import Image

app = Flask(__name__)
CORS(app)

@app.route('/api/generate', methods=['POST'])
@cross_origin()
def generate_image():
    print("Received request to generate image")
    try:
        # Debug information
        print("Request headers:", dict(request.headers))
        print("Request form keys:", list(request.form.keys()))
        print("Request files keys:", list(request.files.keys()))
        
        layout_data = json.loads(request.form.get('layout'))
        uploaded_files = request.files
        print("Layout data:", layout_data)

        canvas_width = layout_data.get('canvasWidth', 1080)
        canvas_height = layout_data.get('canvasHeight', 1350)
        final_image = Image.new('RGB', (canvas_width, canvas_height), 'white')

        for item in layout_data['images']:
            image_id = item['id']
            if image_id not in uploaded_files:
                continue
            
            image_file = uploaded_files[image_id]
            img = Image.open(image_file.stream).convert("RGBA") # Use RGBA for pasting transparent images

            width = int(item['width'])
            height = int(item['height'])
            x = int(item['x'])
            y = int(item['y'])

            img = img.resize((width, height), Image.Resampling.LANCZOS)
            
            # Paste using the image's own alpha channel as a mask
            final_image.paste(img, (x, y), img)

        buf = io.BytesIO()
        final_image.save(buf, format='PNG')
        buf.seek(0)

        return send_file(
            buf,
            mimetype='image/png',
            as_attachment=True,
            download_name='collage.png'
        )

    except Exception as e:
        print(f"An error occurred: {e}")
        return str(e), 500

@app.route('/api/test', methods=['GET'])
def test():
    """Simple endpoint to test if the server is responding."""
    return {"status": "success", "message": "Backend server is running correctly!"}, 200

if __name__ == '__main__':
    print("Starting Flask server on port 8000...")
    app.run(debug=True, port=8000)