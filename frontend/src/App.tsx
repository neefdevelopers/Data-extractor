import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { BusinessDashboard } from './pages/BusinessDashboard';
import { AnalyticDashboard } from './pages/AnalyticDashboard';
import { Customers } from './pages/Customers';
import { Products } from './pages/Products';
import { GeographicAnalytics } from './pages/GeographicAnalytics';
import { RfmAnalytics } from './pages/RfmAnalytics';
import { Uploads } from './pages/Uploads';
import { Reports } from './pages/Reports';
import { Settings } from './pages/Settings';
import { DataDrilldown } from './pages/DataDrilldown';
import { UnknownLocations } from './pages/UnknownLocations';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<BusinessDashboard />} />
          <Route path="analytic-dashboard" element={<AnalyticDashboard />} />
          <Route path="customers" element={<Customers />} />
          <Route path="products" element={<Products />} />
          <Route path="geography" element={<GeographicAnalytics />} />
          <Route path="rfm" element={<RfmAnalytics />} />
          <Route path="drilldown" element={<DataDrilldown />} />
          <Route path="unknown-locations" element={<UnknownLocations />} />
          <Route path="uploads" element={<Uploads />} />
          <Route path="reports" element={<Reports />} />
          <Route path="settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
