
const BACKEND_URL = "http://127.0.0.1:8000";

let currentDocumentId = null;
let currentFilename = null;
let currentDocuments = [];

function getWelcomeMessageHTML() {
    return `
        <div class="welcome-message">
            <div class="welcome-graphic">
              <div class="logo-orb-wrapper">
                <div class="pulsing-halo"></div>
                <div class="inner-orb">
                  <svg
                    width="36"
                    height="36"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.8"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path d="M16 16l3-8 3 8c-.1.3-.3.5-.6.5h-4.8c-.3 0-.5-.2-.6-.5Z" />
                    <path d="M2 16l3-8 3 8c-.1.3-.3.5-.6.5H2.6c-.3 0-.5-.2-.6-.5Z" />
                    <path d="M7 6h10" />
                    <path d="M12 2v18" />
                    <path d="M5 19h14" />
                  </svg>
                </div>
              </div>
            </div>

            <h1>ContractFlow <span class="gradient-text">AI</span></h1>

            <p class="welcome-subtitle">
              Upload a legal contract in PDF, images, or Word format. Ask questions, analyze risks, find obligations, and extract key details instantly.
            </p>

            <div class="suggested-grid">
              <div class="suggested-card">
                <span class="card-icon">⚡</span>
                <h3>Risk Analysis</h3>
                <p>Identify liabilities, penalties, or unusual risk clauses.</p>
              </div>
              <div class="suggested-card">
                <span class="card-icon">🔑</span>
                <h3>Key Obligations</h3>
                <p>Pinpoint important contract terms</p>
              </div>
              <div class="suggested-card">
                <span class="card-icon">📋</span>
                <h3>Summary</h3>
                <p>Get a quick, high-level summary of the contract structure.</p>
              </div>
            </div>
        </div>
    `;
}

// SESSION MANAGEMENT

let sessionId = localStorage.getItem(
    "session_id"
);

if (!sessionId) {

    sessionId = crypto.randomUUID();

    localStorage.setItem(
        "session_id",
        sessionId
    );
}

console.log(
    "Session ID:",
    sessionId
);



// RESTORE SESSION

window.addEventListener(

    "DOMContentLoaded",

    () => {

        document
            .getElementById("fileInput")
            .addEventListener(
                "change",
                uploadFile
            );

        document
            .getElementById("queryInput")
            .addEventListener(

                "keypress",

                function (event) {

                    if (
                        event.key === "Enter"
                    ) {
                        event.preventDefault();
                        sendMessage();
                    }
                }
            );

        restoreSessionState();

        // Ensure sidebar is expanded by default (restore normal sidebar)
        try {
            const sidebar = document.querySelector('.sidebar');
            if (sidebar) {
                sidebar.classList.remove('collapsed');
            }
            localStorage.removeItem('sidebar_collapsed');
            const topBtn = document.getElementById('sidebarToggleTop');
            if (topBtn) topBtn.classList.remove('active');
        } catch (e) { }

        // mobile edge opener (treat like hamburger toggle on small screens)
        const edge = document.getElementById('sidebarEdge');
        if (edge) edge.addEventListener('click', toggleSidebar);


    }
);

// Sidebar collapsed state
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;
    const collapsed = sidebar.classList.toggle('collapsed');
    const topBtn = document.getElementById('sidebarToggleTop');
    if (topBtn) {
        topBtn.classList.toggle('active', collapsed);
    }
    try { localStorage.setItem('sidebar_collapsed', collapsed ? '1' : '0'); } catch (e) { }
}

// restore sidebar state on load
try {
    const saved = localStorage.getItem('sidebar_collapsed');
    if (saved === '1') {
        const s = document.querySelector('.sidebar');
        if (s) s.classList.add('collapsed');
    }
} catch (e) { }

