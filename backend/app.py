# backend/app.py

import io
import json
from flask import Flask, request, send_file
from flask_cors import CORS
from PIL import Image

# Initialize the Flask App
app = Flask(__name__)
# Enable Cross-Origin Resource Sharing
CORS(app)

@app.route('/api/generate', methods=['POST'])
def generate_image():
    """
    This endpoint receives image files and layout data,
    composites them into a single image, and returns it.
    """
    try:
        # --- 1. Receive Data from Frontend ---
        # The layout is sent as a JSON string in a form field
        layout_data = json.loads(request.form.get('layout'))
        # The image files are accessed from request.files
        uploaded_files = request.files

        # --- 2. Create the Base Canvas ---
        canvas_width = layout_data.get('canvasWidth', 1080)
        canvas_height = layout_data.get('canvasHeight', 1350)
        canvas_color = layout_data.get('canvasColor', 'white')

        # Create a new blank image (the canvas)
        final_image = Image.new('RGB', (canvas_width, canvas_height), canvas_color)

        # --- 3. Composite Images onto the Canvas ---
        # Iterate through each image defined in the layout
        for item in layout_data['images']:
            image_id = item['id']
            if image_id not in uploaded_files:
                # If an image specified in the layout wasn't uploaded, skip it
                continue
            
            # Open the uploaded image file
            image_file = uploaded_files[image_id]
            img = Image.open(image_file.stream)

            # Get dimensions and position from layout
            # We use int() to ensure they are whole numbers for pixels
            width = int(item['width'])
            height = int(item['height'])
            x = int(item['x'])
            y = int(item['y'])

            # Resize the image to the specified dimensions
            # LANCZOS is a high-quality downsampling filter
            img = img.resize((width, height), Image.Resampling.LANCZOS)
            
            # Paste the resized image onto the canvas at the specified coordinates
            final_image.paste(img, (x, y))

        # --- 4. Send the Final Image Back ---
        # Save the final image to a memory buffer instead of a file on disk
        buf = io.BytesIO()
        final_image.save(buf, format='PNG')
        buf.seek(0) # Go to the beginning of the buffer

        # Send the buffer as a file in the HTTP response
        return send_file(
            buf,
            mimetype='image/png',
            as_attachment=True,
            download_name='collage.png'
        )

    except Exception as e:
        # Print error for debugging and return an error response
        print(f"An error occurred: {e}")
        return str(e), 500


# To run the server:
# In your terminal, navigate to the `backend` directory and run:
# flask --app app run
if __name__ == '__main__':
    app.run(debug=True, port=5000)