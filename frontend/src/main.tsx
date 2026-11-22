import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import { readThemeMode } from './theme/ThemeContext'

document.documentElement.dataset.theme = readThemeMode()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
