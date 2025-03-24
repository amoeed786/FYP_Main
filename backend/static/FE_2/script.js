document.getElementById("uploadForm").addEventListener("submit", function(event) {
  event.preventDefault();
  
  let formData = new FormData();
  let fileInput = document.getElementById("fileUpload");

  if (fileInput.files.length === 0) {
      alert("Please select a file.");
      return;
  }

  formData.append("file", fileInput.files[0]);

  fetch("/api/documents/upload/", { // Ensure backend has this API
      method: "POST",
      body: formData
  })
  .then(response => response.json())
  .then(data => {
      console.log("Upload Response:", data);
      alert("File uploaded successfully!");
      window.location.href = "/static/FE_2/uploaded.html";
  })
  .catch(error => console.error("Upload Error:", error));
});
