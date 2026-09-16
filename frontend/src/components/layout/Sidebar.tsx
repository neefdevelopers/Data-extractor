import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  Package,
  MapPin,
  Flame,
  GitFork,
  UploadCloud,
  FileSpreadsheet,
  Settings,
} from 'lucide-react';

const NAV_ITEMS = [
  { name: 'Business Dashboard', path: '/', icon: LayoutDashboard },
  { name: 'Data Drill-down', path: '/drilldown', icon: GitFork },
  { name: 'Customers CRM', path: '/customers', icon: Users },
  { name: 'Product Analytics', path: '/products', icon: Package },
  { name: 'Geographic Drilldown', path: '/geography', icon: MapPin },
  { name: 'RFM Customer Segments', path: '/rfm', icon: Flame },
  { name: 'Import Wizard', path: '/uploads', icon: UploadCloud },
  { name: 'Reports & Exports', path: '/reports', icon: FileSpreadsheet },
  { name: 'System Settings', path: '/settings', icon: Settings },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col shrink-0 h-screen sticky top-0 shadow-sm z-30">
      {/* Brand logo */}
      <div className="h-16 flex items-center px-6 border-b border-slate-100 gap-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
          <MapPin className="w-5 h-5 fill-white/20 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-1.5">
            <span className="font-extrabold text-base tracking-tight text-slate-900">Pinlytics</span>
            <span className="text-[10px] uppercase font-bold bg-indigo-50 text-indigo-700 border border-indigo-200 px-1.5 py-0.2 rounded">
              Local
            </span>
          </div>
          <p className="text-[11px] text-slate-500 font-medium">Customer & Business Intelligence</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                  isActive
                    ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-500/20 font-bold'
                    : 'text-slate-600 hover:text-indigo-600 hover:bg-slate-50'
                }`
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{item.name}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Local status footer */}
      <div className="p-4 border-t border-slate-100 bg-slate-50/70">
        <div className="flex items-center gap-2 text-xs text-slate-600">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="font-semibold text-slate-700">Local Engine Active</span>
        </div>
        <p className="text-[11px] text-slate-500 mt-1">Zero cloud dependencies • 100% private</p>
      </div>
    </aside>
  );
};
