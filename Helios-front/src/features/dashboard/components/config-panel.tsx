import { useState } from 'react';
import { Globe, Bell, Cpu, Lock, Check } from 'lucide-react';
import { useLanguage } from '@/lib/i18n/language-context';

// ---------------------------------------------------------------------------
// Primitives
// ---------------------------------------------------------------------------

function SectionHeader({ icon: Icon, title, description }: {
  icon: typeof Globe; title: string; description: string;
}) {
  return (
    <div className="flex items-center gap-3 mb-4">
      <div className="w-9 h-9 rounded-lg bg-orange-500/15 flex items-center justify-center flex-shrink-0">
        <Icon className="w-4 h-4 text-orange-400" />
      </div>
      <div>
        <div className="text-[14px] font-semibold text-white">{title}</div>
        <div className="text-[11px] text-neutral-500">{description}</div>
      </div>
    </div>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between px-4 py-3.5 bg-neutral-800/40 border border-neutral-700/50 rounded-xl">
      <span className="text-[13px] text-neutral-300">{label}</span>
      <div className="flex items-center gap-2">{children}</div>
    </div>
  );
}

function Toggle({ on, onChange }: { on: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      onClick={() => onChange(!on)}
      className={`relative w-11 h-6 rounded-full transition-colors duration-200 ${on ? 'bg-orange-500' : 'bg-neutral-600'}`}
    >
      <span className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200 ${on ? 'translate-x-5' : 'translate-x-0'}`} />
    </button>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function ConfigPanel() {
  const { language, setLanguage, t } = useLanguage();
  const s = t.settings;

  const [notif, setNotif] = useState({ highRisk: true, slackFail: true, digest: false });

  const DEVICE    = 'mps (Apple Silicon)';
  const BATCH     = '16';
  const PRECISION = 'float32';
  const API_KEY   = 'hk_live_••••••••••••••a3f2';

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

      {/* ── TOP-LEFT: Language ───────────────────────────────────── */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
        <SectionHeader icon={Globe} title={s.language} description={s.languageDesc} />
        <div className="grid grid-cols-2 gap-3">
          {([
            { code: 'en', label: s.english,  sub: s.englishSub  },
            { code: 'es', label: s.español,  sub: s.españolSub  },
          ] as const).map(({ code, label, sub }) => {
            const active = language === code;
            return (
              <button
                key={code}
                onClick={() => setLanguage(code)}
                className={`flex items-center justify-between px-4 py-3.5 rounded-xl border transition-colors text-left ${
                  active
                    ? 'bg-orange-500/10 border-orange-500/50'
                    : 'bg-neutral-800/40 border-neutral-700/50 hover:border-neutral-600'
                }`}
              >
                <div>
                  <div className={`text-[14px] font-medium ${active ? 'text-white' : 'text-neutral-300'}`}>{label}</div>
                  <div className="text-[11px] text-neutral-500 mt-0.5">{sub}</div>
                </div>
                {active && (
                  <div className="w-6 h-6 rounded-full bg-orange-500 flex items-center justify-center flex-shrink-0">
                    <Check className="w-3.5 h-3.5 text-white" strokeWidth={2.5} />
                  </div>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* ── TOP-RIGHT: Runtime ──────────────────────────────────── */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
        <SectionHeader icon={Cpu} title={s.runtime} description={s.runtimeDesc} />
        <div className="space-y-2">
          <Row label={s.device}>
            <span className="text-[13px] font-mono text-neutral-300">{DEVICE}</span>
          </Row>
          <Row label={s.batchSize}>
            <span className="text-[13px] font-mono text-neutral-300">{BATCH}</span>
          </Row>
          <Row label={s.precision}>
            <span className="text-[13px] font-mono text-neutral-300">{PRECISION}</span>
          </Row>
        </div>
      </div>

      {/* ── BOTTOM-LEFT: Notifications ───────────────────────────── */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
        <SectionHeader icon={Bell} title={s.notifications} description={s.notificationsDesc} />
        <div className="space-y-2">
          <Row label={s.emailAlerts}>
            <Toggle on={notif.highRisk}  onChange={(v) => setNotif((p) => ({ ...p, highRisk: v }))} />
          </Row>
          <Row label={s.slackPush}>
            <Toggle on={notif.slackFail} onChange={(v) => setNotif((p) => ({ ...p, slackFail: v }))} />
          </Row>
          <Row label={s.weeklyDigest}>
            <Toggle on={notif.digest}    onChange={(v) => setNotif((p) => ({ ...p, digest: v }))} />
          </Row>
        </div>
      </div>

      {/* ── BOTTOM-RIGHT: Security ───────────────────────────────── */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
        <SectionHeader icon={Lock} title={s.security} description={s.securityDesc} />
        <div className="space-y-2">
          <Row label={s.apiKey}>
            <span className="text-[13px] font-mono text-neutral-400">{API_KEY}</span>
          </Row>
          <Row label={s.twoFa}>
            <span className="text-[13px] font-mono text-green-400">{s.enabled}</span>
          </Row>
        </div>
      </div>

    </div>
  );
}
