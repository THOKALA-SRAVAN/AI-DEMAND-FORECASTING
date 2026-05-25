import { useQuery } from "@tanstack/react-query";
import { getSummary, getWeeklyTrend, getCategoryRev } from "../api/client";
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import StatCard from "../components/StatCard";

const COLORS = ["#22c55e", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"];

export default function Overview() {
  const { data: summary } = useQuery({ queryKey: ["summary"], queryFn: getSummary });
  const { data: trend }   = useQuery({ queryKey: ["trend"],   queryFn: getWeeklyTrend });
  const { data: catRev }  = useQuery({ queryKey: ["catrev"],  queryFn: getCategoryRev });

  const trendSampled = trend?.filter((_, i) => i % 7 === 0) ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard Overview</h1>
        <p className="text-gray-400 text-sm mt-1">
          Real-time inventory intelligence powered by XGBoost demand forecasting.
        </p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="SKUs Tracked"       value={summary?.total_skus ?? "—"}       color="blue" />
        <StatCard label="Stores"             value={summary?.total_stores ?? "—"}      color="blue" />
        <StatCard label="Reorder Alerts"     value={summary?.reorder_alerts ?? "—"}    color="red"
                  sub="Need immediate action" />
        <StatCard label="Avg Forecast MAPE"  value={summary ? `${summary.avg_mape}%` : "—"}
                  color="green" sub="Lower is better" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
          <h2 className="text-sm font-semibold mb-4 text-gray-300">Weekly Sales Trend (All SKUs)</h2>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={trendSampled}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#9ca3af" }}
                     tickFormatter={d => d?.slice(5)} />
              <YAxis tick={{ fontSize: 10, fill: "#9ca3af" }} />
              <Tooltip contentStyle={{ background: "#111827", border: "1px solid #374151" }} />
              <Line dataKey="demand" stroke="#22c55e" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
          <h2 className="text-sm font-semibold mb-4 text-gray-300">Annual Revenue by Category</h2>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={catRev ?? []} dataKey="annual_revenue" nameKey="category"
                   cx="50%" cy="50%" outerRadius={80} label={({ category }) => category}>
                {(catRev ?? []).map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: "#111827", border: "1px solid #374151" }}
                       formatter={v => [`$${(v / 1000).toFixed(0)}K`]} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
        <h2 className="text-sm font-semibold mb-2 text-gray-300">High-Risk Stockout Items</h2>
        <p className="text-xs text-gray-500">
          {summary?.high_risk_items ?? 0} SKU-Store combinations have &gt;30% stockout probability.
          Check the Reorder Alerts tab for details.
        </p>
      </div>
    </div>
  );
}
