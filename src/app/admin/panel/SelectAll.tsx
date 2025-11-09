'use client';

import { useEffect, useId, useState } from 'react';

export default function SelectAll({ formId }: { formId: string }) {
  const [checked, setChecked] = useState(false);
  const id = useId();

  useEffect(() => {
    const form = document.getElementById(formId) as HTMLFormElement | null;
    if (!form) return;
    const boxes = Array.from(
      form.querySelectorAll<HTMLInputElement>('input[name="ids"]')
    );
    for (const b of boxes) b.checked = checked;
  }, [checked, formId]);

  return (
    <label className="inline-flex items-center gap-2 cursor-pointer" htmlFor={id}>
      <input
        id={id}
        type="checkbox"
        className="h-4 w-4"
        checked={checked}
        onChange={(e) => setChecked(e.target.checked)}
      />
      <span className="text-xs text-gray-600">Επιλογή όλων</span>
    </label>
  );
}