// ensure top button reflects initial state
try {
    const topBtn = document.getElementById('sidebarToggleTop');
    const sidebar = document.querySelector('.sidebar');
    if (topBtn && sidebar) {
        const collapsed = sidebar.classList.contains('collapsed');
        topBtn.classList.toggle('active', collapsed);
    }
} catch (e) { }

function handleTopToggle() {
    // On small screens, open a drawer overlay. On larger screens toggle collapsed rail.
    if (window.innerWidth <= 768) {
        const sidebar = document.querySelector('.sidebar');
        if (!sidebar) return;
        const isOpen = sidebar.classList.toggle('drawer-open');
        const backdrop = getOrCreateBackdrop();
        if (isOpen) {
            backdrop.classList.add('visible');
            document.body.classList.add('drawer-active');
            try { document.body.style.overflow = 'hidden'; } catch (e) { }
        } else {
            backdrop.classList.remove('visible');
            document.body.classList.remove('drawer-active');
            try { document.body.style.overflow = ''; } catch (e) { }
        }
    } else {
        toggleSidebar();
    }
}

// close on Escape
document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
        closeMobileSidebar();
    }
});

// Mobile sidebar open/close
function openMobileSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const backdrop = getOrCreateBackdrop();
    if (!sidebar || !backdrop) return;
    sidebar.classList.add('drawer-open');
    backdrop.classList.add('visible');
}

function closeMobileSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const backdrop = document.querySelector('.sidebar-backdrop');
    if (!sidebar) return;
    sidebar.classList.remove('drawer-open');
    if (backdrop) backdrop.classList.remove('visible');
    document.body.classList.remove('drawer-active');
    try { document.body.style.overflow = ''; } catch (e) { }
}

function getOrCreateBackdrop() {
    let b = document.querySelector('.sidebar-backdrop');
    if (!b) {
        b = document.createElement('div');
        b.className = 'sidebar-backdrop';
        const container = document.querySelector('.app-container') || document.body;
        container.appendChild(b);
        b.addEventListener('click', closeMobileSidebar);
    }
    return b;
}

// Automatic session teardown on page reload or close has been removed to allow session persistence.
// Session cleanup will now only occur when explicitly requested via the 'End Session' action in the sidebar.

async function restoreSessionState() {

    try {

        const response = await fetch(
            `${BACKEND_URL}/session-state?session_id=${encodeURIComponent(sessionId)}`
        );

        const data = await response.json();

        if (!data.success) {
            return;
        }

        currentDocuments = data.documents || [];
        currentDocumentId = data.document_id || null;
        currentFilename = data.filename || null;

        if (!currentDocumentId && currentDocuments.length) {
            const fallbackDocument = currentDocuments[currentDocuments.length - 1];
            currentDocumentId = fallbackDocument.document_id;
            currentFilename = fallbackDocument.filename;
        }

        if (currentDocumentId && currentFilename) {
            localStorage.setItem("document_id", currentDocumentId);
            localStorage.setItem("filename", currentFilename);
        }

        updateSelectedContractHeader();
        renderContractList();
        renderDocumentInfo(currentFilename);
        updateDeleteButton();
        renderConversationHistory(data.messages || []);

    } catch (error) {

        console.error("SESSION RESTORE ERROR:", error);
    }
}

function renderDocumentInfo(filename) {

    const el = document.getElementById("documentInfo");
    if (!el) return; // element removed from layout by design

    el.innerHTML = filename
        ? `<strong>Uploaded:</strong><br>${filename}`
        : "No contract uploaded";
}

function updateDeleteButton() {

    const deleteButton = document.getElementById("deleteBtn");

    if (!deleteButton) return;

    deleteButton.disabled = !currentDocumentId;
    // Keep button icon markup intact; only update the visible label inside the span
    const labelSpan = deleteButton.querySelector("span");
    if (labelSpan) {
        labelSpan.textContent = currentFilename ? "Delete Contract" : "Delete Contract";
    } else {
        // fallback
        deleteButton.textContent = "Delete Contract";
    }
}

