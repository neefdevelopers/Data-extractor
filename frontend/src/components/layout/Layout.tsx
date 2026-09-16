import React from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';

export const Layout: React.FC = () => {
  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-800">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-x-hidden">
        <main className="flex-1 pb-16">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
