'use client';

import { useFormStatus } from 'react-dom';

export function BulkButton({
  name,
  value,
  label,
  formId,
}: {
  name: string;
  value: string;
  label: string;
  formId: string;
}) {
  const { pending } = useFormStatus();

  return (
    <button
      name={name}
      value={value}
      form={formId}
      className="border rounded-md px-3 py-1.5 text-xs hover:bg-gray-50 disabled:opacity-50"
      disabled={pending}
    >
      {pending ? 'Εκτέλεση…' : label}
    </button>
  );
}
