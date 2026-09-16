import React from 'react';
import { UploadCloud } from 'lucide-react';
import { Button } from '../common/Button';
import { useNavigate } from 'react-router-dom';

interface HeaderProps {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}

export const Header: React.FC<HeaderProps> = ({ title, action }) => {
  const navigate = useNavigate();

  return (
    <header className="h-16 border-b border-slate-200/80 bg-white/90 backdrop-blur-md px-8 flex items-center justify-between sticky top-0 z-20 shadow-xs">
      <div>
        <h1 className="text-lg font-bold text-slate-900 tracking-tight">{title}</h1>
      </div>

      <div className="flex items-center gap-3">
        {action}
        <Button
          size="sm"
          variant="secondary"
          icon={<UploadCloud className="w-3.5 h-3.5" />}
          onClick={() => navigate('/uploads')}
        >
          Import Excel / CSV
        </Button>
      </div>
    </header>
  );
};
