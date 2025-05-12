// --- DOM Elements for Book Finder ---
const startCameraButton = document.getElementById('start-camera-button');
const captureButton = document.getElementById('capture-button');
const videoFeed = document.getElementById('video-feed');
const captureCanvas = document.getElementById('capture-canvas');
const imageDisplayArea = document.getElementById('image-display-area');
const imagePreview = document.getElementById('image-preview');
const previewPlaceholder = document.getElementById('preview-placeholder');
const fileInput = document.getElementById('file-input');
// const uploadLabelButton = document.querySelector('.upload-label-button'); // Not strictly needed for listener
const findBookButton = document.getElementById('find-book-button');
const resultOutput = document.getElementById('result-output');
const backButton = document.getElementById('back-button'); // Keep if needed
const profilePicture = document.getElementById('profile-picture'); // Keep if needed

// --- State ---
let currentImageBlob = null; // Stores the captured/uploaded image Blob/File
let mediaStream = null; // Stores the camera stream

// --- Helper Functions ---

/**
 * Stops the current media stream tracks.
 */
function stopMediaStream() {
    if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
        mediaStream = null;
        console.log("Camera stream stopped.");
    }
    videoFeed.style.display = 'none';
    videoFeed.srcObject = null; // Release video object
    captureButton.style.display = 'none';
    startCameraButton.style.display = 'inline-flex'; // Show start button again
}

/**
 * Clears the image preview, resets state, and disables find button.
 */
function clearPreview() {
    currentImageBlob = null;
    imagePreview.src = '#';
    imagePreview.style.display = 'none';
    previewPlaceholder.style.display = 'inline'; // Show placeholder text
    fileInput.value = null; // Reset file input
    findBookButton.disabled = true;
    console.log("Preview cleared.");
}

/**
 * Sets the image preview from a Blob/File object.
 * @param {Blob|File} blob The image data.
 */
function setImagePreview(blob) {
    if (!blob || !blob.type.startsWith('image/')) {
        console.error("Invalid blob provided for preview:", blob);
        clearPreview();
        alert("Failed to process image. Please try again.");
        return;
    }

    currentImageBlob = blob; // Store the valid blob/file

    // Use URL.createObjectURL for efficient preview generation
    const objectURL = URL.createObjectURL(blob);
    imagePreview.onload = () => {
        // Optional: Revoke previous object URL if one exists to free memory
        // if (imagePreview.src.startsWith('blob:')) { URL.revokeObjectURL(imagePreview.src); }
        console.log("Preview image loaded.");
    }
    imagePreview.onerror = () => {
        console.error("Error loading object URL into image preview.");
        clearPreview();
        alert("Sorry, couldn't display that image preview.");
    }
    imagePreview.src = objectURL;
    imagePreview.style.display = 'block'; // Show image
    previewPlaceholder.style.display = 'none'; // Hide placeholder
    findBookButton.disabled = false; // Enable the find button
    console.log("Preview set, Find button enabled.");
}

/**
 * Updates the result area with streamed content.
 * @param {string} htmlContent - HTML content (potentially Markdown parsed).
 * @param {boolean} isFirstChunk - True if this is the first piece of data.
 */
function updateResultArea(htmlContent, isFirstChunk) {
    console.log("Received data type:", typeof htmlContent); // Should now log 'string'
    console.log("Received data value:", htmlContent);      // Should now log the text

    if (isFirstChunk) {
        resultOutput.innerHTML = ''; // Clear loading/previous content
        resultOutput.classList.remove('loading', 'error');
    }

    // This line should correctly receive the string now
    resultOutput.innerHTML = htmlContent;

    // Apply syntax highlighting if hljs is available
    if (typeof hljs !== 'undefined') {
        resultOutput.querySelectorAll('pre code').forEach((block) => {
            if (!block.classList.contains('hljs')) {
                hljs.highlightElement(block);
            }
        });
    }
     // Optional scroll
     // resultOutput.scrollTop = resultOutput.scrollHeight;
}

/** Sets the result area to a loading state. */
function showResultLoading() {
    resultOutput.innerHTML = 'Analyzing image and finding book info...';
    resultOutput.className = 'result-display-area loading'; // Reset classes and add loading
}

/**
 * Sets the result area to an error state.
 * @param {string} message - The error message.
 */
function showResultError(message) {
    resultOutput.innerHTML = `Error: ${message}`;
    resultOutput.className = 'result-display-area error'; // Reset classes and add error
}

/** Handles UI updates when the API stream completes (success or error). */
function handleResultComplete() {
    findBookButton.disabled = false; // Re-enable the find button
    console.log("Gemini stream finished.");
}


// --- Event Listeners ---

