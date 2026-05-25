import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getInventory } from "../api/client";

const riskColor = (p) => {
  if (p > 0.6) return "text-red-400";
  if (p > 0.3) return "text-yellow-400";
  return "text-green-400";
};

const badgeClass = (cls) => {
  const map = { A: "bg-green-500/20 text-green-400", B: "bg-blue-500/20 text-blue-400",
                C: "bg-gray-700 text-gray-400", X: "bg-teal-500/20 text-teal-400",
                Y: "bg-yellow-500/20 text-yellow-400", Z: "bg-red-500/20 text-red-400" };
  return map[cls] || "bg-gray-700 text-gray-400";
};

export default function InventoryPage() {
  const [store, setStore] = useState("");
  const [abc,   setAbc]   = useState("");

  const { data: inventory, isLoading } = useQuery({
    queryKey: ["inventory", store, abc],
    queryFn:  () => getInventory({ store: store || undefined, abc_class: abc || undefined }),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Inventory Policy</h1>
      <p className="text-sm text-gray-400">
        EOQ, safety stock, reorder points, and stockout risk per SKU-Store.
      </p>

      <div className="flex gap-3 flex-wrap">
        <select className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm"
                value={store} onChange={e => setStore(e.target.value)}>
          <option value="">All Stores</option>
          {["Store_A", "Store_B", "Store_C"].map(s => <option key={s}>{s}</option>)}
        </select>
        <select className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm"
                value={abc} onChange={e => setAbc(e.target.value)}>
          <option value="">All ABC Classes</option>
          <option>A</option><option>B</option><option>C</option>
        </select>
      </div>

      {isLoading && <p className="text-gray-400">Loading...</p>}

      {inventory && (
        <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-400 text-left border-b border-gray-800 text-xs">
                {["SKU","Name","Store","EOQ","Safety Stock","Reorder Point",
                  "Curr. Inventory","Stockout Risk","4W Forecast","Segment"].map(h => (
                  <th key={h} className="px-3 py-3 font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {inventory.map((r, i) => (
                <tr key={i} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                  <td className="px-3 py-2 font-mono text-xs">{r.sku_id}</td>
                  <td className="px-3 py-2">{r.sku_name}</td>
                  <td className="px-3 py-2 text-gray-400">{r.store}</td>
                  <td className="px-3 py-2">{Math.round(r.eoq)}</td>
                  <td className="px-3 py-2">{Math.round(r.safety_stock)}</td>
                  <td className="px-3 py-2">{Math.round(r.reorder_point)}</td>
                  <td className="px-3 py-2">{Math.round(r.current_inventory)}</td>
                  <td className={`px-3 py-2 font-medium ${riskColor(r.stockout_probability)}`}>
                    {(r.stockout_probability * 100).toFixed(1)}%
                  </td>
                  <td className="px-3 py-2">{r.forecast_4w_demand}</td>
                  <td className="px-3 py-2">
                    {r.segment && (
                      <span className="flex gap-1">
                        <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${badgeClass(r.abc_class)}`}>
                          {r.abc_class}
                        </span>
                        <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${badgeClass(r.xyz_class)}`}>
                          {r.xyz_class}
                        </span>
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
