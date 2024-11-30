document.addEventListener("DOMContentLoaded", () => {
    const quizForm = document.getElementById("quizForm");
  
    quizForm.addEventListener("submit", (event) => {
      event.preventDefault(); // Prevent form from reloading the page
  
      const numMCQs = document.getElementById("numMCQs").value;
      const numShortQs = document.getElementById("numShortQs").value;
      const topicName = document.getElementById("topicName").value;
  
      // Validate fields
      if (numMCQs && numShortQs && topicName) {
        // Redirect to quiz page with parameters
        const quizPageURL = `quiz.html?numMCQs=${numMCQs}&numShortQs=${numShortQs}&topicName=${encodeURIComponent(topicName)}`;
        window.location.href = quizPageURL;
      } else {
        alert("Please fill in all the fields!");
      }
    });
  });
  