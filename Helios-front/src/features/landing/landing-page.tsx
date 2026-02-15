import { useNavigate } from 'react-router-dom';
import { LandingHero } from './landing-hero';
import { SystemOverview } from './system-overview';
import { ArchitectureDiagram } from './architecture-diagram';
import { ProjectDescription } from './project-description';
import { LandingCTA } from './landing-cta';

export function LandingPage() {
  const navigate = useNavigate();

  const handleEnterDashboard = () => {
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen bg-neutral-950">
      <LandingHero onEnterDashboard={handleEnterDashboard} />
      <SystemOverview />
      <ArchitectureDiagram />
      <ProjectDescription />
      <LandingCTA onEnterDashboard={handleEnterDashboard} />
    </div>
  );
}
