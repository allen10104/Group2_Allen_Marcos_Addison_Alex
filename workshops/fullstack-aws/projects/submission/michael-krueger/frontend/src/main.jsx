import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// StrictMode is development only and does not ship in a production build.
// It deliberately mounts every component twice, which is worth knowing here
// because it means NoticeList fetches twice on load during development. That
// is the intended behaviour, not a bug: it is how React surfaces effects
// that are not safe to run more than once.
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
