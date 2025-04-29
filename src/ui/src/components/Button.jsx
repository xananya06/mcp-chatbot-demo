// Button.jsx
import React from 'react';
import './Button.css';

function Button({
  children,
  variant = 'default',
  size = 'medium',
  disabled = false,
  fullWidth = false,
  type = 'button',
  onClick
}) {
  return (
    <button
      type={type}
      className={`button ${variant} ${size} ${fullWidth ? 'full-width' : ''}`}
      disabled={disabled}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

export default Button;