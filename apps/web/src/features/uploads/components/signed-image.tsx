'use client';

import { useEffect, useState } from 'react';
import { extractFileId, getSignedUrl } from '../api';

type Props = {
  src: string | null | undefined;
  alt?: string;
  className?: string;
  style?: React.CSSProperties;
  ttlSeconds?: number;
};

const SIGNED_TTL_DEFAULT = 3600;

export function SignedImage({
  src,
  alt = '',
  className,
  style,
  ttlSeconds = SIGNED_TTL_DEFAULT,
}: Props) {
  const [signedSrc, setSignedSrc] = useState<string | null>(null);
  const [error, setError] = useState<boolean>(false);

  useEffect(() => {
    let cancelled = false;

    if (!src) {
      setSignedSrc(null);
      return;
    }

    const fileId = extractFileId(src);

    if (!fileId) {
      setSignedSrc(src);
      return;
    }

    (async () => {
      try {
        const res = await getSignedUrl(fileId, ttlSeconds);
        if (!cancelled) {
          setSignedSrc(res.urlPath);
        }
      } catch {
        if (!cancelled) {
          setError(true);
          setSignedSrc(null);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [src, ttlSeconds]);

  if (error) {
    return (
      <div
        className={className}
        style={{
          ...style,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'rgba(0,0,0,0.05)',
          color: '#888',
          fontSize: '0.75rem',
        }}
      >
        obrázok nedostupný
      </div>
    );
  }

  if (!signedSrc) {
    return (
      <div
        className={className}
        style={{ ...style, background: 'rgba(0,0,0,0.05)' }}
      />
    );
  }

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={signedSrc} alt={alt} className={className} style={style} />
  );
}
