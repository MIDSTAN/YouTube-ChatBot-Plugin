const API_BASE_URL = "http://127.0.0.1:8000";

const elements = {
    connectionStatus: document.getElementById("connection-status"),
    videoTitle: document.getElementById("video-title"),
    videoId: document.getElementById("video-id"),

    prepareButton: document.getElementById("prepare-button"),

    chatMessages: document.getElementById("chat-messages"),
    chatForm: document.getElementById("chat-form"),
    questionInput: document.getElementById("question-input"),
    sendButton: document.getElementById("send-button"),

    closeButton: document.getElementById("close-button")
};

let currentVideo = null;
let isIndexing = false;
let isSending = false;


// --------------------------------------------------
// Utility functions
// --------------------------------------------------

function setStatus(message, type = "") {
    elements.connectionStatus.textContent = message;

    elements.connectionStatus.classList.remove(
        "status-success",
        "status-error"
    );

    if (type === "success") {
        elements.connectionStatus.classList.add("status-success");
    }

    if (type === "error") {
        elements.connectionStatus.classList.add("status-error");
    }
}


function addMessage(text, sender = "assistant", options = {}) {
    const message = document.createElement("div");

    message.className = `message ${
        sender === "user" ? "user-message" : "assistant-message"
    }`;

    if (options.error) {
        message.classList.add("message-error");
    }

    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = sender === "user" ? "YOU" : "AI";

    const content = document.createElement("div");
    content.className = "message-content";
    content.textContent = text;

    message.appendChild(avatar);
    message.appendChild(content);

    elements.chatMessages.appendChild(message);

    elements.chatMessages.scrollTop =
        elements.chatMessages.scrollHeight;

    return message;
}


function setChatEnabled(enabled) {
    elements.questionInput.disabled = !enabled;
    elements.sendButton.disabled = !enabled;

    if (enabled) {
        elements.questionInput.focus();
    }
}


function setVideoInformation(video) {
    currentVideo = video;

    elements.videoTitle.textContent =
        video.title || "YouTube video";

    elements.videoId.textContent =
        video.videoId ? `Video ID: ${video.videoId}` : "";

    elements.prepareButton.disabled = !video.videoId;

    setChatEnabled(false);
}


// --------------------------------------------------
// Detect the current YouTube video
// --------------------------------------------------

async function getCurrentVideo() {
    const [tab] = await chrome.tabs.query({
        active: true,
        currentWindow: true
    });

    if (!tab?.id || !tab.url) {
        throw new Error("Unable to identify the active browser tab.");
    }

    const url = new URL(tab.url);

    if (
        url.hostname !== "www.youtube.com" &&
        url.hostname !== "youtube.com" &&
        url.hostname !== "m.youtube.com"
    ) {
        throw new Error("Open a YouTube video to use this assistant.");
    }

    // The content script reports the title and video ID.
    try {
        const info = await chrome.tabs.sendMessage(tab.id, {
            type: "GET_VIDEO_INFO"
        });

        if (info?.isVideoPage && info.videoId) {
            return info;
        }
    } catch {
        // A content script may not yet be available.
    }

    // Fallback: extract the ID directly from the tab URL.
    const videoId = url.searchParams.get("v");

    if (!videoId || !/^[a-zA-Z0-9_-]{11}$/.test(videoId)) {
        throw new Error("The current tab does not contain a YouTube video.");
    }

    return {
        isVideoPage: true,
        videoId,
        videoUrl: `https://www.youtube.com/watch?v=${videoId}`,
        title: tab.title || "YouTube video"
    };
}


// --------------------------------------------------
// Backend communication
// --------------------------------------------------

async function apiRequest(endpoint, body) {
    const controller = new AbortController();

    const timeout = setTimeout(() => {
        controller.abort();
    }, 120000);

    try {
        const response = await fetch(
            `${API_BASE_URL}${endpoint}`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify(body),

                signal: controller.signal
            }
        );

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(
                data.detail ||
                data.message ||
                `Backend request failed (${response.status}).`
            );
        }

        return data;
    } catch (error) {
        if (error.name === "AbortError") {
            throw new Error(
                "The request took too long. Please try again."
            );
        }

        if (error instanceof TypeError) {
            throw new Error(
                "Cannot connect to FastAPI. Check that your backend is running."
            );
        }

        throw error;
    } finally {
        clearTimeout(timeout);
    }
}


// --------------------------------------------------
// Transcript preparation
// --------------------------------------------------

