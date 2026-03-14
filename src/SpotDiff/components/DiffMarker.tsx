import React from 'react';

interface DiffMarkerProps {
  cx: number;
  cy: number;
  r: number;
  type: 'found' | 'hint';
}

const DiffMarker: React.FC<DiffMarkerProps> = ({ cx, cy, r, type }) => {
  // r is normalized (0-1), but we display circle relative to container
  // Use percentage positioning
  const size = `${r * 200}%`; // diameter in percentage
  const style: React.CSSProperties = {
    left: `${cx * 100}%`,
    top: `${cy * 100}%`,
    width: size,
    height: size,
  };

  return (
    <div
      className={`sd__marker sd__marker--${type}`}
      style={style}
    />
  );
};

export default React.memo(DiffMarker);
