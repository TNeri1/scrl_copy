# backend/app.py

import io
import json
import os
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS, cross_origin
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

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
        
        # Handle background color or gradient
        background_color = layout_data.get('backgroundColor', '#ffffff')
        use_gradient = layout_data.get('useGradientBackground', False)
        
        if use_gradient:
            # For simplicity, we'll just use the first gradient color as background
            # In a real implementation, you'd generate an actual gradient
            gradient_color1 = layout_data.get('gradientColor1', '#3498db')
            background_color = gradient_color1
        
        # Convert hex color to RGB tuple
        if background_color.startswith('#'):
            background_color = background_color[1:]  # Remove the #
            rgb = tuple(int(background_color[i:i+2], 16) for i in (0, 2, 4))
        else:
            rgb = (255, 255, 255)  # Default to white
            
        final_image = Image.new('RGB', (canvas_width, canvas_height), rgb)

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
            
        # Add text elements if any
        if 'textElements' in layout_data:
            try:
                from PIL import ImageDraw, ImageFont
                draw = ImageDraw.Draw(final_image)
                
                for text_element in layout_data['textElements']:
                    text = text_element.get('text', '')
                    x = int(text_element.get('x', 0))
                    y = int(text_element.get('y', 0))
                    width = int(text_element.get('width', 200))
                    height = int(text_element.get('height', 40))
                    font_size = int(text_element.get('fontSize', 20))
                    
                    # Try to use the specified font, fall back to default
                    try:
                        font_name = text_element.get('fontFamily', 'Arial')
                        font = ImageFont.truetype(font_name, font_size)
                    except:
                        # Use default font
                        font = ImageFont.load_default()
                    
                    # Parse color
                    color_hex = text_element.get('color', '#000000')
                    if color_hex.startswith('#'):
                        color_hex = color_hex[1:]  # Remove the #
                        color = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
                    else:
                        color = (0, 0, 0)  # Default to black
                    
                    # Draw text
                    draw.text((x, y), text, fill=color, font=font)
            except Exception as e:
                print(f"Error adding text elements: {e}")

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

@app.route('/api/generate-carousel', methods=['POST'])
@cross_origin()
def generate_carousel():
    print("Received request to generate carousel")
    try:
        layout_data = json.loads(request.form.get('layout'))
        uploaded_files = request.files
        
        template_type = layout_data.get('templateType', 'carousel')
        canvas_width = layout_data.get('canvasWidth', 1080)
        canvas_height = layout_data.get('canvasHeight', 1350 * 3)
        
        # For carousels, determine frame size based on orientation
        if template_type == 'carousel':
            # Vertical carousel (multiple frames stacked)
            frame_height = 1350
            num_frames = canvas_height // frame_height
            frames = []
            
            # Create a full canvas first
            full_image = Image.new('RGB', (canvas_width, canvas_height), 'white')
            
            # Place images on the full canvas
            for item in layout_data['images']:
                image_id = item['id']
                if image_id not in uploaded_files:
                    continue
                
                image_file = uploaded_files[image_id]
                img = Image.open(image_file.stream).convert("RGBA")
                
                width = int(item['width'])
                height = int(item['height'])
                x = int(item['x'])
                y = int(item['y'])
                
                img = img.resize((width, height), Image.Resampling.LANCZOS)
                
                # Paste using the image's alpha channel as a mask
                full_image.paste(img, (x, y), img)
            
            # Slice the full image into frames
            for i in range(num_frames):
                top = i * frame_height
                bottom = top + frame_height
                frame = full_image.crop((0, top, canvas_width, bottom))
                frames.append(frame)
                
            # For now, we'll just return the first frame
            # In a real implementation, we would zip all frames and return them
            buf = io.BytesIO()
            frames[0].save(buf, format='PNG')
            buf.seek(0)
            
            return send_file(
                buf,
                mimetype='image/png',
                as_attachment=True,
                download_name=f'carousel-frame-1.png'
            )
                
        elif template_type == 'panoramic':
            # Horizontal carousel (side by side frames)
            frame_width = 1080
            num_frames = canvas_width // frame_width
            frames = []
            
            # Create a full canvas first
            full_image = Image.new('RGB', (canvas_width, canvas_height), 'white')
            
            # Place images on the full canvas
            for item in layout_data['images']:
                image_id = item['id']
                if image_id not in uploaded_files:
                    continue
                
                image_file = uploaded_files[image_id]
                img = Image.open(image_file.stream).convert("RGBA")
                
                width = int(item['width'])
                height = int(item['height'])
                x = int(item['x'])
                y = int(item['y'])
                
                img = img.resize((width, height), Image.Resampling.LANCZOS)
                
                # Paste using the image's alpha channel as a mask
                full_image.paste(img, (x, y), img)
            
            # Slice the full image into frames
            for i in range(num_frames):
                left = i * frame_width
                right = left + frame_width
                frame = full_image.crop((left, 0, right, canvas_height))
                frames.append(frame)
                
            # For now, we'll just return the first frame
            # In a real implementation, we would zip all frames and return them
            buf = io.BytesIO()
            frames[0].save(buf, format='PNG')
            buf.seek(0)
            
            return send_file(
                buf,
                mimetype='image/png',
                as_attachment=True,
                download_name=f'panoramic-frame-1.png'
            )
        else:
            return {"error": "Unsupported template type for carousel generation"}, 400
            
    except Exception as e:
        print(f"An error occurred in generate_carousel: {e}")
        return str(e), 500

@app.route('/api/test', methods=['GET'])
def test():
    """Simple endpoint to test if the server is responding."""
    return {"status": "success", "message": "Backend server is running correctly!"}, 200

if __name__ == '__main__':
    # For local development
    port = int(os.environ.get('PORT', 8000))
    print(f"Starting Flask server on port {port}...")
    app.run(host='0.0.0.0', debug=True, port=port)