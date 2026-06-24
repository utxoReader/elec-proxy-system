import React from 'react';
import ReactDOM from 'react-dom/client';
import { I18nProvider } from 'react-aria-components';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <I18nProvider locale="zh-CN">
      <App />
    </I18nProvider>
  </React.StrictMode>,
);
