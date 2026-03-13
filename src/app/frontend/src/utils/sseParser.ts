/**
 * SSE (Server-Sent Events) stream parser.
 *
 * Eliminates the duplicated TextDecoder + buffer + line-split logic
 * that was copy-pasted in `streamChat` and `streamRegenerateImage`.
 */
import type { AgentResponse } from '../types';

/**
 * Parse an SSE stream from a `ReadableStreamDefaultReader` into an
 * `AsyncGenerator` of `AgentResponse` objects.
 *
 * Protocol assumed:
 * - Events delimited by `\n\n`
 * - Each event starts with `data: `
 * - `data: [DONE]` terminates the stream
 *
 * @param reader  The reader obtained via `response.body.getReader()`
 */
export async function* parseSSEStream(
  reader: ReadableStreamDefaultReader<Uint8Array>,
): AsyncGenerator<AgentResponse> {
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        if (data === '[DONE]') {
          return;
        }
        try {
          yield JSON.parse(data) as AgentResponse;
        } catch {
          // Malformed SSE frame — skip silently
        }
      }
    }
  }
}
