<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>VikelaMine — Sign in</title>
<style>
:root{
  --red:#e72828;
  --bg:#1A1F26;
  --panel:#232A34;
  --panel2:#2A323D;
  --line:#2E353F;
  --muted:#9AA0A8;
}
*{box-sizing:border-box}
body{margin:0;min-height:100vh;background:var(--bg);color:#fff;font-family:ui-sans-serif,system-ui,sans-serif;display:grid;place-items:center;padding:20px}
.login-card{width:100%;max-width:360px;padding:36px 32px;background:var(--panel);border:1px solid var(--line);border-radius:12px}
.logo{margin:0 0 20px;font-size:24px;font-weight:800}
.logo b{color:var(--red)}
label{display:block;margin:14px 0 6px;color:var(--muted);font-size:13px}
input{width:100%;padding:11px 12px;border:1px solid var(--line);border-radius:8px;background:var(--panel2);color:#fff;font:inherit}
input:focus{outline:2px solid var(--red);outline-offset:2px}
button{width:100%;margin-top:20px;padding:11px 16px;border:0;border-radius:8px;background:var(--red);color:#fff;font:inherit;font-weight:700;cursor:pointer}
button:hover{filter:brightness(1.08)}
</style>
</head>
<body>
<main class="login-card">
  <h1 class="logo">Vike<b>la</b>Mine</h1>
  <form id="login-form">
    <label for="login-email">Email</label>
    <input type="email" id="login-email" placeholder="admin@vikelamine.co.za" autocomplete="username" required>
    <label for="login-password">Password</label>
    <input type="password" id="login-password" placeholder="Password" autocomplete="current-password" required>
    <button type="submit">Log in</button>
  </form>
</main>
<script>
document.getElementById('login-form').addEventListener('submit', function(event){
  event.preventDefault();
  window.location.href = '/alerts.html';
});
</script>
</body>
</html>