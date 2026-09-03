import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Workspace from './pages/Workspace';
import NotFound from './pages/NotFound';
import BackgroundBlobs from './components/BackgroundBlobs';
import { WorkspaceProvider } from './context/WorkspaceContext';
import { ToastProvider } from './context/ToastContext';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <WorkspaceProvider>
        <div className="app-container">
          <BackgroundBlobs />
          <main className="main-content">
            <Routes>
              <Route path="/" element={<Workspace tab="overview" />} />
              <Route path="/endpoints" element={<Workspace tab="endpoints" />} />
              <Route path="/databases" element={<Workspace tab="databases" />} />
              <Route path="/playground" element={<Workspace tab="playground" />} />
              <Route path="/results" element={<Workspace tab="results" />} />
              <Route path="/tests" element={<Workspace tab="tests" />} />
              <Route path="/changes" element={<Workspace tab="changes" />} />
              <Route path="/projects/:projectId" element={<Workspace tab="overview" />} />
              <Route path="/projects/:projectId/:tab" element={<Workspace />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </main>
        </div>
        </WorkspaceProvider>
      </ToastProvider>
    </BrowserRouter>
  );
}

export default App;
