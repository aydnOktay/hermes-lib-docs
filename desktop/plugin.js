/**
 * Lib Docs — current library docs from public npm / PyPI (no API keys).
 *
 * Unified package: copied to $HERMES_HOME/desktop-plugins/lib-docs/.
 */

import { host, useQuery, useMutation, queryClient } from '@hermes/plugin-sdk'
import { jsx, jsxs } from 'react/jsx-runtime'
import { useState } from 'react'

function insertText(text) {
  const trimmed = (text || '').trim()
  if (!trimmed) return
  try {
    window.dispatchEvent(
      new CustomEvent('hermes:composer-insert', {
        detail: { mode: 'block', target: 'main', text: trimmed },
      }),
    )
  } catch {
    /* older hosts */
  }
  if (host.os && typeof host.os.writeClipboard === 'function') {
    void host.os.writeClipboard(trimmed)
  }
  host.notify({
    kind: 'info',
    message: 'Docs summary inserted into the chat box. Paste (Ctrl+V) if it did not appear.',
  })
}

function useRecent(ctx) {
  return useQuery({
    queryKey: ['lib-docs', 'recent'],
    queryFn: () => ctx.rest('/recent'),
    refetchInterval: 6000,
  })
}

function DocsPane({ ctx }) {
  const query = useRecent(ctx)
  const [input, setInput] = useState('')
  const [ecosystem, setEcosystem] = useState('auto')
  const [lastDoc, setLastDoc] = useState(null)
  const clearMut = useMutation({
    mutationFn: () => ctx.rest('/clear', { method: 'POST', body: {} }),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['lib-docs'] })
    },
  })
  const getMut = useMutation({
    mutationFn: (body) => ctx.rest('/get', { method: 'POST', body }),
    onSettled: (data) => {
      queryClient.invalidateQueries({ queryKey: ['lib-docs'] })
      if (data) setLastDoc(data)
      if (data && data.ok === false) {
        host.notify({ kind: 'info', message: data.error || 'Lookup failed.' })
      }
    },
  })

  const items = (query.data && query.data.items) || []
  const busy = getMut.isPending

  const runGet = (pkg, eco) => {
    const name = (pkg || '').trim()
    if (!name) return
    getMut.mutate({ package: name, ecosystem: eco || ecosystem })
  }

  return jsxs('div', {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 10,
      padding: 12,
      height: '100%',
      overflow: 'auto',
      fontSize: 13,
      color: 'var(--ui-text-secondary)',
    },
    children: [
      jsxs('div', {
        style: { display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' },
        children: [
          jsx('div', { style: { fontWeight: 600 }, children: 'Lib Docs' }),
          jsx('div', {
            style: { fontSize: 11, color: 'var(--ui-text-tertiary)' },
            children: items.length ? `${items.length}` : '',
          }),
        ],
      }),
      jsx('div', {
        style: { fontSize: 12, color: 'var(--ui-text-tertiary)', lineHeight: 1.45 },
        children: 'Current package docs from npm / PyPI. No API key. Prefer this over guessing APIs.',
      }),
      jsxs('div', {
        style: { display: 'flex', flexDirection: 'column', gap: 6 },
        children: [
          jsxs('select', {
            value: ecosystem,
            onChange: (event) => setEcosystem(event.target.value),
            style: {
              fontSize: 12,
              padding: '4px 6px',
              color: 'var(--ui-text-secondary)',
              background: 'transparent',
              border: '1px solid var(--ui-stroke-secondary)',
              borderRadius: 6,
            },
            children: [
              jsx('option', { value: 'auto', children: 'auto' }),
              jsx('option', { value: 'npm', children: 'npm' }),
              jsx('option', { value: 'pypi', children: 'pypi' }),
            ],
          }),
          jsx('input', {
            value: input,
            placeholder: 'react, fastapi, lodash…',
            onChange: (event) => setInput(event.target.value),
            onKeyDown: (event) => {
              if (event.key === 'Enter') runGet(input, ecosystem)
            },
            style: {
              fontSize: 12,
              padding: '6px 8px',
              color: 'var(--ui-text-secondary)',
              background: 'transparent',
              border: '1px solid var(--ui-stroke-secondary)',
              borderRadius: 6,
            },
          }),
          jsx('button', {
            type: 'button',
            disabled: busy || !input.trim(),
            onClick: () => runGet(input, ecosystem),
            style: {
              alignSelf: 'flex-start',
              fontSize: 12,
              padding: '6px 10px',
              color: 'var(--ui-text-secondary)',
              background: 'transparent',
              border: '1px solid var(--ui-stroke-secondary)',
              borderRadius: 6,
              cursor: busy ? 'wait' : 'pointer',
            },
            children: busy ? 'Fetching…' : 'Fetch docs',
          }),
        ],
      }),
      lastDoc && lastDoc.ok
        ? jsxs('div', {
            style: {
              display: 'flex',
              flexDirection: 'column',
              gap: 4,
              padding: '8px 0',
              borderTop: '1px solid var(--ui-stroke-secondary)',
            },
            children: [
              jsx('div', {
                style: { fontWeight: 600 },
                children: `${lastDoc.package} @ ${lastDoc.version || '?'}`,
              }),
              jsx('div', {
                style: { fontSize: 11, color: 'var(--ui-text-tertiary)' },
                children: lastDoc.ecosystem,
              }),
              lastDoc.description
                ? jsx('div', {
                    style: { fontSize: 12, lineHeight: 1.4 },
                    children: lastDoc.description,
                  })
                : null,
              jsx('button', {
                type: 'button',
                onClick: () =>
                  insertText(
                    [
                      `${lastDoc.package} ${lastDoc.version || ''} (${lastDoc.ecosystem})`,
                      lastDoc.description || '',
                      lastDoc.homepage || '',
                      (lastDoc.readme || '').slice(0, 2500),
                    ]
                      .filter(Boolean)
                      .join('\n\n'),
                  ),
                style: {
                  alignSelf: 'flex-start',
                  fontSize: 11,
                  padding: '4px 8px',
                  color: 'var(--ui-text-tertiary)',
                  background: 'transparent',
                  border: '1px solid var(--ui-stroke-secondary)',
                  borderRadius: 4,
                  cursor: 'pointer',
                },
                children: 'Insert into chat',
              }),
            ],
          })
        : null,
      jsx('div', {
        style: { fontSize: 11, color: 'var(--ui-text-tertiary)', marginTop: 4 },
        children: items.length ? 'Recent' : 'No lookups yet.',
      }),
      jsx('div', {
        style: { display: 'flex', flexDirection: 'column', gap: 6 },
        children: items
          .slice()
          .reverse()
          .map((it) =>
            jsxs(
              'button',
              {
                type: 'button',
                onClick: () => runGet(it.package, it.ecosystem || 'auto'),
                style: {
                  textAlign: 'left',
                  fontSize: 12,
                  padding: '6px 0',
                  color: 'var(--ui-text-secondary)',
                  background: 'transparent',
                  border: 'none',
                  borderBottom: '1px solid var(--ui-stroke-secondary)',
                  cursor: 'pointer',
                },
                children: [
                  jsx('div', {
                    style: { fontWeight: 600 },
                    children: it.package,
                  }),
                  jsx('div', {
                    style: { fontSize: 11, color: 'var(--ui-text-tertiary)' },
                    children: `${it.ecosystem}@${it.version || '?'}`,
                  }),
                ],
              },
              `${it.ecosystem}:${it.package}`,
            ),
          ),
      }),
      items.length
        ? jsx('button', {
            type: 'button',
            disabled: clearMut.isPending,
            onClick: () => clearMut.mutate(),
            style: {
              alignSelf: 'flex-start',
              fontSize: 12,
              padding: '4px 8px',
              border: '1px solid var(--ui-stroke-secondary)',
              background: 'transparent',
              color: 'var(--ui-text-secondary)',
              borderRadius: 4,
              cursor: clearMut.isPending ? 'wait' : 'pointer',
            },
            children: clearMut.isPending ? 'Clearing…' : 'Clear recent',
          })
        : null,
      query.error
        ? jsx('div', {
            style: { fontSize: 12 },
            children: 'Backend unreachable. Enable lib-docs and restart the gateway.',
          })
        : null,
    ],
  })
}

function DocsChip({ ctx }) {
  const query = useRecent(ctx)
  const n = query.data && typeof query.data.count === 'number' ? query.data.count : 0
  return jsx('button', {
    type: 'button',
    title: 'Lib Docs',
    onClick: () => {
      host.notify({
        kind: 'info',
        message: n
          ? `Lib Docs has ${n} recent lookup${n === 1 ? '' : 's'}.`
          : 'Lib Docs is empty. Fetch a package in the pane.',
      })
    },
    style: {
      padding: '0 6px',
      fontSize: '0.6875rem',
      color: 'var(--ui-text-tertiary)',
      background: 'transparent',
      border: 'none',
      cursor: 'pointer',
    },
    children: n ? `docs ${n}` : 'docs',
  })
}

export default {
  id: 'lib-docs',
  name: 'Lib Docs',
  defaultEnabled: true,
  register(ctx) {
    ctx.register({
      id: 'pane',
      area: 'panes',
      title: 'lib docs',
      data: { placement: 'right', width: '280px' },
      render: () => jsx(DocsPane, { ctx }),
    })
    ctx.register({
      id: 'chip',
      area: 'statusBar.right',
      order: 128,
      render: () => jsx(DocsChip, { ctx }),
    })
  },
}
