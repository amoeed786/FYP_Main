document.addEventListener("DOMContentLoaded", () => {
    const toc = document.getElementById("toc");
    const chatBody = document.getElementById("chatBody");
    const userInput = document.getElementById("userInput");
    const sendBtn = document.getElementById("sendBtn");
    const generateQuizBtn = document.getElementById("generateQuizBtn");

    // Fetch and display Table of Contents
    fetchTOC();

    function fetchTOC() {
        let fileInput = document.getElementById("fileUpload");
        if (fileInput.files.length === 0) {
            alert("Please upload a file first.");
            return;
        }
    
        let formData = new FormData();
        formData.append("file", fileInput.files[0]); // Attach file
    
        fetch("/api/documents/extract-toc/", {
            method: "POST",
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.toc && data.toc.length > 0) {
                displayTOC(data.toc);
            } else {
                toc.innerHTML = "<p>No Table of Contents found.</p>";
            }
        })
        .catch(error => {
            console.error("TOC Fetch Error:", error);
            toc.innerHTML = "<p>Error loading Table of Contents.</p>";
        });
    }
    

    // Chatbot logic
    sendBtn.addEventListener("click", () => {
        const userMessage = userInput.value.trim();
        if (userMessage) {
            addMessage("user", userMessage);
            
            fetch("/api/documents/chatbot/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: userMessage })
            })
            .then(response => response.json())
            .then(data => addMessage("bot", data.bot_reply))
            .catch(error => {
                console.error("Chatbot Error:", error);
                addMessage("bot", "Sorry, I couldn't process that.");
            });

            userInput.value = "";
        }
    });

    // Handle the "Generate Quiz" button
    generateQuizBtn.addEventListener("click", (e) => {
        e.preventDefault();
        window.location.href = "quizForm.html"; // Redirect to quiz page
    });

    function addMessage(sender, message) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("chat-message", sender === "user" ? "user-message" : "bot-message");
        messageDiv.textContent = message;
        chatBody.appendChild(messageDiv);
        chatBody.scrollTop = chatBody.scrollHeight; // Scroll to bottom
    }
});
