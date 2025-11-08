// auth.js
let auth0Client = null;

async function configureClient() {
  const response = await fetch("/auth_config.json");
  const config = await response.json();

  auth0Client = await createAuth0Client({
    domain: config.domain,
    client_id: config.clientId,
    authorizationParams: config.authorizationParams
  });
}

async function login() {
  await auth0Client.loginWithRedirect();
}

async function logout() {
  await auth0Client.logout({
    logoutParams: {
      returnTo: "http://localhost:3000/login.html"
    }
  });
}

async function handleAuthCallback() {
  const query = window.location.search;
  if (query.includes("code=") && query.includes("state=")) {
    await auth0Client.handleRedirectCallback();
    window.history.replaceState({}, document.title, "/login.html");
  }

  const isAuthenticated = await auth0Client.isAuthenticated();
  if (isAuthenticated) {
    const user = await auth0Client.getUser();
    handleUserRedirect(user);
  }
}

function handleUserRedirect(user) {
  // 👇 Assuming you store user roles in a custom claim like this:
  const roles = user["https://yourdomain.com/roles"] || [];

  if (roles.includes("user")) {
    window.location.href = "/submit-report.html";
  } else if (roles.includes("volunteer")) {
    window.location.href = "/volunteer-view.html";
  } else {
    window.location.href = "/guest-view.html";
  }
}

// Initialize on page load
window.onload = async () => {
  await configureClient();
  await handleAuthCallback();
};
