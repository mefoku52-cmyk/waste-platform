'use client';

import { useEffect } from 'react';
import type { FieldValues, Path, UseFormSetValue } from 'react-hook-form';
import { cmepAI } from './dispatcher';

// Shared AI form-filling wiring for react-hook-form forms.
//
// Registers the `fill_form_field` and `highlight_field` client actions for the
// CURRENT form. A handler THROWS when it cannot do what was asked (unknown
// field, field not on screen). The dispatcher turns a throw into status
// 'error', so the widget only ever shows "✓" when the value really landed —
// this is the fix for the old silent `catch {}` that faked success.

const SAFE_FIELD_RE = /^[A-Za-z0-9_]{1,40}$/;

function flash(field: string, color: string): boolean {
  const el = document.querySelector(`[name="${field}"]`) as HTMLElement | null;
  if (!el) return false;
  el.style.transition = 'box-shadow 0.3s';
  el.style.boxShadow = `0 0 0 3px ${color}`;
  window.setTimeout(() => {
    el.style.boxShadow = '';
  }, 1200);
  return true;
}

type Options<T extends FieldValues> = {
  setValue: UseFormSetValue<T>;
  /** The exact set of fields this form renders (stable module-level array). */
  fields: readonly string[];
};

export function useAiFormFilling<T extends FieldValues>({ setValue, fields }: Options<T>) {
  useEffect(() => {
    const known = new Set(fields);

    const unregFill = cmepAI.register('fill_form_field', (args) => {
      const field = typeof args.field === 'string' ? args.field : '';
      if (!SAFE_FIELD_RE.test(field) || !known.has(field)) {
        throw new Error(`unknown_field:${field || '?'}`);
      }
      setValue(field as Path<T>, args.value as never, {
        shouldValidate: true,
        shouldDirty: true,
      });
      flash(field, 'rgba(95,209,122,0.8)');
    });

    const unregHighlight = cmepAI.register('highlight_field', (args) => {
      const field = typeof args.field === 'string' ? args.field : '';
      if (!SAFE_FIELD_RE.test(field) || !known.has(field)) {
        throw new Error(`unknown_field:${field || '?'}`);
      }
      const el = document.querySelector(`[name="${field}"]`) as HTMLElement | null;
      if (!el) throw new Error(`field_not_rendered:${field}`);
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      flash(field, 'rgba(201,168,76,0.9)');
    });

    return () => {
      unregFill();
      unregHighlight();
    };
  }, [setValue, fields]);
}
