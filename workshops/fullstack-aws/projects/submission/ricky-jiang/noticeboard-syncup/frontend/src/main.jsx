import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { ThemeProvider } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import { theme } from './theme.js'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
     {/* actually applies the theme to the entire application, allowing all MUI components to inherit the defined styles and colors. */}
    <ThemeProvider theme={theme}>
      {/* MUI own css reset component that provides a consistent baseline for styling across different browsers. 
      It helps to normalize styles and remove browser-specific inconsistencies,
       ensuring that the application looks and behaves consistently across various platforms. */}
      <CssBaseline />
      <App />
    </ThemeProvider>
  </StrictMode>,
)