function handleSessionEndOnUnload() {

    if (!sessionId) return;

    try {

        const payload = JSON.stringify({ session_id: sessionId });
        const blob = new Blob([payload], { type: "application/json" });
        navigator.sendBeacon(`${BACKEND_URL}/end-session`, blob);

    } catch (error) {

        console.error("SESSION END ON UNLOAD FAILED:", error);
    }
}

function renderContractList() {

    const contractList = document.getElementById("contractList");

    if (!contractList) return;

    if (!currentDocuments.length) {
        contractList.innerHTML = `
            <div class="contract-empty-state">No uploaded contracts yet</div>
        `;
        return;
    }

    contractList.innerHTML = currentDocuments.map((document) => {
        const isActive = document.document_id === currentDocumentId;
        return `
            <button
                class="contract-item ${isActive ? "active" : ""}"
                type="button"
                onclick="selectContract('${document.document_id}')"
            >
                <span class="contract-item-name">${document.filename}</span>
                <span class="contract-item-meta">${isActive ? "Selected" : "Click to select"}</span>
            </button>
        `;
    }).join("");
}

async function selectContract(documentId) {

    try {

        const response = await fetch(
            `${BACKEND_URL}/session-active-document`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    document_id: documentId
                })
            }
        );

        const data = await response.json();

        if (!data.success) {
            addMessage(data.error, "bot-message");
            return;
        }

        currentDocumentId = data.document_id;
        currentFilename = data.filename;
        localStorage.setItem("document_id", currentDocumentId);
        localStorage.setItem("filename", currentFilename);

        updateSelectedContractHeader();
        renderDocumentInfo(currentFilename);
        updateDeleteButton();

        restoreSessionState().then(() => {
            closeMobileSidebar();
        });

    } catch (error) {

        console.error(error);
        addMessage("Could not select contract.", "bot-message");
    }
}

function renderConversationHistory(messages) {

    const chatMessages = document.getElementById("chatMessages");

    chatMessages.innerHTML = "";

    if (!messages.length) {

        chatMessages.innerHTML = getWelcomeMessageHTML();

        return;
    }

    messages.forEach((message) => {
        if (message.role === "user") {
            addMessage(message.content, "user-message");
        } else {
            addBotMessageWithSources(message.content, null);
        }
    });
}

// UPLOAD PICKER

function triggerUpload() {

    document
        .getElementById("fileInput")
        .click();
}


// MESSAGE


function addMessage(

    text,

    className
) {

    removeWelcome();

    const chatMessages =
        document.getElementById(
            "chatMessages"
        );

    const div =
        document.createElement("div");

    div.className =
        `message ${className}`;

    div.innerText = text;

    chatMessages.appendChild(div);

    scrollToBottom();

    return div;
}


// REMOVE WELCOME


function removeWelcome() {

    const welcome =
        document.querySelector(
            ".welcome-message"
        );

    if (welcome) {

        welcome.remove();
    }
}

// UPLOAD

