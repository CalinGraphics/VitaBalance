import React, { useEffect, useState } from 'react';

interface AvatarProps {
  name: string;
  url?: string | null;
  /** Latura în pixeli. */
  size?: number;
  alt?: string;
  className?: string;
}

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return '?';
  const first = parts[0][0] ?? '';
  const last = parts.length > 1 ? parts[parts.length - 1][0] ?? '' : '';
  return (first + last).toUpperCase();
}

/** Poza de profil, cu inițialele ca rezervă (fără poză sau dacă linkul semnat a expirat). */
const Avatar: React.FC<AvatarProps> = ({ name, url, size = 36, alt, className = '' }) => {
  const [failed, setFailed] = useState(false);
  useEffect(() => setFailed(false), [url]);

  const style = { width: size, height: size };
  const base = `inline-flex flex-shrink-0 items-center justify-center overflow-hidden rounded-full border border-line-strong ${className}`;

  if (url && !failed) {
    return (
      <img
        src={url}
        alt={alt ?? name}
        style={style}
        className={`${base} object-cover`}
        onError={() => setFailed(true)}
      />
    );
  }
  return (
    <span
      role="img"
      aria-label={alt ?? name}
      style={{ ...style, fontSize: Math.max(11, Math.round(size * 0.38)) }}
      className={`${base} bg-accent-soft font-semibold text-accent`}
    >
      {initials(name)}
    </span>
  );
};

export default Avatar;
