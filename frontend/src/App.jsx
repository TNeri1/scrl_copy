// frontend/src/App.jsx

import React, { useState } from 'react';
import { Rnd } from 'react-rnd'; // Import Rnd
import './App.css';
import axios from 'axios';

function App() {
  const [images, setImages] = useState([]);
  // We need to store the original File objects to send to the backend
  const [sourceFiles, setSourceFiles] = useState({});
  const [generatedImageUrl, setGeneratedImageUrl] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleFileChange = (event) => {
    const files = Array.from(event.target.files);
    const newImages = [];
    const newSourceFiles = { ...sourceFiles };

    files.forEach((file, index) => {
      const id = `image_${Date.now()}_${index}`;
      newImages.push({
        id: id,
        src: URL.createObjectURL(file), // Create a temporary URL for preview
        x: 50 + index * 20,
        y: 50 + index * 20,
        width: 300,
        height: 200,
      });
      newSourceFiles[id] = file; // Store the original file object
    });

    setImages([...images, ...newImages]);
    setSourceFiles(newSourceFiles);
  };

  // This function updates state when an image is moved or resized
  const onLayoutChange = (id, d, ref) => {
    setImages(currentImages =>
      currentImages.map(img =>
        img.id === id
          ? { ...img, x: d.x, y: d.y, width: ref.offsetWidth, height: ref.offsetHeight }
          : img
      )
    );
  };

  const handleGenerateClick = async () => {
    setIsLoading(true);
    setGeneratedImageUrl(null);

    const formData = new FormData();
    const layout = {
      canvasWidth: 1080, // Final image width
      canvasHeight: 1350, // Final image height
      images: images.map(img => ({
        id: img.id,
        x: Math.round(img.x * 2), // Multiply by 2 because our display canvas is half size
        y: Math.round(img.y * 2),
        width: Math.round(img.width * 2),
        height: Math.round(img.height * 2),
      })),
    };
    formData.append('layout', JSON.stringify(layout));

    images.forEach(img => {
      formData.append(img.id, sourceFiles[img.id]);
    });

    try {
      const response = await axios.post('http://localhost:8000/api/generate', formData, {
        responseType: 'blob',
      });
      const url = URL.createObjectURL(response.data);
      setGeneratedImageUrl(url);
    } catch (error) {
      console.error("Error generating image:", error);
      alert("Failed to generate image. Is the backend server running?");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <div className="controls">
        <h2>Scrapbook Studio</h2>
        <p>1. Upload your photos to begin.</p>
        <input type="file" multiple onChange={handleFileChange} accept="image/*" />
        <p>2. Drag and resize them on the canvas.</p>
        <p>3. Generate your final image.</p>
        <button onClick={handleGenerateClick} disabled={images.length === 0 || isLoading}>
          {isLoading ? 'Generating...' : 'Generate Collage'}
        </button>
        {generatedImageUrl && (
          <div className="result">
            <h3>Your collage is ready!</h3>
            <img src={generatedImageUrl} alt="Generated collage" className="result-preview" />
            <a href={generatedImageUrl} download="scrapbook-collage.png">Download Image</a>
          </div>
        )}
      </div>
      <div className="canvas-container">
        <div className="canvas">
          {images.map(img => (
            <Rnd
              key={img.id}
              className="image-item"
              size={{ width: img.width, height: img.height }}
              position={{ x: img.x, y: img.y }}
              onDragStop={(e, d) => onLayoutChange(img.id, d, { offsetWidth: img.width, offsetHeight: img.height })}
              onResizeStop={(e, dir, ref, delta, pos) => onLayoutChange(img.id, pos, ref)}
              bounds="parent"
            >
              <img src={img.src} alt="" style={{ width: '100%', height: '100%', pointerEvents: 'none' }}/>
            </Rnd>
          ))}
        </div>
      </div>
    </div>
  );
}

export default App;