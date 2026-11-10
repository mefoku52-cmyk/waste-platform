import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi, type Mock } from 'vitest';

import { http } from '@/lib/api/http';
import { KEEPALIVE_MESSAGE } from '@/lib/ai-agent/voice-stt';

import { VoiceLiveButton } from '../src/features/agent-platform/components/voice-live-button';

vi.mock('@/lib/api/http', () => ({
  http: { post: vi.fn() },
}));

const post = http.post as unknown as Mock;

class FakeSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;
  static instances: FakeSocket[] = [];

  readyState = FakeSocket.CONNECTING;
  binaryType = 'blob';
  sent: unknown[] = [];
  onopen: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;

  constructor(
    readonly url: string,
    readonly protocols?: string | string[],
  ) {
    FakeSocket.instances.push(this);
    queueMicrotask(() => {
      this.readyState = FakeSocket.OPEN;
      this.onopen?.(new Event('open'));
    });
  }

  send(data: unknown) {
    this.sent.push(data);
  }

  close() {
    this.readyState = FakeSocket.CLOSED;
  }

  emit(payload: unknown) {
    this.onmessage?.({ data: JSON.stringify(payload) } as MessageEvent);
  }

  static last(): FakeSocket {
    return FakeSocket.instances[FakeSocket.instances.length - 1];
  }
}

const results = (transcript: string, { isFinal = false, speechFinal = false } = {}) => ({
  type: 'Results',
  is_final: isFinal,
  speech_final: speechFinal,
  channel: { alternatives: [{ transcript }] },
});

function installBrowserFakes() {
  const track = { stop: vi.fn() };

  Object.defineProperty(navigator, 'mediaDevices', {
    configurable: true,
    value: { getUserMedia: vi.fn(async () => ({ getTracks: () => [track] })) },
  });

  class FakeAudioContext {
    state = 'running';
    sampleRate = 16000;
    destination = {};
    createMediaStreamSource() {
      return { connect: vi.fn(), disconnect: vi.fn() };
    }
    createGain() {
      return { gain: { value: 0 }, connect: vi.fn(), disconnect: vi.fn() };
    }
    createScriptProcessor() {
      return { onaudioprocess: null, connect: vi.fn(), disconnect: vi.fn() };
    }
    async resume() {}
    async close() {}
  }

  Object.defineProperty(window, 'AudioContext', { configurable: true, value: FakeAudioContext });
  Object.defineProperty(globalThis, 'WebSocket', { configurable: true, value: FakeSocket });

  return { track };
}

async function goLive() {
  render(
    <VoiceLiveButton
      onInterim={vi.fn()}
      onFinalTranscript={vi.fn()}
      onError={vi.fn()}
    />,
  );
  fireEvent.click(screen.getByRole('button'));
  await waitFor(() => expect(screen.getByRole('button').textContent).toContain('Live'));
  await waitFor(() => expect(FakeSocket.instances.length).toBeGreaterThan(0));
  return { socket: FakeSocket.last() };
}

describe('VoiceLiveButton', () => {
  beforeEach(() => {
    FakeSocket.instances = [];
    post.mockReset();
    post.mockResolvedValue({ access_token: 'tok_test', expires_in: 60 });
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
  });

  it('odmietnutý mikrofón zobrazí slovenskú chybu a nezostane v stave live', async () => {
    installBrowserFakes();
    const onError = vi.fn();
    Object.defineProperty(navigator, 'mediaDevices', {
      configurable: true,
      value: {
        getUserMedia: vi.fn(async () => {
          throw new DOMException('denied', 'NotAllowedError');
        }),
      },
    });

    render(<VoiceLiveButton onError={onError} />);
    fireEvent.click(screen.getByRole('button'));

    await waitFor(() => expect(onError).toHaveBeenCalledTimes(1));
    expect(onError.mock.calls[0][0]).toContain('zamietnutý');
    expect(screen.getByRole('button').textContent).toContain('🎧');
    expect(FakeSocket.instances).toHaveLength(0);
  });

  it('finálnu vetu pošle do chatu práve raz (UtteranceEnd ju nezduplikuje)', async () => {
    installBrowserFakes();
    const onFinalTranscript = vi.fn(async () => {});
    render(
      <VoiceLiveButton onInterim={vi.fn()} onFinalTranscript={onFinalTranscript} onError={vi.fn()} />,
    );
    fireEvent.click(screen.getByRole('button'));
    await waitFor(() => expect(FakeSocket.instances).toHaveLength(1));

    const { socket } = { socket: FakeSocket.last() };
    act(() => socket.emit(results('ahoj CMEP', { isFinal: true, speechFinal: true })));
    await waitFor(() => expect(onFinalTranscript).toHaveBeenCalledWith('ahoj CMEP'));

    act(() => socket.emit({ type: 'UtteranceEnd' }));
    act(() => socket.emit(results('ahoj CMEP', { isFinal: true, speechFinal: true })));

    expect(onFinalTranscript).toHaveBeenCalledTimes(1);
    // Token sa berie z nášho backendu (nie z prehliadača) a ide ako subprotocol.
    expect(post).toHaveBeenCalledWith('/agent-platform/voice/token', {});
    expect(socket.protocols).toEqual(['token', 'tok_test']);
  });

  it('pošle KeepAlive, keď je ticho dlhšie ako timeout Deepgramu', async () => {
    vi.useFakeTimers();
    installBrowserFakes();
    render(<VoiceLiveButton onInterim={vi.fn()} onFinalTranscript={vi.fn()} onError={vi.fn()} />);

    fireEvent.click(screen.getByRole('button'));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(100);
    });
    const socket = FakeSocket.last();
    expect(socket.sent).toHaveLength(0);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(6000);
    });

    expect(socket.sent).toContain(KEEPALIVE_MESSAGE);
  });

  it('pri odmountovaní zastaví mikrofónne tracky', async () => {
    const { track } = installBrowserFakes();
    const view = render(<VoiceLiveButton onInterim={vi.fn()} onFinalTranscript={vi.fn()} />);
    fireEvent.click(screen.getByRole('button'));
    await waitFor(() => expect(FakeSocket.instances).toHaveLength(1));

    view.unmount();
    expect(track.stop).toHaveBeenCalled();
  });
});
