/**
 * Browser entry point - the one place the React tree is attached to the page.
 *
 * `#root` is the empty div in index.html. Vite injects this file as a module script,
 * so everything below runs after the DOM exists and no DOMContentLoaded wrapper is
 * needed.
 *
 * StrictMode is DEVELOPMENT-ONLY behaviour and it is deliberately kept on: it renders
 * every component twice and runs each effect twice, which is how you find effects that
 * are not safe to re-run. That double-fetch you see in the network tab locally is this,
 * not a bug - and it is exactly what surfaced the need for useCallback around
 * loadNotices in App.jsx. It disappears in the production build, so it costs the
 * deployed site nothing.
 */
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';

// createRoot is the React 18+ API. The older ReactDOM.render is deprecated and opts you
// out of concurrent rendering.
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
