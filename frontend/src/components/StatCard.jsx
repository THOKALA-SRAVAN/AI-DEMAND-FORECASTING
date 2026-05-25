export default function StatCard({ label, value, sub, color = "green" }) {
  const colors = {
    green:  "border-green-500/30 bg-green-500/5",
    yellow: "border-yellow-500/30 bg-yellow-500/5",
    red:    "border-red-500/30 bg-red-500/5",
    blue:   "border-blue-500/30 bg-blue-500/5",
  };
  return (
    <div className={`rounded-xl border p-4 ${colors[color]}`}>
      <p className="text-xs text-gray-400 mb-1">{label}</p>
      <p className="text-2xl font-bold text-white">{value}</p>
      {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
    </div>
  );
}
