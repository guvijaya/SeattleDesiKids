export type LangCode = 'english' | 'hindi' | 'telugu' | 'marathi' | 'kannada' | 'tamil';

export const LANGUAGES: Record<LangCode, {
  code: LangCode;
  label: string;
  nativeLabel: string;
  htmlLang: string;
  color: string;
  font: string | null;
  unavailableMessage: string;
  availableInText: string;
}> = {
  english: {
    code: 'english',
    label: 'English',
    nativeLabel: 'English',
    htmlLang: 'en',
    color: 'var(--color-lang-en)',
    font: null,
    unavailableMessage: "This essay hasn't been translated to English yet.",
    availableInText: 'Read it in:',
  },
  hindi: {
    code: 'hindi',
    label: 'Hindi',
    nativeLabel: 'हिन्दी',
    htmlLang: 'hi',
    color: 'var(--color-lang-hi)',
    font: 'Noto Serif Devanagari',
    unavailableMessage: 'यह निबंध अभी हिंदी में उपलब्ध नहीं है।',
    availableInText: 'इसे इसमें पढ़ें:',
  },
  telugu: {
    code: 'telugu',
    label: 'Telugu',
    nativeLabel: 'తెలుగు',
    htmlLang: 'te',
    color: 'var(--color-lang-te)',
    font: 'Noto Serif Telugu',
    unavailableMessage: 'ఈ వ్యాసం ఇంకా తెలుగులో అనువదించబడలేదు.',
    availableInText: 'దీన్ని ఇందులో చదవండి:',
  },
  marathi: {
    code: 'marathi',
    label: 'Marathi',
    nativeLabel: 'मराठी',
    htmlLang: 'mr',
    color: 'var(--color-lang-mr)',
    font: 'Noto Serif Devanagari',
    unavailableMessage: 'हा निबंध अद्याप मराठीत अनुवादित केलेला नाही.',
    availableInText: 'हे यात वाचा:',
  },
  kannada: {
    code: 'kannada',
    label: 'Kannada',
    nativeLabel: 'ಕನ್ನಡ',
    htmlLang: 'kn',
    color: 'var(--color-lang-kn)',
    font: 'Noto Serif Kannada',
    unavailableMessage: 'ಈ ಪ್ರಬಂಧವನ್ನು ಇನ್ನೂ ಕನ್ನಡಕ್ಕೆ ಅನುವಾದಿಸಲಾಗಿಲ್ಲ.',
    availableInText: 'ಇದನ್ನು ಇಲ್ಲಿ ಓದಿ:',
  },
  tamil: {
    code: 'tamil',
    label: 'Tamil',
    nativeLabel: 'தமிழ்',
    htmlLang: 'ta',
    color: 'var(--color-lang-ta)',
    font: 'Noto Serif Tamil',
    unavailableMessage: 'இந்த கட்டுரை இன்னும் தமிழில் மொழிபெயர்க்கப்படவில்லை.',
    availableInText: 'இதை இங்கே படிக்கவும்:',
  },
};

export const LANGUAGE_ORDER: LangCode[] = ['tamil', 'english', 'hindi', 'telugu', 'marathi', 'kannada'];

export function getLang(code: string): LangCode {
  if (code in LANGUAGES) return code as LangCode;
  return 'english';
}
