// ui-utils.js

// --- DOM Elements ---
const chatMessagesContainer = document.getElementById('chat-messages');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('prompt');
const sendButton = document.getElementById('send-button');
const initialGreeting = document.querySelector('.initial-greeting'); // Get reference to greeting

// --- State ---
let isFirstUserMessage = true; // Flag to track if it's the first message

// --- UI Update Functions ---

// ... (addMessage, showLoadingIndicator, updateBotMessageContent, showStreamError, handleStreamCompletion, scrollToBottom, setSendButtonState functions remain the same as before) ...

/**
 * Adds a message bubble to the chat.
 * @param {string} text - The message text (can be empty for loading state).
 * @param {'user' | 'bot' | 'error'} sender - The sender type.
 * @param {string | null} elementId - Optional ID for the message element.
 * @returns {HTMLElement} The created message element.
 */
function addMessage(text, sender, elementId = null) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', sender);
    if (elementId) {
        messageElement.id = elementId;
    }

    // Handle initial content (use marked for bot, plain text otherwise)
    if (sender === 'bot' && text && typeof marked !== 'undefined') {
        // Ensure message content doesn't get parsed if it's meant to be simple text initially
         if (elementId && elementId.startsWith('bot-message-')) {
            // It's a loading or error message, set text directly first
            messageElement.textContent = text;
         } else {
             messageElement.innerHTML = marked.parse(text);
         }
    } else {
        // Basic text content for user, error, or initial bot message before parsing
        messageElement.textContent = text;
    }

    chatMessagesContainer.appendChild(messageElement);
    scrollToBottom(); // Scroll after adding ANY message
    return messageElement;
}

/**
 * Adds a bot message bubble specifically for the loading state.
 * @param {string} elementId - The ID to assign to the loading message element.
 * @returns {HTMLElement} The created loading message element.
 */
function showLoadingIndicator(elementId) {
    const loadingElement = addMessage('', 'bot', elementId); // Start with empty content
    loadingElement.classList.add('loading-state'); // Add class for styling
    // Use textContent to avoid potential parsing issues with the span itself
    loadingElement.innerHTML = '<span class="loading-text">Generating response...</span>';
    // Don't need extra scroll here, addMessage already scrolls
    // scrollToBottom();
    return loadingElement;
}

/**
 * Updates the content of an existing bot message bubble, parsing Markdown.
 * @param {HTMLElement} element - The message element to update.
 * @param {string} fullHtmlContent - The full HTML content (already parsed).
 * @param {boolean} isFirstChunk - Flag indicating if this is the first chunk of real data.
 */
function updateBotMessageContent(element, fullHtmlContent, isFirstChunk) {
    if (isFirstChunk) {
        element.classList.remove('loading-state');
        element.textContent = ''; // Clear previous content if it was just loading text
    }
    element.innerHTML = fullHtmlContent; // Update/set the main content

    // *** Apply Syntax Highlighting ***
    // Check if highlight.js (hljs) is loaded
    if (typeof hljs !== 'undefined') {
        // Find all <pre><code> blocks within the specific message element that was just updated
        const codeBlocks = element.querySelectorAll('pre code');
        codeBlocks.forEach((block) => {
            // Apply highlighting to each block
            hljs.highlightElement(block);
            console.log("Applied highlighting to code block:", block);
        });
    } else {
        // Warning if highlight.js wasn't loaded correctly
        console.warn("highlight.js (hljs) not loaded, cannot apply syntax highlighting.");
    }
    // Keep scrolled to the bottom as content streams in
    scrollToBottom();
}

/**
 * Updates a message bubble to show an error state.
 * @param {HTMLElement} element - The message element (likely the loading one).
 * @param {string} errorText - The error message to display.
 */
function showStreamError(element, errorText) {
     element.classList.remove('loading-state', 'bot');
     element.classList.add('error');
      // Clear any potential loading HTML before setting text
     element.innerHTML = '';
     element.textContent = `Error: ${errorText}`;
     scrollToBottom();
}

/**
 * Handles UI changes needed when the stream completes successfully.
 * @param {HTMLElement} element - The final bot message element.
 */
function handleStreamCompletion(element) {
    // Optional: Add subtle animation or indicator that generation finished
    // e.g., element.classList.add('finished');
    setSendButtonState(true); // Re-enable button
    userInput.focus();
}


/**
 * Scrolls the chat container to the bottom smoothly.
 */
function scrollToBottom() {
    // Small delay to ensure DOM update before scrolling
    setTimeout(() => {
        chatMessagesContainer.scrollTo({
            top: chatMessagesContainer.scrollHeight,
            behavior: 'smooth'
        });
    }, 50); // Adjust delay if needed
}

/**
 * Enables or disables the send button and updates input focus.
 * @param {boolean} enabled - True to enable, false to disable.
 */
function setSendButtonState(enabled) {
    sendButton.disabled = !enabled;
    if (enabled) {
        userInput.focus();
    }
}


// --- Event Listeners ---

chatForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const userMessage = userInput.value.trim();
    if (!userMessage) return;

    // --- HIDE INITIAL GREETING ON FIRST MESSAGE ---
    if (isFirstUserMessage && initialGreeting) {
        initialGreeting.classList.add('hidden');
        isFirstUserMessage = false; // Set flag so it only happens once
    }
    // ---------------------------------------------

    // 1. Add user message to UI
    addMessage(userMessage, 'user');
    const promptValue = userInput.value; // Grab value before clearing
    userInput.value = '';
    setSendButtonState(false); // Disable button

    // 2. Show loading indicator in a new bot message bubble
    const botMessageId = `bot-message-${Date.now()}`;
    const loadingElement = showLoadingIndicator(botMessageId);

    // 3. Call the API function (defined in api.js)
    streamChatResponse(promptValue, loadingElement, {
        onData: updateBotMessageContent,
        onError: showStreamError,
        onComplete: handleStreamCompletion
    });
});

// Optional: Enter key submission
userInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        chatForm.requestSubmit();
    }
});

// --- Initial Setup ---
document.addEventListener('DOMContentLoaded', () => {
    // Ensure initial greeting is visible on load if it exists
    // (The CSS opacity: 0 and animation handles the fade-in)
    userInput.focus();
    const backButton = document.getElementById('back-button');
    if (backButton) {
        backButton.addEventListener('click', () => {
            window.history.back(); // Navigate to the previous page in history
        });
    }
});