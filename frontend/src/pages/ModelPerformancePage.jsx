import { useQuery } from "@tanstack/react-query";
import { getMetrics, getMapeBySkus } from "../api/client";
import {
  BarChart, Bar, ScatterChart, Scatter, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import StatCard from "../components/StatCard";

export default function ModelPerformancePage() {
  const { data: metrics }    = useQuery({ queryKey: ["metrics"],    queryFn: getMetrics });
  const { data: mapeBySkus } = useQuery({ queryKey: ["mapeBySkus"], queryFn: getMapeBySkus });

  const avgMape  = metrics ? (metrics.reduce((s,m) => s + m.mape,  0) / metrics.length).toFixed(2) : "—";
  const avgSmape = metrics ? (metrics.reduce((s,m) => s + m.smape, 0) / metrics.length).toFixed(2) : "—";
  const avgRmse  = metrics ? (metrics.reduce((s,m) => s + m.rmse,  0) / metrics.length).toFixed(1) : "—";
  const avgImprove = metrics
    ? (metrics.filter(m => m.improvement_vs_baseline != null)
              .reduce((s,m) => s + (m.improvement_vs_baseline ?? 0), 0) /
       metrics.filter(m => m.improvement_vs_baseline != null).length).toFixed(2)
    : "—";

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Model Performance</h1>
      <p className="text-sm text-gray-400">
        Walk-forward cross-validated metrics for the XGBoost ensemble across all SKU-Store models.
      </p>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Avg MAPE"               value={`${avgMape}%`}     color="green" />
        <StatCard label="Avg SMAPE"              value={`${avgSmape}%`}    color="green" />
        <StatCard label="Avg RMSE"               value={avgRmse}           color="blue" />
        <StatCard label="Avg vs Baseline"        value={`+${avgImprove}%`} color="yellow"
                  sub="SMAPE improvement" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
          <h2 className="text-sm font-semibold mb-4 text-gray-300">Avg MAPE by SKU</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={mapeBySkus ?? []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="sku_id" tick={{ fontSize: 9, fill: "#9ca3af" }} />
              <YAxis tick={{ fontSize: 10, fill: "#9ca3af" }} tickFormatter={v => `${v}%`} />
              <Tooltip contentStyle={{ background: "#111827", border: "1px solid #374151" }}
                       formatter={v => [`${v}%`, "Avg MAPE"]} />
              <Bar dataKey="avg_mape" radius={4}>
                {(mapeBySkus ?? []).map((_, i) => (
                  <Cell key={i} fill={`hsl(${140 + i * 20}, 70%, 50%)`} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
          <h2 className="text-sm font-semibold mb-4 text-gray-300">MAPE vs RMSE (all models)</h2>
          <ResponsiveContainer width="100%" height={220}>
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="mape" name="MAPE" tick={{ fontSize: 10, fill: "#9ca3af" }}
                     tickFormatter={v => `${v}%`} />
              <YAxis dataKey="rmse" name="RMSE" tick={{ fontSize: 10, fill: "#9ca3af" }} />
              <Tooltip contentStyle={{ background: "#111827", border: "1px solid #374151" }} />
              <Scatter data={metrics ?? []} fill="#22c55e" fillOpacity={0.7} />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
        <h2 className="text-sm font-semibold mb-3 text-gray-300">All Model Metrics</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-gray-400 text-left border-b border-gray-800">
                {["SKU","Store","MAPE","SMAPE","RMSE","Bias","CV SMAPE","Baseline SMAPE","Improvement"].map(h => (
                  <th key={h} className="px-3 py-2 font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(metrics ?? []).sort((a, b) => a.mape - b.mape).map((m, i) => (
                <tr key={i} className="border-b border-gray-800/40 hover:bg-gray-800/30">
                  <td className="px-3 py-2 font-mono">{m.sku_id}</td>
                  <td className="px-3 py-2 text-gray-400">{m.store}</td>
                  <td className="px-3 py-2 text-green-400">{m.mape}%</td>
                  <td className="px-3 py-2">{m.smape}%</td>
                  <td className="px-3 py-2">{m.rmse}</td>
                  <td className="px-3 py-2">{m.bias}</td>
                  <td className="px-3 py-2">{m.cv_smape ?? "—"}</td>
                  <td className="px-3 py-2">{m.baseline_smape ?? "—"}</td>
                  <td className="px-3 py-2 text-yellow-400">
                    {m.improvement_vs_baseline != null ? `+${m.improvement_vs_baseline}%` : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
