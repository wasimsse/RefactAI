'use client';

import Image from 'next/image';
import React, { useState } from 'react';

type BrandLogoProps = {
  size?: number; // square px size
  className?: string;
  title?: string;
};

const BRAND_NAME = process.env.NEXT_PUBLIC_BRAND_NAME || 'RENDRI-R';
// SVG placeholder avoids 404s when no logo is present
const PLACEHOLDER_DATA_URI =
  'data:image/svg+xml;utf8,' +
  encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128"><rect width="100%" height="100%" rx="16" fill="%233c4453"/><text x="50%" y="54%" dominant-baseline="middle" text-anchor="middle" font-family="sans-serif" font-size="56" fill="%23ffffff">${(process.env.NEXT_PUBLIC_BRAND_NAME || 'R').slice(0,1)}</text></svg>`
  );
const BRAND_LOGO_SRC = process.env.NEXT_PUBLIC_BRAND_LOGO || PLACEHOLDER_DATA_URI;

export default function BrandLogo({ size = 48, className, title }: BrandLogoProps) {
  const alt = title || BRAND_NAME;
  const [src, setSrc] = useState<string>(BRAND_LOGO_SRC);
  const [failed, setFailed] = useState<boolean>(false);
  // Try to upgrade to /logo.png only if it actually exists, to avoid 404 noise
  React.useEffect(() => {
    const candidate = '/logo.png';
    if (BRAND_LOGO_SRC === PLACEHOLDER_DATA_URI) {
      const probe = new window.Image();
      probe.onload = () => setSrc(candidate);
      probe.onerror = () => void 0;
      probe.src = candidate;
    }
  }, []);
  return (
    <div className={className} style={{ lineHeight: 0 }}>
      {!failed ? (
        <Image
          src={src}
          alt={alt}
          width={size}
          height={size}
          priority
          unoptimized
          onError={() => {
            if (src !== '/logo.png') {
              setSrc('/logo.png');
            } else {
              setFailed(true);
            }
          }}
          className="rounded-lg object-contain"
        />
      ) : (
        <div
          aria-label={alt}
          className="rounded-lg bg-slate-700 text-white flex items-center justify-center"
          style={{ width: size, height: size }}
        >
          {BRAND_NAME.slice(0, 1)}
        </div>
      )}
    </div>
  );
}

export const BrandName = BRAND_NAME;

