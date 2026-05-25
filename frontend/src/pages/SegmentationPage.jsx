import { useQuery } from "@tanstack/react-query";
import { getSegments, getInventory } from "../api/client";
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell, Legend,
} from "recharts";

const SEG_COLORS = {
  AX: "#22c55e", AY: "#16a34a", AZ: "#15803d",
  BX: "#3b82f6", BY: "#2563eb", BZ: "#1d4ed8",
  CX: "#9ca3af", CY: "#6b7280", CZ: "#4b5563",
};

const descriptions = {
  A: "High-value (top 70% revenue)",
  B: "Medium-value (next 20% revenue)",
  C: "Low-value (bottom 10% revenue)",
  X: "Stable demand (CoV < 0.5)",
  Y: "Variable demand (CoV 0.5–1.0)",
  Z: "Erratic demand (CoV > 1.0)",
};

export default function SegmentationPage() {
  const { data: segments }  = useQuery({ queryKey: ["segments"],  queryFn: getSegments });
  const { data: inventory } = useQuery({ queryKey: ["inventory"], queryFn: () => getInventory() });

  const scatterData = inventory?.map(r => ({
    x: r.annual_revenue,
    y: r.stockout_probability * 100,
    name: r.sku_name,
    segment: r.segment,
  })) ?? [];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">ABC-XYZ Inventory Segmentation</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
          <h2 className="text-sm font-semibold mb-1 text-gray-300">ABC Classification</h2>
          <p className="text-xs text-gray-500 mb-3">Based on annual revenue contribution</p>
          {["A","B","C"].map(c => (
            <div key={c} className="flex items-center gap-2 mb-2 text-sm">
              <span className="w-6 h-6 rounded bg-green-500/10 text-green-400 flex items-center
                               justify-center text-xs font-bold border border-green-500/30">{c}</span>
              <span className="text-gray-300">{descriptions[c]}</span>
            </div>
          ))}
        </div>
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
          <h2 className="text-sm font-semibold mb-1 text-gray-300">XYZ Classification</h2>
          <p className="text-xs text-gray-500 mb-3">Based on demand variability (Coefficient of Variation)</p>
          {["X","Y","Z"].map(c => (
            <div key={c} className="flex items-center gap-2 mb-2 text-sm">
              <span className="w-6 h-6 rounded bg-blue-500/10 text-blue-400 flex items-center
                               justify-center text-xs font-bold border border-blue-500/30">{c}</span>
              <span className="text-gray-300">{descriptions[c]}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
        <h2 className="text-sm font-semibold mb-4 text-gray-300">
          Revenue vs. Stockout Risk (colored by segment)
        </h2>
        <ResponsiveContainer width="100%" height={280}>
          <ScatterChart>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis dataKey="x" name="Annual Revenue" tick={{ fontSize: 10, fill: "#9ca3af" }}
                   tickFormatter={v => `$${(v/1000).toFixed(0)}K`} />
            <YAxis dataKey="y" name="Stockout Risk %" tick={{ fontSize: 10, fill: "#9ca3af" }}
                   tickFormatter={v => `${v.toFixed(0)}%`} />
            <Tooltip
              contentStyle={{ background: "#111827", border: "1px solid #374151" }}
              formatter={(val, name) => name === "Annual Revenue"
                ? [`$${(val/1000).toFixed(1)}K`, name]
                : [`${val.toFixed(1)}%`, name]}
              cursor={{ strokeDasharray: "3 3" }}
            />
            <Scatter data={scatterData} name="SKU-Store">
              {scatterData.map((d, i) => (
                <Cell key={i} fill={SEG_COLORS[d.segment] ?? "#6b7280"} fillOpacity={0.8} />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </div>

      <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
        <h2 className="text-sm font-semibold mb-3 text-gray-300">Segment Summary</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-400 text-left border-b border-gray-800 text-xs">
                <th className="pb-2 px-2">Segment</th>
                <th className="pb-2 px-2">Count</th>
                <th className="pb-2 px-2">Avg Annual Revenue</th>
                <th className="pb-2 px-2">Strategy</th>
              </tr>
            </thead>
            <tbody>
              {(segments ?? []).sort((a, b) => b.revenue - a.revenue).map((s, i) => (
                <tr key={i} className="border-b border-gray-800/50">
                  <td className="py-2 px-2">
                    <span className="font-bold" style={{ color: SEG_COLORS[s.segment] }}>
                      {s.segment}
                    </span>
                  </td>
                  <td className="py-2 px-2">{s.count}</td>
                  <td className="py-2 px-2">${(s.revenue / s.count / 1000).toFixed(1)}K</td>
                  <td className="py-2 px-2 text-xs text-gray-400">
                    {s.abc === "A" ? "Tight control, frequent orders" :
                     s.abc === "B" ? "Moderate control" : "Periodic review"}
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