async function uploadFile(event) {

    try {

        const file = event.target.files[0];

        if (!file) return;

        console.log("Uploading:", file.name);

        const progressContainer = document.getElementById("uploadProgressContainer");
        const progressBar = document.getElementById("uploadProgressBar");
        const progressText = document.getElementById("uploadProgressText");

        if (progressContainer && progressBar && progressText) {
            progressContainer.style.display = "block";
            progressBar.style.width = "0%";
            progressBar.style.background = ""; // Reset background color
            progressText.textContent = "Just a Moment...";
        }

        const formData = new FormData();
        formData.append("file", file);
        formData.append("session_id", sessionId);

        const xhr = new XMLHttpRequest();

        xhr.upload.addEventListener("progress", (e) => {
            if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 100);
                if (progressBar) progressBar.style.width = `${percent}%`;

                if (percent >= 100) {
                    if (progressText) progressText.textContent = "Analyzing contract, please wait...";
                } else {
                    if (progressText) progressText.textContent = `Uploading contract... ${percent}%`;
                }
            }
        });

        xhr.addEventListener("load", () => {
            try {
                if (xhr.status >= 200 && xhr.status < 300) {
                    const data = JSON.parse(xhr.responseText);
                    console.log("UPLOAD DATA:", data);

                    if (data.success === true) {
                        currentDocumentId = data.document_id;
                        currentFilename = data.filename;

                        currentDocuments = [
                            ...currentDocuments.filter(
                                (document) => document.document_id !== data.document_id
                            ),
                            {
                                document_id: data.document_id,
                                filename: data.filename
                            }
                        ];

                        localStorage.setItem("document_id", data.document_id);
                        localStorage.setItem("filename", data.filename);

                        updateSelectedContractHeader();
                        renderDocumentInfo(data.filename);
                        updateDeleteButton();

                        restoreSessionState().then(() => {
                            if (progressBar) {
                                progressBar.style.width = "100%";
                                progressBar.style.background = "linear-gradient(135deg, #10b981 0%, #059669 100%)";
                            }
                            if (progressText) progressText.textContent = "Contract ready!";
                            closeMobileSidebar();
                        });
                    } else {
                        addMessage(`Upload Failed: ${data.error}`, "bot-message");
                    }
                } else {
                    addMessage(`Upload failed with status code ${xhr.status}.`, "bot-message");
                }
            } catch (err) {
                console.error("Parse error:", err);
                addMessage("Upload failed: Invalid response format.", "bot-message");
            } finally {
                setTimeout(() => {
                    if (progressContainer) progressContainer.style.display = "none";
                    if (progressBar) progressBar.style.background = ""; // Reset back to default css gradient
                }, 2000);
            }
        });

        xhr.addEventListener("error", () => {
            addMessage("Upload failed due to network error.", "bot-message");
            if (progressContainer) progressContainer.style.display = "none";
        });

        xhr.open("POST", `${BACKEND_URL}/upload`);
        xhr.send(formData);

    } catch (error) {

        console.error("UPLOAD ERROR:", error);
        addMessage("Upload failed.", "bot-message");
        const progressContainer = document.getElementById("uploadProgressContainer");
        if (progressContainer) progressContainer.style.display = "none";
    }
}




// SEND MESSAGE

