import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LandingPage from './components/LandingPage';
import CandidatePage from './components/CandidatePage';
import RecruiterPage from './components/RecruiterPage';
import ErrorBoundary from './components/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/candidate" element={<CandidatePage />} />
          <Route path="/recruiter" element={<RecruiterPage />} />
        </Routes>
      </Router>
    </ErrorBoundary>
  );
}

export default App;

