import React from 'react';

/** Indicator de încărcare care moștenește culoarea textului (`currentColor`). */
const Spinner: React.FC<{ className?: string }> = ({ className = 'h-4 w-4' }) => (
  <span
    aria-hidden="true"
    className={`inline-block animate-spin rounded-full border-2 border-current border-t-transparent ${className}`}
  />
);

export default Spinner;