async function sendMessage() {

    const input =
        document.getElementById(
            "queryInput"
        );

    const query =
        input.value.trim();

    if (!query) return;

    if (!currentDocumentId) {

        addMessage(

            "Please upload a contract first.",

            "bot-message"
        );

        return;
    }

    addMessage(
        query,
        "user-message"
    );

    input.value = "";

    const loading =
        addLoadingMessage("Just a Moment...");

    try {

        const response = await fetch(

            `${BACKEND_URL}/chat`,

            {
                method: "POST",

                headers: {

                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({

                    query: query,

                    document_id:
                        currentDocumentId,
                    session_id: sessionId
                })
            }
        );

        const data =
            await response.json();

        loading.remove();

        if (data.success) {
            addBotMessageWithSources(data.answer, data.sources);
        } else {
            addMessage(data.error, "bot-message");
        }

    } catch (error) {

        console.error(error);

        loading.remove();

        addMessage(

            "Backend connection failed.",

            "bot-message"
        );
    }
}

// DELETE CONTRACT

async function deleteCurrentContract() {

    if (!currentDocumentId) {

        addMessage(

            "Select a contract first.",

            "bot-message"
        );

        return;
    }

    const deletedDocumentId = currentDocumentId;

    try {

        const response = await fetch(

            `${BACKEND_URL}/delete-contract`,

            {
                method: "POST",

                headers: {

                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({

                    document_id:
                        currentDocumentId,
                    session_id: sessionId
                })
            }
        );

        const data =
            await response.json();

        if (data.success) {

            localStorage.removeItem(
                "document_id"
            );

            localStorage.removeItem(
                "filename"
            );

            currentDocumentId = null;
            currentFilename = null;
            currentDocuments = currentDocuments.filter(
                (document) => document.document_id !== deletedDocumentId
            );

            if (currentDocuments.length) {
                const fallbackDocument = currentDocuments[currentDocuments.length - 1];
                currentDocumentId = fallbackDocument.document_id;
                currentFilename = fallbackDocument.filename;

                localStorage.setItem("document_id", currentDocumentId);
                localStorage.setItem("filename", currentFilename);
            }

            updateSelectedContractHeader();
            renderDocumentInfo(currentFilename);
            updateDeleteButton();

            restoreSessionState();

        } else {

            addMessage(

                data.error,

                "bot-message"
            );
        }

    } catch (error) {

        console.error(error);

        addMessage(

            "Delete failed.",

            "bot-message"
        );
    }
}

async function endSession() {

    try {

        const response = await fetch(
            `${BACKEND_URL}/end-session`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ session_id: sessionId })
            }
        );

        const data = await response.json();

        if (!data.success) {
            addMessage(data.error, "bot-message");
            return;
        }

        localStorage.removeItem("session_id");
        localStorage.removeItem("document_id");
        localStorage.removeItem("filename");

        sessionId = crypto.randomUUID();
        localStorage.setItem("session_id", sessionId);

        currentDocumentId = null;
        currentFilename = null;
        currentDocuments = [];

        updateSelectedContractHeader();
        renderDocumentInfo(null);
        updateDeleteButton();
        renderContractList();

        document.getElementById("chatMessages").innerHTML = getWelcomeMessageHTML();

    } catch (error) {

        console.error(error);
        addMessage("Could not end session.", "bot-message");
    }
}

function addLoadingMessage(text) {

    removeWelcome();

    const chatMessages = document.getElementById("chatMessages");

    const div = document.createElement("div");
    div.className = "message bot-message loading-message";
    div.innerHTML = `
        <div class="loading-card">
            <div class="loading-orb"></div>
            <div class="loading-copy">
                <div class="loading-title">${text}</div>
                <div class="loading-dots" aria-hidden="true">
                    <span></span><span></span><span></span>
                </div>
            </div>
        </div>
    `;

    chatMessages.appendChild(div);
    scrollToBottom();

    return div;
}

function updateSelectedContractHeader() {
    const activeNameEl = document.getElementById("activeContractName");
    const activeMetaEl = document.getElementById("activeContractMeta");
    if (activeNameEl) {
        activeNameEl.textContent = currentFilename || "No contract selected";
    }
    if (activeMetaEl) {
        activeMetaEl.textContent = currentFilename
            ? "Ready for analysis — Ask questions in the panel below"
            : "Select a contract from the sidebar to begin";
    }
}

function formatMarkdown(text) {
    let escaped = escapeHtml(text);
    // Replace **bold** with <strong>bold</strong>
    escaped = escaped.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    return escaped;
}

