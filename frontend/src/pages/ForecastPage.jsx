import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getSkus, getStores, getHistory, getForecasts, getMetrics } from "../api/client";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import StatCard from "../components/StatCard";

export default function ForecastPage() {
  const { data: skus   = [] } = useQuery({ queryKey: ["skus"],   queryFn: getSkus });
  const { data: stores = [] } = useQuery({ queryKey: ["stores"], queryFn: getStores });

  const [sku,   setSku]   = useState("");
  const [store, setStore] = useState("");

  const ready = Boolean(sku && store);

  const { data: history   = [] } = useQuery({
    queryKey: ["history", sku, store],
    queryFn:  () => getHistory(sku, store),
    enabled:  ready,
  });

  const { data: forecasts = [] } = useQuery({
    queryKey: ["forecasts", sku, store],
    queryFn:  () => getForecasts(sku, store),
    enabled:  ready,
  });

  const { data: allMetrics = [] } = useQuery({
    queryKey: ["metrics"],
    queryFn:  getMetrics,
  });

  const skuMetric = allMetrics.find(m => m.sku_id === sku && m.store === store);

  // Sample daily history to every 7th point to avoid chart overload
  const histSampled = history.filter((_, i) => i % 7 === 0);

  const chartData = [
    ...histSampled.map(r => ({ date: String(r.date).slice(5), actual: r.demand })),
    ...forecasts.map(r  => ({ date: String(r.date).slice(5), xgboost: r.forecast_demand, baseline: r.baseline_forecast })),
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Demand Forecasting</h1>

      <div className="flex gap-4 flex-wrap">
        <select
          className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm"
          value={sku}
          onChange={e => setSku(e.target.value)}
        >
          <option value="">Select SKU</option>
          {skus.map(s => <option key={s} value={s}>{s}</option>)}
        </select>

        <select
          className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm"
          value={store}
          onChange={e => setStore(e.target.value)}
        >
          <option value="">Select Store</option>
          {stores.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {skuMetric && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard label="MAPE"           value={`${skuMetric.mape}%`}   color="green" />
          <StatCard label="SMAPE"          value={`${skuMetric.smape}%`}  color="green" />
          <StatCard label="RMSE"           value={skuMetric.rmse}         color="blue" />
          <StatCard label="vs Baseline"
                    value={skuMetric.improvement_vs_baseline != null
                      ? `+${skuMetric.improvement_vs_baseline}%`
                      : "—"}
                    color="yellow"
                    sub="SMAPE improvement" />
        </div>
      )}

      {ready && chartData.length > 0 && (
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
          <h2 className="text-sm font-semibold mb-1 text-gray-300">
            {sku} — {store}: History + 8-Week Forecast
          </h2>
          <p className="text-xs text-gray-500 mb-4">
            Green dashed line = XGBoost forecast &nbsp;|&nbsp; Yellow = 4-week rolling baseline
          </p>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#9ca3af" }} interval={20} />
              <YAxis tick={{ fontSize: 10, fill: "#9ca3af" }} />
              <Tooltip contentStyle={{ background: "#111827", border: "1px solid #374151" }} />
              <Legend />
              <Line dataKey="actual"   stroke="#3b82f6" dot={false} strokeWidth={2} name="Actual"   connectNulls={false} />
              <Line dataKey="xgboost"  stroke="#22c55e" dot={false} strokeWidth={2} name="XGBoost"  strokeDasharray="6 3" connectNulls={false} />
              <Line dataKey="baseline" stroke="#f59e0b" dot={false} strokeWidth={1} name="Baseline" strokeDasharray="3 3" connectNulls={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {ready && forecasts.length > 0 && (
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
          <h2 className="text-sm font-semibold mb-3 text-gray-300">8-Week Forecast</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-400 text-left border-b border-gray-800 text-xs">
                  <th className="pb-2 pr-6">Week</th>
                  <th className="pb-2 pr-6">XGBoost Forecast</th>
                  <th className="pb-2">Baseline</th>
                </tr>
              </thead>
              <tbody>
                {forecasts.map((r, i) => (
                  <tr key={i} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                    <td className="py-2 pr-6 text-gray-400">{r.date}</td>
                    <td className="py-2 pr-6 text-green-400 font-medium">{r.forecast_demand}</td>
                    <td className="py-2 text-gray-400">{r.baseline_forecast}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {!ready && (
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-16 text-center text-gray-500">
          Select a SKU and Store above to view the demand forecast.
        </div>
      )}
    </div>
  );
}
