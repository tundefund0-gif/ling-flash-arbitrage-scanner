import React from 'react';
import { IconRefresh } from './icons';

export default function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="state">
      <div className="em">⚠️</div>
      <div>{message}</div>
      {onRetry && (
        <button className="btn btn-primary empty-cta" onClick={onRetry}>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}><IconRefresh size={15} /> Retry</span>
        </button>
      )}
    </div>
  );
}
