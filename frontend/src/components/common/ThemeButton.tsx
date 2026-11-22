import { Moon, Sun } from 'lucide-react';
import { useTheme } from '../../theme/ThemeContext';

export function ThemeButton() {
  const { mode, toggleMode } = useTheme();
  const label = mode === 'dark' ? 'Switch to light mode' : 'Switch to dark mode';
  return <button type="button" className="button icon-button" onClick={toggleMode} aria-label={label} title={label}>
    {mode === 'dark' ? <Sun size={18} aria-hidden="true" /> : <Moon size={18} aria-hidden="true" />}
  </button>;
}
