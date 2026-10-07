'use client';

// Comet-style client-side action dispatcher.
// Komponenty registrujú handlery, AI ich volá cez client_actions.

type ActionHandler = (args: Record<string, unknown>) => void | Promise<void>;

type Registry = Record<string, ActionHandler>;

const registry: Registry = {};

type AIEvent = {
  type: 'action';
  name: string;
  args: Record<string, unknown>;
  status: 'ok' | 'error' | 'no_handler';
  error?: string;
};

type Listener = (e: AIEvent) => void;
const listeners = new Set<Listener>();

export const cmepAI = {
  register(name: string, handler: ActionHandler): () => void {
    registry[name] = handler;
    return () => {
      if (registry[name] === handler) delete registry[name];
    };
  },

  async dispatch(name: string, args: Record<string, unknown>): Promise<AIEvent> {
    const handler = registry[name];
    if (!handler) {
      const ev: AIEvent = { type: 'action', name, args, status: 'no_handler' };
      listeners.forEach((l) => l(ev));
      return ev;
    }
    try {
      await handler(args);
      const ev: AIEvent = { type: 'action', name, args, status: 'ok' };
      listeners.forEach((l) => l(ev));
      return ev;
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'unknown';
      const ev: AIEvent = { type: 'action', name, args, status: 'error', error: msg };
      listeners.forEach((l) => l(ev));
      return ev;
    }
  },

  subscribe(listener: Listener): () => void {
    listeners.add(listener);
    return () => { listeners.delete(listener); };
  },
};

// Global window hook — aby sa dali registrovať handlery odkiaľkoľvek
if (typeof window !== 'undefined') {
  (window as unknown as { cmepAI: typeof cmepAI }).cmepAI = cmepAI;
}
