import React from 'react';

const Logo: React.FC = () => {
  return (
    <div className="flex items-center py-2 overflow-visible">
      {/* Logo Image */}
      <div className="flex-shrink-0" style={{ minWidth: '80px', height: '80px', display: 'flex', alignItems: 'center', justifyContent: 'flex-start', overflow: 'visible' }}>
        <img
          src="/folder/logo.png"
          alt="Harvard Undergraduate Consulting Group"
          className="h-full w-auto object-contain"
          style={{ maxHeight: '80px', maxWidth: '300px', objectFit: 'contain', display: 'block' }}
          onError={() => {
            // Fallback if image doesn't load
            console.warn('Logo image not found at /folder/logo.png');
          }}
        />
      </div>
    </div>
  );
};

export default Logo;