// Inject CSS styles dynamically for the three-dots dropdown and modal
(function () {
    const style = document.createElement("style");
    style.textContent = `
        .message.bot-message {
            position: relative;
            padding-right: 44px !important;
        }
        .message-actions {
            position: absolute;
            top: 10px;
            right: 10px;
            z-index: 10;
        }
        .message-action-btn {
            background: transparent;
            border: none;
            color: rgba(255, 255, 255, 0.45);
            padding: 6px;
            cursor: pointer;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
        }
        .message-action-btn:hover {
            background: rgba(255, 255, 255, 0.08);
            color: #ffffff;
        }
        .message-dropdown {
            display: none;
            position: absolute;
            top: 100%;
            right: 0;
            margin-top: 6px;
            background: #181824;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 8px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
            padding: 4px;
            min-width: 140px;
            z-index: 100;
        }
        .message-dropdown.active {
            display: block;
        }
        .dropdown-item {
            width: 100%;
            background: transparent;
            border: none;
            color: rgba(255, 255, 255, 0.8);
            padding: 8px 12px;
            text-align: left;
            font-size: 13px;
            cursor: pointer;
            display: flex;
            align-items: center;
            border-radius: 6px;
            transition: all 0.2s ease;
        }
        .dropdown-item:hover {
            background: rgba(255, 255, 255, 0.06);
            color: #ffffff;
        }
        
        /* Sources Modal styling */
        .sources-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0, 0, 0, 0.65);
            backdrop-filter: blur(6px);
            z-index: 9999;
            align-items: center;
            justify-content: center;
        }
        .sources-modal.visible {
            display: flex;
        }
        .sources-modal-content {
            background: #11111a;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
            width: 90%;
            max-width: 650px;
            max-height: 80vh;
            display: flex;
            flex-direction: column;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);
            overflow: hidden;
            animation: modalIn 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        }
        @keyframes modalIn {
            from { transform: scale(0.95); opacity: 0; }
            to { transform: scale(1); opacity: 1; }
        }
        .sources-modal-header {
            padding: 16px 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            display: flex;
            align-items: center;
            justify-content: text-between;
            justify-content: space-between;
        }
        .sources-modal-header h3 {
            margin: 0;
            font-size: 15px;
            font-weight: 600;
            color: #ffffff;
        }
        .sources-modal-close {
            background: transparent;
            border: none;
            color: rgba(255, 255, 255, 0.4);
            cursor: pointer;
            padding: 4px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
        }
        .sources-modal-close:hover {
            background: rgba(255, 255, 255, 0.08);
            color: #ffffff;
        }
        .sources-modal-list {
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        .modal-source-item {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.04);
            border-radius: 10px;
            padding: 16px;
        }
        .modal-source-text {
            font-size: 13.5px;
            line-height: 1.55;
            color: rgba(255, 255, 255, 0.85);
            margin-bottom: 12px;
            white-space: pre-wrap;
        }
        .modal-source-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }
        .modal-source-badge {
            background: rgba(255, 255, 255, 0.06);
            border-radius: 6px;
            padding: 3px 8px;
            font-size: 11px;
            color: rgba(255, 255, 255, 0.55);
        }
        .modal-source-badge.risk-high {
            background: rgba(239, 68, 68, 0.12);
            color: #f87171;
        }
        .modal-source-badge.risk-medium {
            background: rgba(245, 158, 11, 0.12);
            color: #fbbf24;
        }
        .modal-source-badge.risk-low {
            background: rgba(16, 185, 129, 0.12);
            color: #34d399;
        }
    `;
    document.head.appendChild(style);
})();

