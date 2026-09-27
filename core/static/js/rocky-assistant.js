(() => {
    const launcher = document.getElementById('rockyLauncher');
    const panel = document.getElementById('rockyPanel');
    const form = document.getElementById('rockyForm');
    const questionInput = document.getElementById('rockyQuestion');
    const messages = document.getElementById('rockyMessages');
    const status = document.getElementById('rockyStatus');
    let selectedReportRow = null;
    let rockyRecorder = null;
    let rockyMicrophone = null;
    let rockyAudioChunks = [];

    const copy = {
        'en-US': {needReport: 'Open the report form or choose a report first. Rocky only uses that report.', thinking: 'Rocky is reviewing the selected report...', voiceError: 'Voice input is not supported in this browser.'},
        'zu-ZA': {needReport: 'Vula ifomu lombiko noma ukhethe umbiko kuqala. URocky usebenzisa lowo mbiko kuphela.', thinking: 'URocky ubuyekeza umbiko okhethiwe...', voiceError: 'Ukufaka ngezwi akusekelwa kulesi siphequluli.'},
        'tn-ZA': {needReport: 'Bula foromo ya pego kgotsa tlhopha pego pele. Rocky o dirisa pego eo fela.', thinking: 'Rocky o sekaseka pego e e tlhophilweng...', voiceError: 'Go bua ga go tshegediwe mo browser eno.'},
        'af-ZA': {needReport: 'Maak die verslagvorm oop of kies eers n verslag. Rocky gebruik net daardie verslag.', thinking: 'Rocky beoordeel die gekose verslag...', voiceError: 'Stem invoer word nie in hierdie blaaier ondersteun nie.'},
        'ts-ZA': {needReport: 'Pfula fomo ya xiviko kumbe u hlawula xiviko ku sungula. Rocky u tirhisa xiviko xexo ntsena.', thinking: 'Rocky u kambisisa xiviko lexi hlawuriweke...', voiceError: 'Ku nghenisa hi rito a swi seketeriwi eka browser leyi.'}
    };

    function language() {
        const selected = document.getElementById('language')?.value || 'en-US';
        return ({en: 'en-US', zu: 'zu-ZA', af: 'af-ZA', tn: 'tn-ZA', ts: 'ts-ZA', st: 'st-ZA'})[selected] || selected;
    }

    function localized(key) {
        return (copy[language()] || copy['en-US'])[key];
    }

    function appendMessage(text, role) {
        const message = document.createElement('p');
        message.className = `rocky-message ${role}`;
        message.dataset.role = role;
        message.textContent = text;
        messages.appendChild(message);
        messages.scrollTop = messages.scrollHeight;
        return message;
    }

    async function speakReply(text) {
        if ('speechSynthesis' in window && 'SpeechSynthesisUtterance' in window) {
            try {
                await new Promise((resolve, reject) => {
                    const utterance = new SpeechSynthesisUtterance(text);
                    utterance.lang = language();
                    utterance.onend = resolve;
                    utterance.onerror = event => reject(new Error(event.error || 'Browser speech failed.'));
                    speechSynthesis.cancel();
                    speechSynthesis.speak(utterance);
                });
                return;
            } catch (error) {
                console.warn('Browser speech failed; trying server speech.', error);
            }
        }

        const payload = new FormData();
        payload.append('text', text);
        payload.append('language', language());
        const response = await fetch('/api/text-to-speech/', {
            method: 'POST',
            credentials: 'same-origin',
            body: payload
        });
        if (!response.ok) throw new Error('Speech playback is unavailable.');
        const audio = new Audio(URL.createObjectURL(await response.blob()));
        await audio.play();
    }

    async function transcribeRockyRecording(blob) {
        const extension = blob.type.includes('ogg') ? 'ogg' : blob.type.includes('mp4') ? 'm4a' : 'webm';
        const payload = new FormData();
        payload.append('audio', blob, `rocky-question.${extension}`);
        status.textContent = 'Transcribing your question...';
        const response = await fetch('/api/transcribe-voice/', {
            method: 'POST',
            credentials: 'same-origin',
            body: payload
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || 'Voice transcription failed.');
        status.textContent = '';
        await askRocky(result.transcript);
    }

    async function currentReportContext() {
        const reportForm = document.getElementById('hazardForm');
        if (reportForm) {
            const description = reportForm.querySelector('#description')?.value.trim() || '';
            const imageInput = reportForm.querySelector('#photo');
            const photo = typeof capturedPhotoBlob !== 'undefined' && capturedPhotoBlob ? capturedPhotoBlob : imageInput?.files[0];
            const voice = typeof audioBlob !== 'undefined' ? audioBlob : null;
            if (!description && !photo && !voice) return null;
            return {
                description,
                hazardType: reportForm.querySelector('#hazard_type')?.value || '',
                location: [reportForm.querySelector('#latitude')?.value, reportForm.querySelector('#longitude')?.value].filter(Boolean).join(', '),
                photo,
                voice
            };
        }

        if (!selectedReportRow) return null;
        const audio = selectedReportRow.querySelector('audio');
        let voice = null;
        if (audio?.src) {
            try {
                voice = await fetch(audio.src).then(response => response.ok ? response.blob() : null);
            } catch (error) {
                console.warn('Could not load the selected report voice note.', error);
            }
        }
        const description = selectedReportRow.querySelector('.voice-transcript')?.textContent.trim()
            || selectedReportRow.dataset.reportText
            || '';
        if (!description && !voice) return null;
        return {
            description,
            hazardType: selectedReportRow.dataset.reportType || '',
            location: selectedReportRow.dataset.reportLocation || '',
            photo: null,
            voice
        };
    }

    async function askRocky(question) {
        const text = question.trim();
        if (!text) return;
        const context = await currentReportContext();
        if (!context) {
            appendMessage(localized('needReport'), 'assistant');
            return;
        }

        const history = Array.from(messages.querySelectorAll('[data-role]'))
            .slice(-8)
            .map(message => ({role: message.dataset.role, content: message.textContent}));
        appendMessage(text, 'user');
        const pending = appendMessage(localized('thinking'), 'assistant');
        const payload = new FormData();
        payload.append('message', text);
        payload.append('description', context.description);
        payload.append('hazard_type', context.hazardType);
        payload.append('location_name', context.location);
        payload.append('language', language());
        payload.append('history', JSON.stringify(history));
        if (context.photo) payload.append('photo', context.photo, context.photo.name || 'report-image.jpg');
        if (context.voice) payload.append('voice_note', context.voice, 'report-voice.webm');

        try {
            const cookie = document.cookie.split(';').map(item => item.trim()).find(item => item.startsWith('csrftoken='));
            const response = await fetch('/api/ai-chat/', {
                method: 'POST',
                credentials: 'same-origin',
                body: payload,
                headers: {'X-CSRFToken': cookie ? decodeURIComponent(cookie.slice('csrftoken='.length)) : ''}
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || 'Rocky is unavailable.');
            pending.textContent = result.reply;
            await speakReply(result.reply);
        } catch (error) {
            pending.textContent = error.message;
        }
    }

    launcher.addEventListener('click', () => {
        const open = panel.style.display !== 'flex';
        panel.style.display = open ? 'flex' : 'none';
        launcher.setAttribute('aria-expanded', String(open));
        if (open) questionInput.focus();
    });
    document.getElementById('rockyClose').addEventListener('click', () => {
        panel.style.display = 'none';
        launcher.setAttribute('aria-expanded', 'false');
    });
    form.addEventListener('submit', event => {
        event.preventDefault();
        const question = questionInput.value;
        questionInput.value = '';
        askRocky(question);
    });
    document.getElementById('rockyVoice').addEventListener('click', async event => {
        const button = event.currentTarget;
        if (rockyRecorder?.state === 'recording') {
            rockyRecorder.stop();
            button.textContent = '🎤';
            button.setAttribute('aria-label', 'Record a voice question');
            return;
        }
        const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (Recognition) {
            const recognition = new Recognition();
            recognition.lang = language();
            recognition.onresult = event => askRocky(event.results[0][0].transcript);
            recognition.onerror = () => { status.textContent = localized('voiceError'); };
            recognition.start();
            return;
        }

        if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
            status.textContent = localized('voiceError');
            return;
        }
        try {
            rockyMicrophone = await navigator.mediaDevices.getUserMedia({audio: true});
            rockyAudioChunks = [];
            rockyRecorder = new MediaRecorder(rockyMicrophone);
            rockyRecorder.ondataavailable = recordingEvent => {
                if (recordingEvent.data.size) rockyAudioChunks.push(recordingEvent.data);
            };
            rockyRecorder.onstop = async () => {
                const blob = new Blob(rockyAudioChunks, {type: rockyRecorder.mimeType || 'audio/webm'});
                rockyMicrophone?.getTracks().forEach(track => track.stop());
                rockyMicrophone = null;
                rockyRecorder = null;
                try {
                    await transcribeRockyRecording(blob);
                } catch (error) {
                    status.textContent = error.message;
                }
            };
            rockyRecorder.start();
            button.textContent = '■';
            button.setAttribute('aria-label', 'Stop recording question');
            status.textContent = 'Recording. Press stop when you are done speaking.';
        } catch (error) {
            status.textContent = 'Microphone access failed. Allow microphone permission and try again.';
        }
    });
    document.querySelectorAll('.ask-rocky-report').forEach(button => button.addEventListener('click', () => {
        selectedReportRow = button.closest('.report-row');
        panel.style.display = 'flex';
        launcher.setAttribute('aria-expanded', 'true');
        questionInput.focus();
    }));
})();