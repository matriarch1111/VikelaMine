function reportToolsCookie(name) {
    const cookie = document.cookie.split(';').map(item => item.trim()).find(item => item.startsWith(name + '='));
    return cookie ? decodeURIComponent(cookie.slice(name.length + 1)) : '';
}

function filterReports() {
    const type = document.getElementById('reportFilterType')?.value || '';
    const priority = document.getElementById('reportFilterPriority')?.value || '';
    const status = document.getElementById('reportFilterStatus')?.value || '';
    const date = document.getElementById('reportFilterDate')?.value || '';
    const query = document.getElementById('reportFilterSearch')?.value.trim().toLowerCase() || '';
    document.querySelectorAll('.report-row').forEach(row => {
        const searchable = [row.dataset.reportText, row.dataset.reportPerson, row.dataset.reportLocation].join(' ').toLowerCase();
        const visible = (!type || row.dataset.reportType === type)
            && (!priority || row.dataset.reportPriority === priority)
            && (!status || row.dataset.reportStatus === status)
            && (!date || row.dataset.reportDate === date)
            && (!query || searchable.includes(query));
        row.hidden = !visible;
    });
}
['reportFilterType', 'reportFilterPriority', 'reportFilterStatus', 'reportFilterDate', 'reportFilterSearch'].forEach(id => {
    document.getElementById(id)?.addEventListener('input', filterReports);
    document.getElementById(id)?.addEventListener('change', filterReports);
});

document.querySelectorAll('.translate-report').forEach(button => button.addEventListener('click', async () => {
    const row = button.closest('.report-row');
    const output = row.querySelector('.report-translation');
    const source = row.querySelector('.voice-transcript')?.textContent.trim() || row.dataset.reportText;
    output.textContent = 'Translating...';

    try {
        const response = await fetch('/api/translate-report/', {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': reportToolsCookie('csrftoken')
            },
            body: JSON.stringify({
                text: source,
                source_language: row.dataset.reportLanguage,
                target_language: row.querySelector('.report-target').value
            })
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || 'Translation failed.');
        output.textContent = result.translation;
    } catch (error) {
        output.textContent = error.message;
    }
}));

document.querySelectorAll('.speak-report').forEach(button => button.addEventListener('click', async () => {
    const row = button.closest('.report-row');
    const translated = row.querySelector('.report-translation').textContent.trim();
    const text = translated || row.querySelector('.voice-transcript')?.textContent.trim() || row.dataset.reportText;
    const language = translated ? row.querySelector('.report-target').value : row.dataset.reportLanguage;

    if ('speechSynthesis' in window) {
        speechSynthesis.cancel();
        const speech = new SpeechSynthesisUtterance(text);
        speech.lang = language;
        speechSynthesis.speak(speech);
        return;
    }

    const payload = new FormData();
    payload.append('text', text);
    payload.append('language', language);
    try {
        const response = await fetch('/api/text-to-speech/', {
            method: 'POST',
            credentials: 'same-origin',
            body: payload,
            headers: { 'X-CSRFToken': reportToolsCookie('csrftoken') }
        });
        if (!response.ok) throw new Error('Text-to-speech is unavailable.');
        const audio = new Audio(URL.createObjectURL(await response.blob()));
        await audio.play();
    } catch (error) {
        row.querySelector('.report-translation').textContent = error.message;
    }
}));

document.querySelectorAll('.transcribe-report').forEach(button => button.addEventListener('click', async () => {
    const row = button.closest('.report-row');
    const audio = row.querySelector('audio');
    const output = row.querySelector('.voice-transcript');
    button.disabled = true;
    output.textContent = 'Transcribing voice note...';

    try {
        const audioBlob = await fetch(audio.src).then(response => {
            if (!response.ok) throw new Error('Voice note could not be loaded.');
            return response.blob();
        });
        const filename = new URL(audio.src).pathname.split('/').pop() || 'voice-note.webm';
        const payload = new FormData();
        payload.append('audio', audioBlob, filename);
        const response = await fetch('/api/transcribe-voice/', {
            method: 'POST',
            credentials: 'same-origin',
            body: payload,
            headers: { 'X-CSRFToken': reportToolsCookie('csrftoken') }
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || 'Transcription failed.');
        output.textContent = result.transcript;
    } catch (error) {
        output.textContent = error.message;
    } finally {
        button.disabled = false;
    }
}));