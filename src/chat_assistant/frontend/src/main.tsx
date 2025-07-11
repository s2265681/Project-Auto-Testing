import React from 'react';
import ReactDOM from 'react-dom/client';
import ChatApp from './components/ChatApp';
import './styles/globals.scss';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <ChatApp />
  </React.StrictMode>
);

// Hot Module Replacement
if (import.meta.hot) {
  import.meta.hot.accept();
} 