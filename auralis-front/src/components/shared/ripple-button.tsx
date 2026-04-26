import { useState, type ButtonHTMLAttributes, type ReactNode, type MouseEvent } from 'react';

interface RippleButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: 'primary' | 'secondary' | 'ghost';
}

interface Ripple {
  x: number;
  y: number;
  id: number;
}

export function RippleButton({ children, variant = 'primary', className = '', ...props }: RippleButtonProps) {
  const [ripples, setRipples] = useState<Ripple[]>([]);

  const addRipple = (event: MouseEvent<HTMLButtonElement>) => {
    const button = event.currentTarget;
    const rect = button.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const id = Date.now();

    setRipples(prev => [...prev, { x, y, id }]);

    setTimeout(() => {
      setRipples(prev => prev.filter(ripple => ripple.id !== id));
    }, 600);
  };

  const handleClick = (event: MouseEvent<HTMLButtonElement>) => {
    addRipple(event);
    if (props.onClick) {
      props.onClick(event);
    }
  };

  const variantStyles = {
    primary: 'bg-orange-500 hover:bg-orange-600 text-white',
    secondary: 'bg-blue-500 hover:bg-blue-600 text-white',
    ghost: 'bg-white/5 hover:bg-white/10 text-white border border-white/10'
  };

  return (
    <button
      {...props}
      onClick={handleClick}
      className={`relative overflow-hidden px-6 py-2.5 rounded-lg transition-all ${variantStyles[variant]} ${className}`}
    >
      {children}
      <span className="absolute inset-0 pointer-events-none">
        {ripples.map(ripple => (
          <span
            key={ripple.id}
            className="absolute rounded-full bg-white/40 animate-ripple"
            style={{
              left: ripple.x,
              top: ripple.y,
              width: 0,
              height: 0,
            }}
          />
        ))}
      </span>
    </button>
  );
}
