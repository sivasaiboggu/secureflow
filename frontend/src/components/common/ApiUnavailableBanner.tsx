import React from 'react';
import { apiUnavailableReason } from '../../services/api';

// Shown on every page when this build has no API to talk to. Better an
// honest notice than pages that silently look empty.
export const ApiUnavailableBanner: React.FC = () => {
  if (!apiUnavailableReason) return null;
  return (
    <div
      role="status"
      style={{
        background: 'rgba(251,146,60,0.12)',
        borderBottom: '0.8px solid rgba(251,146,60,0.35)',
        color: '#fb923c',
        fontFamily: '"Geist", sans-serif',
        fontSize: 13,
        padding: '10px 24px',
        textAlign: 'center',
      }}
    >
      {apiUnavailableReason}
    </div>
  );
};
