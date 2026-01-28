// Static Background Image Configuration
// Set your background image URL here
const BACKGROUND_IMAGE_URL = '/config/bg.jpg'; // Local image from config directory

// Set static background
(function() {
  'use strict';
  
  if (!BACKGROUND_IMAGE_URL || BACKGROUND_IMAGE_URL.trim() === '') {
    return; // No background configured
  }
  
  function setBackground() {
    const backgroundElement = document.createElement('div');
    backgroundElement.id = 'static-background';
    backgroundElement.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      z-index: -1;
      background-size: cover;
      background-position: center;
      background-repeat: no-repeat;
    `;
    document.body.insertBefore(backgroundElement, document.body.firstChild);
    
    // Preload image to check if it loads successfully
    const img = new Image();
    img.onload = function() {
      backgroundElement.style.backgroundImage = `url("${BACKGROUND_IMAGE_URL}")`;
      console.log('Background image loaded successfully:', BACKGROUND_IMAGE_URL);
    };
    img.onerror = function() {
      console.error('Failed to load background image:', BACKGROUND_IMAGE_URL);
      console.error('Make sure the file exists at:', BACKGROUND_IMAGE_URL);
      console.error('Try accessing it directly in your browser to verify the path is correct.');
    };
    img.src = BACKGROUND_IMAGE_URL;
  }
  
  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setBackground);
  } else {
    setBackground();
  }
})();
