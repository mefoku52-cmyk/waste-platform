import { test } from 'node:test';
import assert from 'node:assert/strict';

import {
  buildSttUrl,
  createUtteranceTracker,
  parseSttMessage,
} from '../src/lib/ai-agent/voice-stt.ts';

const results = (transcript, { isFinal = false, speechFinal = false } = {}) =>
  JSON.stringify({
    type: 'Results',
    is_final: isFinal,
    speech_final: speechFinal,
    channel: { alternatives: [{ transcript }] },
  });

test('buildSttUrl deklaruje presne ten formát, ktorý posielame (linear16 mono)', () => {
  const url = new URL(buildSttUrl(16000));
  assert.equal(url.origin + url.pathname, 'wss://api.deepgram.com/v1/listen');
  assert.equal(url.searchParams.get('model'), 'nova-3');
  assert.equal(url.searchParams.get('language'), 'sk');
  assert.equal(url.searchParams.get('encoding'), 'linear16');
  assert.equal(url.searchParams.get('channels'), '1');
  assert.equal(url.searchParams.get('interim_results'), 'true');
  assert.equal(url.searchParams.get('endpointing'), '800');
  assert.equal(url.searchParams.get('utterance_end_ms'), '1200');
  assert.equal(url.searchParams.get('sample_rate'), '16000');
});

test('buildSttUrl použije reálny sample rate AudioContextu (nie natvrdo 16000)', () => {
  assert.equal(new URL(buildSttUrl(48000)).searchParams.get('sample_rate'), '48000');
  // Neplatný vstup nesmie poslať NaN do Deepgramu.
  assert.equal(new URL(buildSttUrl(Number.NaN)).searchParams.get('sample_rate'), '16000');
  assert.equal(new URL(buildSttUrl(0)).searchParams.get('sample_rate'), '16000');
});

test('parseSttMessage rozlíši priebežný a finálny výsledok', () => {
  const interim = parseSttMessage(results('ahoj ako'));
  assert.deepEqual(interim, { kind: 'interim', text: 'ahoj ako' });

  const finalNoEnd = parseSttMessage(results('ahoj ako sa máš', { isFinal: true }));
  assert.deepEqual(finalNoEnd, { kind: 'final', text: 'ahoj ako sa máš', endsUtterance: false });

  const finalEnd = parseSttMessage(results('ahoj ako sa máš', { isFinal: true, speechFinal: true }));
  assert.deepEqual(finalEnd, { kind: 'final', text: 'ahoj ako sa máš', endsUtterance: true });
});

test('parseSttMessage mapuje UtteranceEnd, Error a ostatné správy', () => {
  assert.deepEqual(parseSttMessage(JSON.stringify({ type: 'UtteranceEnd' })), {
    kind: 'utterance_end',
  });
  assert.deepEqual(
    parseSttMessage(JSON.stringify({ type: 'Error', description: 'Invalid credentials' })),
    { kind: 'error', message: 'Invalid credentials' },
  );
  // Error bez description použije message, inak generický text — nikdy nesmie zmiznúť.
  assert.deepEqual(parseSttMessage(JSON.stringify({ type: 'Error', message: 'bad model' })), {
    kind: 'error',
    message: 'bad model',
  });
  assert.equal(parseSttMessage(JSON.stringify({ type: 'Error' })).kind, 'error');

  for (const ignored of [
    JSON.stringify({ type: 'Welcome' }),
    JSON.stringify({ type: 'Metadata' }),
    JSON.stringify({ type: 'SpeechStarted' }),
    'not-json',
    '',
  ]) {
    assert.deepEqual(parseSttMessage(ignored), { kind: 'ignore' });
  }
});

test('tracker skladá finálne fragmenty a vydá výpoveď raz na speech_final', () => {
  const tracker = createUtteranceTracker();
  assert.deepEqual(tracker.push(parseSttMessage(results('ahoj ako'))), { interim: 'ahoj ako' });
  // Deepgram posiela v každom is_final len NOVÉ slová segmentu (nie kumulatívne).
  assert.deepEqual(tracker.push(parseSttMessage(results('ahoj ako', { isFinal: true }))), {
    interim: 'ahoj ako',
  });
  assert.deepEqual(
    tracker.push(parseSttMessage(results('sa máš', { isFinal: true, speechFinal: true }))),
    { final: 'ahoj ako sa máš' },
  );
  // Po odoslaní je buffer prázdny — žiadne zdvojenie v chate.
  assert.deepEqual(tracker.push({ kind: 'utterance_end' }), { interim: '' });
  assert.equal(tracker.interimText(), '');
});

test('tracker vydá výpoveď aj keď príde len UtteranceEnd (bez speech_final)', () => {
  const tracker = createUtteranceTracker();
  tracker.push(parseSttMessage(results('treba drevo', { isFinal: true })));
  assert.deepEqual(tracker.push({ kind: 'utterance_end' }), { final: 'treba drevo' });
  assert.deepEqual(tracker.push({ kind: 'utterance_end' }), { interim: '' });
});

test('tracker neodošle prázdnu výpoveď ani prázdne fragmenty', () => {
  const tracker = createUtteranceTracker();
  assert.deepEqual(tracker.push({ kind: 'utterance_end' }), { interim: '' });
  tracker.push(parseSttMessage(results('   ', { isFinal: true, speechFinal: true })));
  assert.deepEqual(tracker.push({ kind: 'utterance_end' }), { interim: '' });
});

test('tracker dedupuje tú istú výpoveď v krátkom okne, ale dovolí ju zopakovať neskôr', () => {
  const tracker = createUtteranceTracker(3000);

  tracker.push(parseSttMessage(results('áno', { isFinal: true })));
  assert.deepEqual(tracker.push({ kind: 'utterance_end' }, 1000), { final: 'áno' });

  // Druhý flush tej istej výpovede (speech_final + UtteranceEnd) → nič.
  tracker.push(parseSttMessage(results('áno', { isFinal: true })));
  assert.deepEqual(tracker.push({ kind: 'utterance_end' }, 1500), { interim: '' });

  // Tá istá veta neskôr = nová výpoveď, musí prejsť.
  tracker.push(parseSttMessage(results('áno', { isFinal: true })));
  assert.deepEqual(tracker.push({ kind: 'utterance_end' }, 5000), { final: 'áno' });
});

test('tracker drží dve rôzne výpovede oddelene (druhá sa nespojí s prvou)', () => {
  const tracker = createUtteranceTracker();
  // speech_final odošle hneď a vyčistí buffer.
  assert.deepEqual(
    tracker.push(parseSttMessage(results('prvá vec', { isFinal: true, speechFinal: true }))),
    { final: 'prvá vec' },
  );
  assert.deepEqual(tracker.push({ kind: 'utterance_end' }, 1000), { interim: '' });

  assert.deepEqual(
    tracker.push(parseSttMessage(results('druhá vec', { isFinal: true, speechFinal: true }))),
    { final: 'druhá vec' },
  );
  assert.deepEqual(tracker.push({ kind: 'utterance_end' }, 1200), { interim: '' });
});
