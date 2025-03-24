document.addEventListener("DOMContentLoaded", () => {
    const urlParams = new URLSearchParams(window.location.search);
    const numMCQs = parseInt(urlParams.get("numMCQs"));
    const numShortQs = parseInt(urlParams.get("numShortQs"));
    const topicName = decodeURIComponent(urlParams.get("topicName"));
  
    document.getElementById("topicNameDisplay").textContent = topicName;
    const quizPaper = document.getElementById("quizPaper");
  
    // Generate MCQs with radio buttons
    for (let i = 1; i <= numMCQs; i++) {
      const mcqQuestion = document.createElement("div");
      mcqQuestion.classList.add("question-block");
      mcqQuestion.innerHTML = `
        <p class="question">${i}. What is the capital of Country ${i}?</p>
        <ul class="options">
          <li><label><input type="radio" name="q${i}"> Option A</label></li>
          <li><label><input type="radio" name="q${i}"> Option B</label></li>
          <li><label><input type="radio" name="q${i}"> Option C</label></li>
          <li><label><input type="radio" name="q${i}"> Option D</label></li>
        </ul>
      `;
      quizPaper.appendChild(mcqQuestion);
    }
  
    // Generate Short Questions with text areas
    for (let i = 1; i <= numShortQs; i++) {
      const shortQuestion = document.createElement("div");
      shortQuestion.classList.add("question-block");
      shortQuestion.innerHTML = `
        <p class="question">${numMCQs + i}. Describe the concept of ${topicName}.</p>
        <textarea class="short-answer" rows="4" placeholder="Write your answer here..."></textarea>
      `;
      quizPaper.appendChild(shortQuestion);
    }
  
    // Modal and Download Handlers
    const modal = document.getElementById("formatModal");
    const closeModal = document.getElementById("closeModal");
    const downloadBtn = document.getElementById("download-btn");
  
    // Show Modal on Download Icon Click
    downloadBtn.addEventListener("click", (e) => {
      e.preventDefault();
      modal.style.display = "block";
    });
  
    // Close Modal
    closeModal.addEventListener("click", () => {
      modal.style.display = "none";
    });
  
    // Download Functions
    const downloadContent = (format) => {
      let content = `Topic: ${topicName}\n\n`;
  
      // Add MCQs with options to the content
      for (let i = 1; i <= numMCQs; i++) {
        content += `${i}. What is the capital of Country ${i}?\n`;
        content += `  - A) Option A\n  - B) Option B\n  - C) Option C\n  - D) Option D\n\n`;
      }
  
      // Add short questions to the content
      for (let i = 1; i <= numShortQs; i++) {
        content += `${numMCQs + i}. Describe the concept of ${topicName}.\n\n`;
      }
  
      if (format === "txt") {
        const blob = new Blob([content], { type: "text/plain" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `${topicName}-Quiz.txt`;
        link.click();
      } else if (format === "doc") {
        const blob = new Blob(
          [`<html><body><pre>${content}</pre></body></html>`],
          { type: "application/msword" }
        );
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `${topicName}-Quiz.doc`;
        link.click();
      } else if (format === "pdf") {
        const pdfWindow = window.open("", "_blank");
        pdfWindow.document.write(`<pre>${content}</pre>`);
        pdfWindow.print();
      }
  
      modal.style.display = "none";
    };
  
    // Attach Event Listeners to Format Buttons
    document.getElementById("download-txt").addEventListener("click", () => downloadContent("txt"));
    document.getElementById("download-doc").addEventListener("click", () => downloadContent("doc"));
    document.getElementById("download-pdf").addEventListener("click", () => downloadContent("pdf"));
  });
  