// Mock: These would come from backend or localStorage
const totalMarks = 10;
const obtainedMarks = 7;

const userAnswers = [
  { question: "What is AI?", answer: "Artificial Intelligence" },
  { question: "What is 2+2?", answer: "5" }, // wrong
  { question: "Capital of France?", answer: "Paris" }
];

const correctAnswers = [
  { question: "What is AI?", answer: "Artificial Intelligence" },
  { question: "What is 2+2?", answer: "4" },
  { question: "Capital of France?", answer: "Paris" }
];

document.getElementById("total-marks").textContent = totalMarks;
document.getElementById("obtained-marks").textContent = obtainedMarks;
const percentage = (obtainedMarks / totalMarks) * 100;
document.getElementById("percentage").textContent = percentage.toFixed(2) + "%";

// Chart
const ctx = document.getElementById('resultChart').getContext('2d');
new Chart(ctx, {
  type: 'doughnut',
  data: {
    labels: ['Obtained', 'Remaining'],
    datasets: [{
      data: [obtainedMarks, totalMarks - obtainedMarks],
      backgroundColor: ['#4caf50', '#f44336'],
    }]
  },
  options: {
    responsive: true,
    plugins: {
      legend: { position: 'bottom' }
    }
  }
});

// Call GPT API
async function getGPTFeedback(userAnswers, correctAnswers, score, total) {
  const payload = {
    model: "gpt-4",
    messages: [
      {
        role: "system",
        content: "You are a kind and encouraging quiz evaluator. Provide detailed feedback for wrong answers and give an overall motivational message."
      },
      {
        role: "user",
        content: `A student has completed a quiz. Here are their answers vs correct ones:\n\n${userAnswers.map((ua, idx) => {
          return `Q: ${ua.question}\nStudent: ${ua.answer}\nCorrect: ${correctAnswers[idx].answer}`;
        }).join("\n\n")}\n\nThe student scored ${score} out of ${total}. Give performance feedback and guidance.`
      }
    ]
  };

  const response = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      "Authorization": "Bearer YOUR_API_KEY",
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  const data = await response.json();
  const feedback = data.choices[0].message.content;
  document.getElementById("feedback").textContent = feedback;
}



// Call the function
getGPTFeedback(userAnswers, correctAnswers, obtainedMarks, totalMarks);
