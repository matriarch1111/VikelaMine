(() => {
    const languageSelect = document.getElementById('language');
    const status = document.getElementById('languageStatus');
    const csrfToken = () => {
        const cookie = document.cookie.split(';').map(item => item.trim()).find(item => item.startsWith('csrftoken='));
        return cookie ? decodeURIComponent(cookie.slice('csrftoken='.length)) : '';
    };

    function collectInterfaceText() {
        const targets = [];
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
            acceptNode(node) {
                const parent = node.parentElement;
                if (!parent || !node.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
                if (parent.closest('script,style,option,[data-translation-skip],.report-row,.sos-alert-row,.report-original,.voice-transcript,.report-translation')) return NodeFilter.FILTER_REJECT;
                const raw = node.nodeValue;
                const text = raw.trim();
                const leading = raw.slice(0, raw.indexOf(text));
                const trailing = raw.slice(raw.indexOf(text) + text.length);
                targets.push({get: () => text, set: value => { node.nodeValue = leading + value + trailing; }});
                return NodeFilter.FILTER_REJECT;
            }
        });
        while (walker.nextNode()) {}

        document.querySelectorAll('input[placeholder],textarea[placeholder],button[aria-label],input[aria-label],textarea[aria-label],button[title]').forEach(element => {
            ['placeholder', 'aria-label', 'title'].forEach(attribute => {
                const value = element.getAttribute(attribute);
                if (value && !element.closest('[data-translation-skip]')) {
                    targets.push({get: () => value, set: translated => element.setAttribute(attribute, translated)});
                }
            });
        });
        return targets;
    }

    function hashTexts(texts) {
        let hash = 2166136261;
        for (const character of texts.join('\u0000')) {
            hash ^= character.charCodeAt(0);
            hash = Math.imul(hash, 16777619);
        }
        return (hash >>> 0).toString(16);
    }

    const interfaceTargets = collectInterfaceText();
    const interfaceOriginals = interfaceTargets.map(target => target.get());

    async function applySiteLanguage(language) {
        document.documentElement.lang = language;
        if (language === 'en-US') {
            interfaceTargets.forEach((target, index) => target.set(interfaceOriginals[index]));
            if (status) status.textContent = '';
            return;
        }

        if (status) status.textContent = 'Translating interface...';
        const cacheKey = `vikela-ui-v1-${language}-${location.pathname}-${hashTexts(interfaceOriginals)}`;
        let translated;
        try {
            const cached = localStorage.getItem(cacheKey);
            if (cached) translated = JSON.parse(cached);
        } catch (error) {
            localStorage.removeItem(cacheKey);
        }

        if (!translated) {
            try {
                const response = await fetch('/api/translate-interface/', {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrfToken()},
                    body: JSON.stringify({texts: interfaceOriginals, target_language: language})
                });
                const result = await response.json();
                if (!response.ok) throw new Error(result.error || 'Interface translation failed.');
                translated = result.translations;
                try {
                    localStorage.setItem(cacheKey, JSON.stringify(translated));
                } catch (error) {
                    console.warn('Could not cache translated interface text.', error);
                }
            } catch (error) {
                if (status) status.textContent = error.message;
                return;
            }
        }

        if (!Array.isArray(translated) || translated.length !== interfaceTargets.length) {
            if (status) status.textContent = 'Translation returned an incomplete page.';
            return;
        }
        interfaceTargets.forEach((target, index) => target.set(translated[index]));
        if (status) status.textContent = '';
    }

    const savedLanguage = localStorage.getItem('vikela-language') || 'en-US';
    if (languageSelect && Array.from(languageSelect.options).some(option => option.value === savedLanguage)) {
        languageSelect.value = savedLanguage;
        applySiteLanguage(savedLanguage);
    }

    languageSelect?.addEventListener('change', () => {
        localStorage.setItem('vikela-language', languageSelect.value);
        document.dispatchEvent(new CustomEvent('vikela-language-change', {detail: {language: languageSelect.value}}));
        applySiteLanguage(languageSelect.value);
    });
})();