export function createClientId(prefix?: string): string {
  const raw =
    typeof globalThis.crypto?.randomUUID === 'function'
      ? globalThis.crypto.randomUUID()
      : `${Date.now()}_${Math.random().toString(16).slice(2)}`;
  return prefix ? `${prefix}${raw}` : raw;
}

