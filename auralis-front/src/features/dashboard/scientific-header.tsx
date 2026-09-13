import { Menu } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface ScientificHeaderProps {
  onMenuClick: () => void;
}

/**
 * Dashboard chrome shared by all tabs.
 *
 * Kept intentionally minimal: hamburger (mobile) + title/breadcrumb. The
 * search box and the sync-time / bell / refresh actions were removed at the
 * product's request across every tab.
 */
export function ScientificHeader({ onMenuClick }: ScientificHeaderProps) {
  const navigate = useNavigate();

  return (
    <header className="h-[56px] flex-shrink-0 bg-[#0d0d0d] border-b border-neutral-800/60 px-3 md:px-6 flex items-center gap-2 md:gap-4">

      {/* Hamburger — mobile only */}
      <button
        onClick={onMenuClick}
        className="md:hidden w-8 h-8 flex items-center justify-center rounded-lg text-neutral-500 hover:text-neutral-300 hover:bg-neutral-800 transition-colors flex-shrink-0"
        aria-label="Open menu"
      >
        <Menu className="w-4 h-4" />
      </button>

      {/* ── Left: Title + breadcrumb ───────────────────────────── */}
      <div className="flex-shrink-0">
        <button onClick={() => navigate('/')} className="text-left group">
          <div className="text-[13px] font-semibold text-white group-hover:text-neutral-200 transition-colors leading-tight">
            Solar Activity Analysis
          </div>
          <div className="hidden sm:flex items-center gap-1 text-[11px] text-neutral-500 mt-[1px]">
            <span>Auralis</span>
            <span className="text-neutral-700">›</span>
            <span>SDO-HMI</span>
          </div>
        </button>
      </div>
    </header>
  );
}
