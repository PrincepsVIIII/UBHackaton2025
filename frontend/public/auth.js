// auth.js — minimal Auth0 SPA setup
let auth0 = null;

async function configureAuth() {
  const resp = await fetch('/auth_config.json');
  const cfg = await resp.json();

  auth0 = await createAuth0Client({
    domain: cfg.domain,
    client_id: cfg.clientId,
    authorizationParams: cfg.authorizationParams
  });

  // If returning from Auth0 redirect
  if (window.location.search.includes('code=') && window.location.search.includes('state=')) {
    try {
      await auth0.handleRedirectCallback();
    } catch (e) {
      console.error('Callback handling failed', e);
    }
    // keep user on this page (callback is login.html), remove query params
    window.history.replaceState({}, document.title, '/login.html');
  }

  const isAuth = await auth0.isAuthenticated();
  if (isAuth) {
    const user = await auth0.getUser();
    // call page-defined hook
    if (window.onSignedIn) window.onSignedIn(user);
    document.getElementById('btnLogin').style.display = 'none';
    document.getElementById('btnLogout').style.display = 'inline-block';
  } else {
    if (window.onSignedOut) window.onSignedOut();
    document.getElementById('btnLogin').style.display = 'inline-block';
    document.getElementById('btnLogout').style.display = 'none';
  }

  // wire buttons
  document.getElementById('btnLogin').onclick = async () => {
    await auth0.loginWithRedirect({
      authorizationParams: { redirect_uri: cfg.authorizationParams.redirect_uri }
    });
  };
  document.getElementById('btnLogout').onclick = () => {
    auth0.logout({ logoutParams: { returnTo: cfg.authorizationParams.redirect_uri }});
  };
}

// init
window.addEventListener('load', () => configureAuth());
