import { useState } from "react";
import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import {
  LayoutDashboard, TrendingUp, Package, AlertTriangle,
  PieChart, BarChart3, FlaskConical, Menu, X,
} from "lucide-react";

import ErrorBoundary from "./components/ErrorBoundary";
import Overview from "./pages/Overview";
import ForecastPage from "./pages/ForecastPage";
import InventoryPage from "./pages/InventoryPage";
import AlertsPage from "./pages/AlertsPage";
import SegmentationPage from "./pages/SegmentationPage";
import ModelPerformancePage from "./pages/ModelPerformancePage";
import WhatIfPage from "./pages/WhatIfPage";

const NAV = [
  { to: "/",            label: "Overview",        icon: LayoutDashboard },
  { to: "/forecast",    label: "Demand Forecast",  icon: TrendingUp },
  { to: "/inventory",   label: "Inventory Policy", icon: Package },
  { to: "/alerts",      label: "Reorder Alerts",   icon: AlertTriangle },
  { to: "/segments",    label: "ABC-XYZ",           icon: PieChart },
  { to: "/performance", label: "Model Performance", icon: BarChart3 },
  { to: "/whatif",      label: "What-If Simulator", icon: FlaskConical },
];

function Sidebar({ open, onClose }) {
  return (
    <aside
      className={`fixed inset-y-0 left-0 z-40 w-60 bg-gray-900 border-r border-gray-800 flex flex-col
        transform transition-transform duration-200
        ${open ? "translate-x-0" : "-translate-x-full"} md:translate-x-0`}
    >
      <div className="p-5 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <Package className="text-green-400" size={22} />
          <span className="font-bold text-sm leading-tight">
            AI Demand<br />Forecasting
          </span>
        </div>
      </div>
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {NAV.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            onClick={onClose}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors
              ${isActive
                ? "bg-green-500/20 text-green-400 font-medium"
                : "text-gray-400 hover:bg-gray-800 hover:text-gray-100"}`
            }
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="p-4 text-xs text-gray-600 border-t border-gray-800">
        XGBoost · FastAPI · PostgreSQL · React
      </div>
    </aside>
  );
}

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <BrowserRouter>
      <div className="flex h-screen overflow-hidden">
        <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

        {sidebarOpen && (
          <div
            className="fixed inset-0 z-30 bg-black/50 md:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        <div className="flex-1 flex flex-col md:ml-60 overflow-hidden">
          <header className="md:hidden flex items-center gap-3 px-4 py-3 bg-gray-900 border-b border-gray-800">
            <button onClick={() => setSidebarOpen(true)}>
              <Menu size={20} />
            </button>
            <span className="font-semibold text-sm">AI Inventory Dashboard</span>
          </header>

          <main className="flex-1 overflow-y-auto p-4 md:p-6">
            <ErrorBoundary>
              <Routes>
                <Route path="/"            element={<Overview />} />
                <Route path="/forecast"    element={<ForecastPage />} />
                <Route path="/inventory"   element={<InventoryPage />} />
                <Route path="/alerts"      element={<AlertsPage />} />
                <Route path="/segments"    element={<SegmentationPage />} />
                <Route path="/performance" element={<ModelPerformancePage />} />
                <Route path="/whatif"      element={<WhatIfPage />} />
              </Routes>
            </ErrorBoundary>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
}
