import { RippleButton } from '@/components/shared/ripple-button';
import { ArrowRight } from 'lucide-react';

interface LandingCTAProps {
  /** Invoked when the user clicks the CTA; parent swaps to the dashboard view. */
  onEnterDashboard: () => void;
}

/**
 * Closing call-to-action band on the landing page.
 *
 * @param props.onEnterDashboard - Callback fired when the CTA button is clicked.
 */
export function LandingCTA({ onEnterDashboard }: LandingCTAProps) {
  return (
    <div className="px-6 py-20 bg-neutral-900 border-t border-neutral-800">
      <div className="max-w-3xl mx-auto text-center">
        <h2 className="text-3xl font-semibold text-white mb-4">
          Explore the Dashboard
        </h2>
        <p className="text-sm text-neutral-400 mb-8 max-w-2xl mx-auto">
          Inspect local magnetograms, current-index inference, model metrics, and research artifacts from the pipeline.
        </p>

        <RippleButton
          variant="primary"
          onClick={onEnterDashboard}
          className="!px-10 !py-4 text-base"
        >
          Enter Dashboard
          <ArrowRight className="w-5 h-5 ml-2" />
        </RippleButton>

        <div className="mt-12 pt-8 border-t border-neutral-800">
          <p className="text-xs text-neutral-600">
            Auralis • Data Engineering & Machine Learning Project • 2026
          </p>
        </div>
      </div>
    </div>
  );
}
