import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { LandingPage } from '@/features/landing/landing-page';
import { DashboardPage } from '@/features/dashboard/dashboard-page';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
      </Routes>
    </BrowserRouter>
  );
}