async function prepareVideo() {
    if (isIndexing) {
        return;
    }

    isIndexing = true;

    elements.prepareButton.disabled = true;
    elements.prepareButton.textContent = "Preparing...";

    setChatEnabled(false);
    setStatus("Preparing video...");

    addMessage(
        "I'm retrieving the English transcript and preparing the video for questions."
    );

    try {
        const video = await getCurrentVideo();

        setVideoInformation(video);

        const result = await apiRequest("/transcript", {
            video_id: video.videoId,
            language: "en"
        });

        if (result.status !== "ready") {
            throw new Error(
                result.message || "The transcript is not ready yet."
            );
        }

        setStatus("Transcript ready", "success");

        elements.prepareButton.textContent = "Video Ready";

        setChatEnabled(true);

        addMessage(
            "The video is ready! Ask me anything about its content."
        );

        // Remember which video was prepared in this popup session.
        await chrome.storage.local.set({
            preparedVideoId: video.videoId
        });

    } catch (error) {
        setStatus("Preparation failed", "error");

        elements.prepareButton.textContent = "Retry Preparation";

        addMessage(error.message, "assistant", {
            error: true
        });

    } finally {
        isIndexing = false;

        elements.prepareButton.disabled = !currentVideo?.videoId;
    }
}


// --------------------------------------------------
// Display answer sources
// --------------------------------------------------

function formatSources(sources) {
    if (!Array.isArray(sources) || sources.length === 0) {
        return "";
    }

    const formatted = sources.map((source) => {
        const start = Number(source.start_time);
        const end = Number(source.end_time);

        if (!Number.isFinite(start)) {
            return null;
        }

        const startLabel = formatTime(start);

        if (!Number.isFinite(end)) {
            return `Source: ${startLabel}`;
        }

        return `Source: ${startLabel}–${formatTime(end)}`;
    }).filter(Boolean);

    return [...new Set(formatted)].join("\n");
}


function formatTime(seconds) {
    const total = Math.max(0, Math.floor(seconds));

    const hours = Math.floor(total / 3600);
    const minutes = Math.floor((total % 3600) / 60);
    const remainingSeconds = total % 60;

    if (hours > 0) {
        return [
            hours,
            String(minutes).padStart(2, "0"),
            String(remainingSeconds).padStart(2, "0")
        ].join(":");
    }

    return [
        minutes,
        String(remainingSeconds).padStart(2, "0")
    ].join(":");
}


// --------------------------------------------------
// Chat
// --------------------------------------------------

async function sendQuestion(question) {
    if (isSending || !currentVideo?.videoId) {
        return;
    }

    isSending = true;

    elements.sendButton.disabled = true;
    elements.questionInput.disabled = true;

    addMessage(question, "user");

    const loadingMessage = addMessage(
        "Thinking...",
        "assistant"
    );

    loadingMessage.querySelector(".message-content")
        .classList.add("typing-indicator");

    try {
        const result = await apiRequest("/chat", {
            video_id: currentVideo.videoId,
            question
        });

        if (!result.answer) {
            throw new Error("The backend returned an empty answer.");
        }

        loadingMessage.remove();

        const sources = formatSources(result.sources);

        const answer = sources
            ? `${result.answer}\n\n${sources}`
            : result.answer;

        addMessage(answer, "assistant");

    } catch (error) {
        loadingMessage.remove();

        addMessage(error.message, "assistant", {
            error: true
        });

    } finally {
        isSending = false;

        elements.questionInput.disabled = false;
        elements.sendButton.disabled = false;

        elements.questionInput.focus();
    }
}


// --------------------------------------------------
// Event listeners
// --------------------------------------------------

elements.prepareButton.addEventListener("click", prepareVideo);

elements.chatForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const question = elements.questionInput.value.trim();

    if (!question || isSending || isIndexing) {
        return;
    }

    elements.questionInput.value = "";

    await sendQuestion(question);
});


elements.closeButton.addEventListener("click", () => {
    window.close();
});


// --------------------------------------------------
// Initialize popup
// --------------------------------------------------

async function initialize() {
    try {
        setStatus("Detecting video...");

        const video = await getCurrentVideo();

        setVideoInformation(video);

        setStatus("Ready to prepare video");

    } catch (error) {
        setStatus("No video detected", "error");

        elements.videoTitle.textContent = error.message;

        elements.videoId.textContent = "";

        elements.prepareButton.disabled = true;
        setChatEnabled(false);
    }
}

initialize();