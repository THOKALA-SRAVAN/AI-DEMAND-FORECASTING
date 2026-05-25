import axios from "axios";

const api = axios.create({ baseURL: "/api" });

export const getSummary       = ()              => api.get("/metrics/summary").then(r => r.data);
export const getWeeklyTrend   = ()              => api.get("/forecasts/weekly-trend").then(r => r.data);
export const getSkus          = ()              => api.get("/forecasts/skus").then(r => r.data);
export const getStores        = ()              => api.get("/forecasts/stores").then(r => r.data);
export const getForecasts     = (sku, store)    => api.get("/forecasts/", { params: { sku_id: sku, store } }).then(r => r.data);
export const getHistory       = (sku, store)    => api.get("/forecasts/history", { params: { sku_id: sku, store } }).then(r => r.data);
export const getInventory     = (filters = {})  => api.get("/inventory/", { params: filters }).then(r => r.data);
export const getAlerts        = ()              => api.get("/inventory/alerts").then(r => r.data);
export const getSegments      = ()              => api.get("/inventory/segments").then(r => r.data);
export const getCategoryRev   = ()              => api.get("/inventory/category-revenue").then(r => r.data);
export const getMetrics       = ()              => api.get("/metrics/").then(r => r.data);
export const getMapeBySkus    = ()              => api.get("/metrics/mape-by-sku").then(r => r.data);
export const runWhatIf        = (payload)       => api.post("/inventory/whatif", payload).then(r => r.data);
