import { useLanguage } from '@/lib/i18n/language-context';

export function ConfigPanel() {
    const { t, language, setLanguage } = useLanguage();

    return (
        <div className="bg-neutral-950 border border-neutral-800">
            {/* Header */}
            <div className="border-b border-neutral-800 px-4 py-2.5 bg-neutral-900">
                <h2 className="text-sm font-semibold text-white">{t.config.title}</h2>
            </div>

            <div className="p-6">
                {/* General Settings Section */}
                <div className="space-y-6">
                    <div>
                        <h3 className="text-sm font-medium text-white mb-4">{t.config.generalSettings}</h3>

                        {/* Language Selector */}
                        <div className="bg-neutral-900 border border-neutral-800 p-4">
                            <div className="mb-3">
                                <label className="text-xs font-medium text-white">{t.config.language}</label>
                                <p className="text-[11px] text-neutral-500 mt-1">{t.config.languageDescription}</p>
                            </div>

                            <div className="flex space-x-2">
                                <button
                                    onClick={() => setLanguage('en')}
                                    className={`flex-1 px-4 py-2.5 text-sm font-medium transition-all ${language === 'en'
                                        ? 'bg-blue-600 text-white border border-blue-500'
                                        : 'bg-neutral-800 text-neutral-400 border border-neutral-700 hover:bg-neutral-750 hover:text-neutral-300'
                                        }`}
                                >
                                    {t.config.english}
                                </button>
                                <button
                                    onClick={() => setLanguage('es')}
                                    className={`flex-1 px-4 py-2.5 text-sm font-medium transition-all ${language === 'es'
                                        ? 'bg-blue-600 text-white border border-blue-500'
                                        : 'bg-neutral-800 text-neutral-400 border border-neutral-700 hover:bg-neutral-750 hover:text-neutral-300'
                                        }`}
                                >
                                    {t.config.spanish}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
