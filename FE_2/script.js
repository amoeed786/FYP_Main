document.addEventListener("DOMContentLoaded", () => {
    const fileUpload = document.getElementById("fileUpload");
    const fileInfo = document.getElementById("fileInfo");
    const uploadForm = document.getElementById("uploadForm");
  
    // Display selected file details
    fileUpload.addEventListener("change", (event) => {
      const file = event.target.files[0];
      if (file) {
        fileInfo.textContent = `Selected file: ${file.name} (${(file.size / 1024).toFixed(2)} KB)`;
      } else {
        fileInfo.textContent = "No file selected";
      }
    });
  
    uploadForm.addEventListener("submit", (event) => {
        event.preventDefault();
        const file = fileUpload.files[0];
        if (file) {

      
          // Redirect to the Document Viewer Page
          window.location.href = "uploaded.html";
        } else {
          alert("Please select a file to upload.");
        }
      });
      
  });
  