document.addEventListener("DOMContentLoaded", () => {
    const toc = document.getElementById("toc");
    const chatBody = document.getElementById("chatBody");
    const userInput = document.getElementById("userInput");
    const sendBtn = document.getElementById("sendBtn");
    const generateQuizBtn = document.getElementById("generateQuizBtn"); // New Button
  
    // Simulate Table of Contents with topics and subtopics
    const tableOfContents = [
      {
        topic: "Introduction",
        subtopics: ["Overview", "Purpose", "How to Use"],
      },
      {
        topic: "Chapter 1: Getting Started",
        subtopics: ["Setup", "Basic Concepts", "First Steps"],
      },
      {
        topic: "Chapter 2: Advanced Topics",
        subtopics: ["Deep Dive", "Best Practices", "Common Issues"],
      },
      {
        topic: "Conclusion",
        subtopics: ["Summary", "Next Steps", "Further Reading"],
      },
    ];
  
    // Build TOC with topics and subtopics
    tableOfContents.forEach((item) => {
      const li = document.createElement("li");
      li.textContent = item.topic;
      li.setAttribute("data-expanded", "false");
  
      // Create a nested list for subtopics
      const subUl = document.createElement("ul");
      item.subtopics.forEach((subtopic) => {
        const subLi = document.createElement("li");
        subLi.textContent = subtopic;
        subUl.appendChild(subLi);
      });
  
      subUl.style.display = "none"; // Initially hide subtopics
      li.appendChild(subUl);
      toc.appendChild(li);
  
      // Add click event to toggle subtopics
      li.addEventListener("click", (e) => {
        e.stopPropagation(); // Prevent event bubbling
        const isExpanded = li.getAttribute("data-expanded") === "true";
        li.setAttribute("data-expanded", !isExpanded);
        subUl.style.display = isExpanded ? "none" : "block";
      });
    });
  
    // Chatbot logic
    sendBtn.addEventListener("click", () => {
      const userMessage = userInput.value.trim();
      if (userMessage) {
        // Display user message
        addMessage("user", userMessage);
  
        // Simulate bot response
        setTimeout(() => {
          const botResponse = generateBotResponse(userMessage);
          addMessage("bot", botResponse);
        }, 1000);
  
        // Clear input
        userInput.value = "";
      }
    });
  
    // Handle the "Generate Quiz" button
    generateQuizBtn.addEventListener("click", (e) => {
      e.preventDefault();  // Prevent form submission (if it’s part of a form)
      
      // Navigate to the quiz page after clicking the "Generate Quiz" button
      window.location.href = "quizForm.html"; // Redirect to the quiz page
    });
  
    // Add a message to the chat
    function addMessage(sender, message) {
      const messageDiv = document.createElement("div");
      messageDiv.classList.add("chat-message");
      messageDiv.classList.add(sender === "user" ? "user-message" : "bot-message");
      messageDiv.textContent = message;
      chatBody.appendChild(messageDiv);
      chatBody.scrollTop = chatBody.scrollHeight; // Scroll to the bottom
    }
  
    // Generate a simple bot response
    function generateBotResponse(userMessage) {
      // Basic responses
      if (userMessage.toLowerCase().includes("hello")) {
        return "Hi there! How can I assist you?";
      } else if (userMessage.toLowerCase().includes("help")) {
        return "Sure! Please provide more details about your query.";
      } else {
        return "I'm here to help! Could you clarify your question?";
      }
    }
});