// Start Camera Button
startCameraButton.addEventListener('click', async () => {
    console.log("Start camera clicked.");
    stopMediaStream(); // Stop any existing stream first
    clearPreview(); // Clear existing preview/blob

    const constraints = {
        video: {
            facingMode: 'environment', // Prioritize rear camera
            width: { ideal: 1280 }, // Request preferred resolution
            height: { ideal: 720 }
        },
        audio: false
    };

    try {
        mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
        console.log("Camera stream obtained.");
        videoFeed.srcObject = mediaStream;
        videoFeed.style.display = 'block';
        previewPlaceholder.style.display = 'none'; // Hide placeholder while video is active
        imagePreview.style.display = 'none'; // Hide static preview if shown
        startCameraButton.style.display = 'none'; // Hide start button
        captureButton.style.display = 'inline-flex'; // Show capture button
        findBookButton.disabled = true; // Disable find while camera active
    } catch (err) {
        console.error("Error accessing camera:", err);
        mediaStream = null; // Ensure stream is null on error
        videoFeed.style.display = 'none';
        captureButton.style.display = 'none';
        startCameraButton.style.display = 'inline-flex'; // Ensure start is visible
        previewPlaceholder.style.display = 'inline'; // Show placeholder again
        alert(`Could not access camera: ${err.name}\n\n${err.message}\n\nPlease ensure permission is granted and no other app is using the camera.`);
    }
});

// Capture Button
captureButton.addEventListener('click', () => {
    if (!mediaStream || !videoFeed.videoWidth) {
        console.error("Capture clicked but stream or video not ready.");
        return;
    }
    console.log("Capture button clicked.");

    // Set canvas dimensions to match video feed display size
    captureCanvas.width = videoFeed.videoWidth;
    captureCanvas.height = videoFeed.videoHeight;

    // Draw the current video frame onto the canvas
    const context = captureCanvas.getContext('2d');
    context.drawImage(videoFeed, 0, 0, captureCanvas.width, captureCanvas.height);

    // Convert canvas to Blob (more efficient than DataURL for sending)
    captureCanvas.toBlob(blob => {
        if (blob) {
            console.log(`Canvas captured to Blob. Size: ${blob.size}, Type: ${blob.type}`);
            // Create a File object for easier handling/naming (optional)
            const capturedFile = new File([blob], `capture-${Date.now()}.png`, { type: blob.type });
            setImagePreview(capturedFile); // Show preview, enable find button
        } else {
            console.error("Canvas toBlob resulted in null.");
            clearPreview();
            alert("Failed to capture image from camera.");
        }
        // Stop the camera stream AFTER capture and preview are set
        stopMediaStream();
    }, 'image/png'); // Specify format (png or jpeg)

});

// File Input Change (Upload)
fileInput.addEventListener('change', (event) => {
    const file = event.target.files[0];
    console.log("File input changed.");
    stopMediaStream(); // Stop camera if it was running

    if (file && file.type.startsWith('image/')) {
        console.log(`File selected: ${file.name}, Size: ${file.size}, Type: ${file.type}`);
        setImagePreview(file); // Show preview, enable find button, stores the file in currentImageBlob
    } else if (file) {
        console.warn("Invalid file type selected:", file.type);
        clearPreview();
        alert("Please select a valid image file (e.g., JPG, PNG, GIF, WEBP).");
    } else {
        console.log("File input cleared or no file selected.");
        // Don't clear preview if they just cancelled the dialog without selecting
        // clearPreview();
    }
});

// Find Book Button
findBookButton.addEventListener('click', () => {
    if (!currentImageBlob) {
        alert("Please capture or upload an image first.");
        return;
    }
    console.log("Find book button clicked.");

    findBookButton.disabled = true; // Disable during API call
    showResultLoading(); // Show loading state in result area

    const fixedPrompt = "tell me about this book in details"; // The required prompt

    // Check if the API function is available
    if (typeof window.streamChatResponse === 'function') {
        window.streamChatResponse(fixedPrompt, currentImageBlob, resultOutput, {
            onData: updateResultArea,
            onError: (targetElement, errorMsg) => { // Pass targetElement explicitly if needed by error func
                showResultError(errorMsg); // Display error in result area
                handleResultComplete(); // Still need to re-enable button on error
            },
            onComplete: (targetElement) => { // Pass targetElement explicitly if needed by complete func
                // Don't re-enable here if error handles it, or check state
                 handleResultComplete();
            }
        });
    } else {
        console.error("Error: streamChatResponse function is not defined.");
        showResultError("Book finding function is unavailable. Please refresh.");
        findBookButton.disabled = false; // Re-enable button
    }
});


// --- Initial Setup ---
document.addEventListener('DOMContentLoaded', () => {
    clearPreview(); // Ensure initial state is clean
    stopMediaStream(); // Ensure camera isn't active on load (e.g., after refresh)

    // Keep Back button and Profile Picture listeners if they are used
    if (backButton) {
        backButton.addEventListener('click', () => window.history.back());
    }
    if (profilePicture) {
        // Add listener for profile picture if it opens a menu, etc.
        // profilePicture.addEventListener('click', openSidePanel); // Example
    }
});