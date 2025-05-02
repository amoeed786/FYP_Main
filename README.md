# FYP_Main

<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>GitHub Repository Structure</title>
  <style>
    body {
      font-family: 'Segoe UI', sans-serif;
      background-color: #f4f7f9;
      padding: 40px;
    }

    .container {
      max-width: 600px;
      margin: auto;
      background: #ffffff;
      border-radius: 12px;
      box-shadow: 0 4px 10px rgba(0,0,0,0.1);
      padding: 20px 30px;
    }

    h2 {
      text-align: center;
      color: #333;
      margin-bottom: 20px;
    }

    ul {
      list-style-type: none;
      padding-left: 0;
    }

    li {
      padding: 10px 15px;
      margin: 5px 0;
      background-color: #e7edf3;
      border-left: 6px solid #007acc;
      border-radius: 6px;
      font-weight: 500;
      color: #333;
    }

    .folder::before {
      content: "📁 ";
    }

    .file::before {
      content: "📄 ";
    }
  </style>
</head>
<body>
  <div class="container">
    <h2>📦 Project Repository Structure</h2>
    <ul>
      <li class="folder">core</li>
      <li class="file">db.sqlite3</li>
      <li class="file">db.sqlite3.bak</li>
      <li class="file">Dockerfile</li>
      <li class="file">manage.py</li>
      <li class="file">requirements.txt</li>
      <li class="file">requirements-2.txt</li>
      <li class="file">docker-compose.yml</li>
      <li class="folder">examigo</li>
      <li class="folder">media</li>
    </ul>
  </div>
</body>
</html>
