import { useQuery } from "@tanstack/react-query";
import { getAlerts } from "../api/client";
import { AlertTriangle } from "lucide-react";

const riskLabel = (p) => {
  if (p > 0.6) return { label: "CRITICAL", cls: "bg-red-500/20 text-red-400 border-red-500/30" };
  if (p > 0.3) return { label: "HIGH",     cls: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30" };
  return              { label: "MEDIUM",   cls: "bg-blue-500/20 text-blue-400 border-blue-500/30" };
};

export default function AlertsPage() {
  const { data: alerts, isLoading } = useQuery({ queryKey: ["alerts"], queryFn: getAlerts });

  const critical = alerts?.filter(a => a.stockout_probability > 0.6).length ?? 0;
  const high     = alerts?.filter(a => a.stockout_probability > 0.3 && a.stockout_probability <= 0.6).length ?? 0;
  const medium   = alerts?.filter(a => a.stockout_probability <= 0.3).length ?? 0;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Reorder Alerts</h1>
      <p className="text-sm text-gray-400">
        SKU-Store combinations where current inventory is at or below the reorder point.
      </p>

      <div className="grid grid-cols-3 gap-4">
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-center">
          <p className="text-3xl font-bold text-red-400">{critical}</p>
          <p className="text-xs text-gray-400 mt-1">Critical (&gt;60%)</p>
        </div>
        <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4 text-center">
          <p className="text-3xl font-bold text-yellow-400">{high}</p>
          <p className="text-xs text-gray-400 mt-1">High (30-60%)</p>
        </div>
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4 text-center">
          <p className="text-3xl font-bold text-blue-400">{medium}</p>
          <p className="text-xs text-gray-400 mt-1">Medium (&lt;30%)</p>
        </div>
      </div>

      {isLoading && <p className="text-gray-400">Loading alerts...</p>}

      {alerts?.map((a, i) => {
        const risk = riskLabel(a.stockout_probability);
        return (
          <div key={i}
               className={`rounded-xl border p-4 flex items-start gap-4 ${risk.cls}`}>
            <AlertTriangle size={18} className="mt-0.5 shrink-0" />
            <div className="flex-1">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-semibold">{a.sku_name}</span>
                <span className="text-xs opacity-70">{a.sku_id}</span>
                <span className="text-xs opacity-70">·</span>
                <span className="text-xs opacity-70">{a.store}</span>
                <span className={`ml-auto text-xs px-2 py-0.5 rounded font-bold border ${risk.cls}`}>
                  {risk.label}
                </span>
              </div>
              <div className="mt-2 grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                <div>
                  <span className="text-gray-400">Stockout Risk</span>
                  <p className="font-semibold">{(a.stockout_probability * 100).toFixed(1)}%</p>
                </div>
                <div>
                  <span className="text-gray-400">Current Stock</span>
                  <p className="font-semibold">{Math.round(a.current_inventory)} units</p>
                </div>
                <div>
                  <span className="text-gray-400">Reorder Point</span>
                  <p className="font-semibold">{Math.round(a.reorder_point)} units</p>
                </div>
                <div>
                  <span className="text-gray-400">Order Qty (EOQ)</span>
                  <p className="font-semibold">{Math.round(a.eoq)} units</p>
                </div>
              </div>
            </div>
          </div>
        );
      })}

      {!isLoading && alerts?.length === 0 && (
        <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-8 text-center text-green-400">
          All inventory levels are healthy. No reorder alerts.
        </div>
      )}
    </div>
  );
}
