document.getElementById("quizForm").addEventListener("submit", function(event) {
  event.preventDefault();

  let numMCQs = document.getElementById("numMCQs").value;
  let numShortQs = document.getElementById("numShortQs").value;
  let topicName = document.getElementById("topicName").value;
  let bloomLevel = document.getElementById("bloomLevel").value; // Get Bloom’s level

  fetch("/api/quiz/generate/", {
      method: "POST",
      headers: {
          "Content-Type": "application/json"
      },
      body: JSON.stringify({
          topic: topicName,
          numMCQs: numMCQs,
          numShortQs: numShortQs,
          bloomLevel: bloomLevel
      })
  })
  .then(response => response.json())
  .then(data => {
      console.log("Quiz Response:", data);
      displayQuiz(data.quiz); // Call function to render quiz on frontend
  })
  .catch(error => console.error("Error:", error));
});

// Function to display quiz dynamically
function displayQuiz(quiz) {
  let quizContainer = document.getElementById("quizPaper");
  quizContainer.innerHTML = ""; // Clear old content

  quiz.mcqs.forEach((mcq, index) => {
      let questionBlock = document.createElement("div");
      questionBlock.classList.add("question-block");

      let questionText = document.createElement("p");
      questionText.innerHTML = `<strong>Q${index + 1}:</strong> ${mcq.question}`;
      questionBlock.appendChild(questionText);

      let optionsList = document.createElement("ul");
      mcq.options.forEach((option, key) => {
          let optionItem = document.createElement("li");
          optionItem.innerHTML = `<input type="radio" name="q${index}" value="${key}"> ${option}`;
          optionsList.appendChild(optionItem);
      });

      questionBlock.appendChild(optionsList);
      quizContainer.appendChild(questionBlock);
  });

  quiz.short_questions.forEach((shortQ, index) => {
      let questionBlock = document.createElement("div");
      questionBlock.classList.add("question-block");

      let questionText = document.createElement("p");
      questionText.innerHTML = `<strong>Q${index + quiz.mcqs.length + 1}:</strong> ${shortQ.question}`;
      questionBlock.appendChild(questionText);

      let answerBox = document.createElement("textarea");
      answerBox.setAttribute("rows", "2");
      answerBox.setAttribute("cols", "50");
      questionBlock.appendChild(answerBox);

      quizContainer.appendChild(questionBlock);
  });
}
