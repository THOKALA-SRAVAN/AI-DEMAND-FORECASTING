import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { getSkus, getStores, runWhatIf } from "../api/client";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from "recharts";

function DeltaBadge({ delta }) {
  const positive = delta >= 0;
  return (
    <span className={`text-xs font-medium ml-2 ${positive ? "text-green-400" : "text-red-400"}`}>
      {positive ? "+" : ""}{delta.toFixed(1)}
    </span>
  );
}

export default function WhatIfPage() {
  const { data: skus }   = useQuery({ queryKey: ["skus"],   queryFn: getSkus });
  const { data: stores } = useQuery({ queryKey: ["stores"], queryFn: getStores });

  const [sku,           setSku]           = useState("");
  const [store,         setStore]         = useState("");
  const [shock,         setShock]         = useState(0);
  const [serviceLevel,  setServiceLevel]  = useState(95);
  const [orderingCost,  setOrderingCost]  = useState(50);
  const [holdingRate,   setHoldingRate]   = useState(25);

  const { mutate, data: result, isPending } = useMutation({
    mutationFn: () => runWhatIf({
      sku_id: sku, store,
      demand_shock_pct: shock,
      service_level: serviceLevel / 100,
      ordering_cost: orderingCost,
      holding_cost_rate: holdingRate / 100,
    }),
  });

  const chartData = result ? [
    { name: "EOQ",          Original: result.original_eoq,           Simulated: result.eoq },
    { name: "Safety Stock", Original: result.original_safety_stock,  Simulated: result.safety_stock },
    { name: "Reorder Pt",   Original: result.original_reorder_point, Simulated: result.reorder_point },
  ] : [];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">What-If Simulator</h1>
      <p className="text-sm text-gray-400">
        Adjust demand and cost parameters to see how inventory policy responds in real time.
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-5 space-y-5">
          <h2 className="text-sm font-semibold text-gray-300">Parameters</h2>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-gray-400 block mb-1">SKU</label>
              <select className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm"
                      value={sku} onChange={e => setSku(e.target.value)}>
                <option value="">Select SKU</option>
                {(skus ?? []).map(s => <option key={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Store</label>
              <select className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm"
                      value={store} onChange={e => setStore(e.target.value)}>
                <option value="">Select Store</option>
                {(stores ?? []).map(s => <option key={s}>{s}</option>)}
              </select>
            </div>
          </div>

          <div>
            <label className="text-xs text-gray-400 block mb-1">
              Demand Shock: <span className="text-white font-medium">{shock > 0 ? "+" : ""}{shock}%</span>
            </label>
            <input type="range" min={-50} max={100} step={5} value={shock}
                   onChange={e => setShock(Number(e.target.value))}
                   className="w-full accent-green-500" />
          </div>

          <div>
            <label className="text-xs text-gray-400 block mb-1">
              Service Level: <span className="text-white font-medium">{serviceLevel}%</span>
            </label>
            <input type="range" min={80} max={99} step={1} value={serviceLevel}
                   onChange={e => setServiceLevel(Number(e.target.value))}
                   className="w-full accent-green-500" />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-gray-400 block mb-1">Ordering Cost ($)</label>
              <input type="number" value={orderingCost} min={1}
                     onChange={e => setOrderingCost(Number(e.target.value))}
                     className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Holding Rate (%/yr)</label>
              <input type="number" value={holdingRate} min={1} max={60}
                     onChange={e => setHoldingRate(Number(e.target.value))}
                     className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm" />
            </div>
          </div>

          <button
            onClick={() => mutate()}
            disabled={!sku || !store || isPending}
            className="w-full bg-green-600 hover:bg-green-500 disabled:opacity-40 disabled:cursor-not-allowed
                       text-white font-medium py-2 rounded-lg text-sm transition-colors"
          >
            {isPending ? "Simulating…" : "Run Simulation"}
          </button>
        </div>

        <div className="space-y-4">
          {result ? (
            <>
              <div className="grid grid-cols-2 gap-4">
                {[
                  { label: "EOQ",           val: result.eoq,            orig: result.original_eoq },
                  { label: "Safety Stock",  val: result.safety_stock,   orig: result.original_safety_stock },
                  { label: "Reorder Point", val: result.reorder_point,  orig: result.original_reorder_point },
                  { label: "Stockout Risk", val: `${(result.stockout_probability * 100).toFixed(1)}%`,
                    orig: null,
                    deltaVal: (result.stockout_probability - result.original_stockout_probability) * 100 },
                ].map(({ label, val, orig, deltaVal }) => (
                  <div key={label} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                    <p className="text-xs text-gray-400">{label}</p>
                    <p className="text-xl font-bold mt-1">
                      {typeof val === "number" ? Math.round(val) : val}
                      {orig != null && <DeltaBadge delta={val - orig} />}
                      {deltaVal != null && <DeltaBadge delta={deltaVal} />}
                    </p>
                    {orig != null && (
                      <p className="text-xs text-gray-600 mt-1">was {Math.round(orig)}</p>
                    )}
                  </div>
                ))}
              </div>

              <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
                <h2 className="text-sm font-semibold mb-4 text-gray-300">Original vs. Simulated</h2>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                    <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#9ca3af" }} />
                    <YAxis tick={{ fontSize: 10, fill: "#9ca3af" }} />
                    <Tooltip contentStyle={{ background: "#111827", border: "1px solid #374151" }} />
                    <Legend />
                    <Bar dataKey="Original"  fill="#3b82f6" radius={4} />
                    <Bar dataKey="Simulated" fill="#22c55e" radius={4} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </>
          ) : (
            <div className="bg-gray-900 rounded-xl border border-gray-800 p-12 text-center text-gray-500 h-full flex items-center justify-center">
              Configure parameters and run the simulation to see results.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