function getOrCreateSourcesModal() {
    let modal = document.getElementById("sourcesModal");
    if (!modal) {
        modal = document.createElement("div");
        modal.id = "sourcesModal";
        modal.className = "sources-modal";
        modal.addEventListener("click", closeSourcesModal);

        modal.innerHTML = `
            <div class="sources-modal-content" onclick="event.stopPropagation()">
                <div class="sources-modal-header">
                    <h3>Sources & Citations</h3>
                    <button class="sources-modal-close" onclick="hideSourcesModal()">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                    </button>
                </div>
                <div id="sourcesModalList" class="sources-modal-list"></div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    return modal;
}

function hideSourcesModal() {
    const modal = document.getElementById("sourcesModal");
    if (modal) {
        modal.classList.remove("visible");
    }
}

function closeSourcesModal(e) {
    hideSourcesModal();
}

function openSourcesModal(sources, e) {
    if (e) {
        e.stopPropagation();
        e.preventDefault();
    }

    // Close active dropdowns
    document.querySelectorAll(".message-dropdown.active").forEach(d => {
        d.classList.remove("active");
    });

    const modal = getOrCreateSourcesModal();
    const list = document.getElementById("sourcesModalList");
    if (!list) return;

    list.innerHTML = "";

    sources.forEach(src => {
        const textContent = src.text || "";
        const filename = src.metadata?.filename || "Unknown document";
        const sectionName = src.metadata?.parent_section || "General Section";
        const riskLevel = src.metadata?.risk_level || "Low";
        const riskCategory = src.metadata?.risk_category || "General";
        const riskClass = `risk-${riskLevel.toLowerCase()}`;

        const item = document.createElement("div");
        item.className = "modal-source-item";
        item.innerHTML = `
            <div class="modal-source-text">"${escapeHtml(textContent)}"</div>
            <div class="modal-source-meta">
                <span class="modal-source-badge">Doc: ${escapeHtml(filename)}</span>
                <span class="modal-source-badge">Sec: ${escapeHtml(sectionName)}</span>
                <span class="modal-source-badge ${riskClass}">Risk: ${escapeHtml(riskLevel)} (${escapeHtml(riskCategory)})</span>
            </div>
        `;
        list.appendChild(item);
    });

    modal.classList.add("visible");
}

function toggleMessageMenu(btn, e) {
    if (e) {
        e.stopPropagation();
        e.preventDefault();
    }
    const dropdown = btn.nextElementSibling;
    const isActive = dropdown.classList.contains("active");

    // Close other dropdowns
    document.querySelectorAll(".message-dropdown.active").forEach(d => {
        if (d !== dropdown) d.classList.remove("active");
    });

    dropdown.classList.toggle("active", !isActive);
}

// Close dropdowns on outside click
document.addEventListener("click", () => {
    document.querySelectorAll(".message-dropdown.active").forEach(d => {
        d.classList.remove("active");
    });
});

function addBotMessageWithSources(text, sources) {
    removeWelcome();

    const chatMessages = document.getElementById("chatMessages");
    const div = document.createElement("div");
    div.className = "message bot-message";

    let formattedText = "";
    const paragraphs = text.split("\n\n");
    paragraphs.forEach(p => {
        p = p.trim();
        if (!p) return;

        if (p.includes("\n* ") || p.includes("\n- ") || p.startsWith("* ") || p.startsWith("- ")) {
            const lines = p.split("\n");
            let listHtml = "<ul>";
            lines.forEach(line => {
                line = line.trim();
                if (line.startsWith("*") || line.startsWith("-")) {
                    listHtml += `<li>${formatMarkdown(line.substring(1).trim())}</li>`;
                } else {
                    listHtml += `<li>${formatMarkdown(line)}</li>`;
                }
            });
            listHtml += "</ul>";
            formattedText += listHtml;
        } else {
            formattedText += `<p>${formatMarkdown(p).replace(/\n/g, "<br>")}</p>`;
        }
    });

    div.innerHTML = formattedText;

    if (sources && sources.length > 0) {
        const actionsContainer = document.createElement("div");
        actionsContainer.className = "message-actions";

        actionsContainer.innerHTML = `
            <button class="message-action-btn" onclick="toggleMessageMenu(this, event)" title="Message Actions">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="1.5"></circle>
                    <circle cx="12" cy="5" r="1.5"></circle>
                    <circle cx="12" cy="19" r="1.5"></circle>
                </svg>
            </button>
            <div class="message-dropdown">
                <button class="dropdown-item" onclick="openSourcesModal(JSON.parse(this.dataset.sources), event)">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 6px;">
                        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
                        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
                    </svg>
                    View sources
                </button>
            </div>
        `;
        const dropdownItem = actionsContainer.querySelector(".dropdown-item");
        dropdownItem.dataset.sources = JSON.stringify(sources);

        div.appendChild(actionsContainer);
    }

    chatMessages.appendChild(div);
    scrollToBottom();
    return div;
}

function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function scrollToBottom() {
    const chatMessages = document.getElementById("chatMessages");
    if (chatMessages) {
        setTimeout(() => {
            chatMessages.scrollTo({
                top: chatMessages.scrollHeight,
                behavior: "smooth"
            });
        }, 50);
    }
}

