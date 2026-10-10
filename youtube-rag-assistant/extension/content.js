(() => {
    if (window.__youtubeRagAssistantLoaded) {
        return;
    }

    window.__youtubeRagAssistantLoaded = true;

    function getVideoInformation() {
        const url = new URL(window.location.href);

        const videoId =
            url.hostname === "youtu.be"
                ? url.pathname.slice(1)
                : url.searchParams.get("v");

        if (!videoId || !/^[a-zA-Z0-9_-]{11}$/.test(videoId)) {
            return {
                isVideoPage: false,
                videoId: null,
                videoUrl: null,
                title: null
            };
        }

        const titleElement =
            document.querySelector(
                "h1.ytd-watch-metadata yt-formatted-string"
            ) ||
            document.querySelector("h1.title");

        const title =
            titleElement?.textContent?.trim() ||
            document.title.replace(/\s*-\s*YouTube$/, "").trim();

        return {
            isVideoPage: true,
            videoId,
            videoUrl: `https://www.youtube.com/watch?v=${videoId}`,
            title
        };
    }

    chrome.runtime.onMessage.addListener(
        (message, sender, sendResponse) => {
            if (message.type === "GET_VIDEO_INFO") {
                sendResponse(getVideoInformation());
            }
        }
    );

    // YouTube uses client-side navigation, so the URL can change
    // without reloading the page.
    let lastUrl = location.href;

    const observer = new MutationObserver(() => {
        if (location.href === lastUrl) {
            return;
        }

        lastUrl = location.href;

        // Popup requests fresh video information when opened.
        // No backend request is made from this content script.
    });

    observer.observe(document, {
        childList: true,
        subtree: true
    });
})();