import { GoogleGenerativeAI, HarmCategory, HarmBlockThreshold } from "https://cdn.jsdelivr.net/npm/@google/generative-ai/+esm";

// --- Configuration ---
const API_KEY = "AIzaSyATo2BlQ3pWpjqPeWKMFwVZm2yKqfT5VNI"; // Replace with your key
const MODEL_NAME = "gemini-1.5-pro-latest";

// --- NO CHAT HISTORY ---
// let chatHistory = []; // REMOVED
// console.log("Initial chat history:", chatHistory); // REMOVED

// --- Initialize Gemini ---
let genAI;
let model;
try {
    genAI = new GoogleGenerativeAI(API_KEY);
    model = genAI.getGenerativeModel({ model: MODEL_NAME });
    console.log("GoogleGenerativeAI initialized successfully.");
} catch (error) {
    console.error("Error initializing GoogleGenerativeAI:", error);
    alert("Failed to initialize the AI service. Please check the API key and configuration.");
}

// --- Safety Settings --- (Keep as is or adjust as needed)
const safetySettings = [
    // Add settings here if needed
];

// --- Generation Configuration --- (Keep as is or adjust)
const generationConfig = {
    temperature: 0.8,
    topK: 1,
    topP: 0.95,
    maxOutputTokens: 2048,
};

// Check if marked library is loaded (it wasn't in your log - ensure it's linked correctly in HTML if you need Markdown)
const isMarkedLoaded = typeof marked === 'function';
if (!isMarkedLoaded) {
    console.warn("marked library not loaded. Markdown will not be parsed.");
}

/**
 * Converts a File object to the GoogleGenerativeAI.Part format.
 */
async function fileToGenerativePart(file) {
    const base64EncodedDataPromise = new Promise((resolve) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result.split(',')[1]);
        reader.readAsDataURL(file);
    });
    return {
        inlineData: { data: await base64EncodedDataPromise, mimeType: file.type },
    };
}

/**
 * Sends the prompt (text and/or image) to the Gemini API and streams the response.
 * This version does NOT use chat history.
 *
 * @param {string} newPromptText - The user's text prompt.
 * @param {File | Blob | null} imageFile - The user's uploaded image file/blob.
 * @param {HTMLElement} targetElement - The DOM element to update with the response.
 * @param {object} callbacks - UI update callback functions { onData, onError, onComplete }.
 */
async function streamChatResponse(newPromptText, imageFile, targetElement, callbacks) {
    if (!model) {
        callbacks.onError(targetElement, "AI Model not initialized.");
        callbacks.onComplete(targetElement);
        return;
    }

    let fullResponse = "";
    let isFirstChunk = true;
    let streamHasData = false;

    // --- Construct the user's message parts ---
    const userParts = [];
    let imagePartPromise = null;

    if (imageFile) {
        imagePartPromise = fileToGenerativePart(imageFile).catch(error => {
            console.error("Error converting image file:", error);
            throw new Error("Failed to process the image file.");
        });
    }

    if (newPromptText) {
        userParts.push({ text: newPromptText });
    }

    if (imagePartPromise) {
        try {
            const imagePart = await imagePartPromise;
            userParts.push(imagePart);
        } catch (error) {
             callbacks.onError(targetElement, error.message);
             callbacks.onComplete(targetElement);
             return;
        }
    }

    if (userParts.length === 0) {
        callbacks.onError(targetElement, "Cannot send an empty message.");
        callbacks.onComplete(targetElement);
        return;
    }

    // --- Prepare message for API (NO HISTORY) ---
    const currentUserMessage = { role: "user", parts: userParts };
    const messagesToSend = [currentUserMessage]; // Send only the current message

    console.log("Sending to Gemini (no history):", JSON.stringify(messagesToSend, null, 2));

    let result;
    try {
        console.log("Calling model.generateContentStream()...");
        result = await model.generateContentStream({
            contents: messagesToSend,
            generationConfig,
            safetySettings,
        });
        console.log("model.generateContentStream() call returned. Awaiting stream...");

        for await (const chunk of result.stream) {
            if (chunk.promptFeedback && chunk.promptFeedback.blockReason) {
                const blockMessage = `Blocked based on prompt: ${chunk.promptFeedback.blockReason}`;
                console.error(blockMessage);
                throw new Error(blockMessage);
            }

            const chunkText = chunk.text();

            if (chunkText !== undefined && chunkText !== null) {
                 if (chunkText.length > 0) {
                    streamHasData = true;
                    fullResponse += chunkText;
                    // Use marked only if loaded, otherwise pass raw text
                    const parsedHtml = typeof marked !== 'undefined' ? marked.parse(fullResponse) : fullResponse;

                    // --- *** CORRECTED CALLBACK ARGUMENT ORDER *** ---
                    callbacks.onData(parsedHtml, isFirstChunk, targetElement); // Pass content first!

                    isFirstChunk = false;
                }
            }
        }
        console.log("Finished iterating through stream.");

        const finalResponse = await result.response;
        console.log("Final response object:", JSON.stringify(finalResponse, null, 2));

        const promptFeedback = finalResponse?.promptFeedback;
        const finishReason = finalResponse?.candidates?.[0]?.finishReason;

        if (promptFeedback?.blockReason) {
            throw new Error(`Request blocked after streaming. Reason: ${promptFeedback.blockReason}`);
        }
        if (finishReason && finishReason !== "STOP" && finishReason !== "MAX_TOKENS") {
             const reasonMessage = `Stream finished unexpectedly. Reason: ${finishReason}`;
             console.warn(reasonMessage);
             if (finishReason === "SAFETY") {
                throw new Error("Response blocked due to safety filters.");
             } else {
                 throw new Error(reasonMessage);
             }
        }

        if (streamHasData) {
            console.log("Stream finished successfully. (No history update needed)");
            callbacks.onComplete(targetElement);
        } else {
             console.warn("Stream finished, but no text content was generated or processed.");
             if (finishReason === "STOP") {
                 throw new Error("AI responded successfully but generated no text content.");
             } else {
                 throw new Error("Received an empty response from the AI. (Reason Unknown)");
             }
        }

    } catch (error) {
        console.error("Error during Gemini stream processing:", error);
        // Pass targetElement if onError callback expects it (though showResultError doesn't use it)
        callbacks.onError(targetElement, error.message || "An unknown error occurred.");
        callbacks.onComplete(targetElement); // Ensure UI is re-enabled
    }
}

// Ensure the function is globally accessible
window.streamChatResponse = streamChatResponse;
console.log("streamChatResponse available on window?", typeof window.streamChatResponse === 'function');