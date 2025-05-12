import { GoogleGenerativeAI, HarmCategory, HarmBlockThreshold } from "https://cdn.jsdelivr.net/npm/@google/generative-ai/+esm";

// --- Configuration ---
// WARNING: Storing API keys client-side is insecure for production. Use a backend proxy.
const API_KEY = "AIzaSyATo2BlQ3pWpjqPeWKMFwVZm2yKqfT5VNI"; // YOUR API KEY
const MODEL_NAME = "gemini-1.5-pro-latest";


// --- Conversation History ---
// This array will store the conversation turns.
// Each element should be { role: "user" | "model", parts: [{ text: "..." }] }
let chatHistory = [];
console.log("Initial chat history:", chatHistory);

// --- Initialize Gemini ---
let genAI;
let model;
try {
    genAI = new GoogleGenerativeAI(API_KEY);
    model = genAI.getGenerativeModel({ model: MODEL_NAME });
    console.log("GoogleGenerativeAI initialized successfully.");
} catch (error) {
    console.error("Error initializing GoogleGenerativeAI:", error);
    // Optionally, display an error message to the user early
    alert("Failed to initialize the AI service. Please check the API key and configuration.");
}

// --- Safety Settings ---
// const safetySettings = [
//     { category: HarmCategory.HARM_CATEGORY_HARASSMENT,         threshold: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE },
//     { category: HarmCategory.HARM_CATEGORY_HATE_SPEECH,        threshold: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE },
//     { category: HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE },
//     { category: HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,  threshold: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE },
// ];

const safetySettings = [

];

// --- Generation Configuration ---
const generationConfig = {
    temperature: 0.8,
    topK: 1,
    topP: 0.95,
    maxOutputTokens: 2048, // Increased slightly if needed for longer follow-ups
};

// Check if marked library is loaded
console.log("marked library loaded?", typeof marked === 'function');


/**
 * Sends the *entire conversation history* plus the new prompt to the Gemini API
 * and streams the response. Updates history upon successful completion.
 *
 * @param {string} newPrompt - The user's latest message.
 * @param {HTMLElement} targetElement - The message element to update.
 * @param {object} callbacks - UI update callback functions.
 */
// js/api.js (or gemini2.js)
// ... (imports, config, history, init code remain the same) ...

async function streamChatResponse(newPrompt, targetElement, callbacks) {
    // ... (model initialization check remains the same) ...

    let fullResponse = "";
    let isFirstChunk = true;
    let streamHasData = false;

    const messagesToSend = [
        ...chatHistory,
        { role: "user", parts: [{ text: newPrompt }] }
    ];

    console.log("Sending to Gemini:", messagesToSend);

    let result; // Declare result outside try to access response in finally/catch if needed
    try {
        console.log("Calling model.generateContentStream()...");
        result = await model.generateContentStream({ // Assign to outer result
            contents: messagesToSend,
            generationConfig,
            safetySettings,
        });
        console.log("model.generateContentStream() call returned. Awaiting stream...");

        for await (const chunk of result.stream) {
            // console.log("Received stream chunk:", chunk); // Keep for deep debugging if needed

            // Check for prompt block ONLY within the loop
            if (chunk.promptFeedback && chunk.promptFeedback.blockReason) {
                const blockMessage = `Blocked based on prompt: ${chunk.promptFeedback.blockReason}`;
                console.error(blockMessage);
                throw new Error(blockMessage); // Exit loop and go to catch
            }

            // Attempt to get text, might be empty string
            const chunkText = chunk.text();
            // console.log("Extracted chunk text:", chunkText); // Keep for deep debugging

            if (chunkText !== undefined && chunkText !== null) { // Check exists, even if empty string
                // Only consider it data if it's non-empty
                if (chunkText.length > 0) {
                    streamHasData = true;
                    fullResponse += chunkText;
                    const parsedHtml = typeof marked !== 'undefined' ? marked.parse(fullResponse) : fullResponse;
                    callbacks.onData(targetElement, parsedHtml, isFirstChunk);
                    isFirstChunk = false;
                }
                // If chunkText is "", we just continue without setting streamHasData=true
            }
        }

        console.log("Finished iterating through stream.");

        // *** NEW: Check final response AFTER the loop ***
        const finalResponse = await result.response;
        console.log("Final response object:", JSON.stringify(finalResponse, null, 2)); // Log the whole object

        // Check for blocks or finish reasons in the final response
        const promptFeedback = finalResponse?.promptFeedback;
        const finishReason = finalResponse?.candidates?.[0]?.finishReason;
        const safetyRatings = finalResponse?.candidates?.[0]?.safetyRatings;

        if (promptFeedback?.blockReason) {
            const blockMessage = `Request blocked after streaming. Reason: ${promptFeedback.blockReason}`;
            console.error(blockMessage);
            throw new Error(blockMessage);
        }

        if (finishReason && finishReason !== "STOP" && finishReason !== "MAX_TOKENS") {
             // Other reasons include SAFETY, RECITATION, OTHER
             const reasonMessage = `Stream finished unexpectedly. Reason: ${finishReason}`;
             console.warn(reasonMessage, "Safety Ratings:", safetyRatings);
             // Decide if this specific reason should be an error for the user
             if (finishReason === "SAFETY") {
                throw new Error("Response blocked due to safety filters.");
             } else {
                 throw new Error(reasonMessage); // Throw a generic error for other non-STOP reasons
             }
        }

        // *** Final Check: Did we actually get data? ***
        if (streamHasData) {
            // SUCCESS: Update history
            console.log("Stream finished successfully with data. Updating history.");
            chatHistory.push({ role: "user", parts: [{ text: newPrompt }] });
            chatHistory.push({ role: "model", parts: [{ text: fullResponse }] });
            console.log("Updated History:", JSON.stringify(chatHistory));
            callbacks.onComplete(targetElement); // Signal UI completion
        } else {
            // No data received, and no specific block/error reason caught above
            console.warn("Stream finished, but no text content was processed.");
            // Check if finishReason was STOP but still no data (odd case)
             if (finishReason === "STOP") {
                 throw new Error("AI responded successfully but generated no text content.");
             } else {
                 // Default empty error if no other reason identified
                 throw new Error("Received an empty response from the AI. (Reason Unknown)");
             }
        }

    } catch (error) {
        console.error("Error during Gemini stream processing:", error);
        // Use the error message directly from the throw
        callbacks.onError(targetElement, error.message || "An unknown error occurred.");
        // Ensure UI is re-enabled even on error
        callbacks.onComplete(targetElement); // Signal UI completion
    }
}

// Ensure the function is globally accessible for scripts.js
window.streamChatResponse = streamChatResponse;
console.log("streamChatResponse available on window?", typeof window.streamChatResponse === 'function');