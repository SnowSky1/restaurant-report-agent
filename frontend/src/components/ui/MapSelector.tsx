"use client";

import { useState } from "react";
import { APILoader, Map, Marker } from "@uiw/react-amap";
import { motion } from "framer-motion";
import { AlertTriangle, Loader2, LocateFixed, Search, X } from "lucide-react";
import { geocodeAddress, reverseGeocode } from "@/lib/api";

interface MapSelectorProps {
  onSelect: (location: { lng: number; lat: number; address: string }) => void;
  onClose: () => void;
  initialAddress?: string;
  apiKey?: string;
}

const DEFAULT_API_KEY = process.env.NEXT_PUBLIC_AMAP_MAPS_API_KEY || "";

export function MapSelector({ onSelect, onClose, initialAddress = "", apiKey = DEFAULT_API_KEY }: MapSelectorProps) {
  const [center, setCenter] = useState<[number, number]>([116.397428, 39.90923]);
  const [selectedPos, setSelectedPos] = useState<[number, number] | null>(null);
  const [address, setAddress] = useState(initialAddress);
  const [query, setQuery] = useState(initialAddress);
  const [manualCoordinates, setManualCoordinates] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const selectCoordinates = async (lng: number, lat: number) => {
    const coordinates = `${lng.toFixed(6)},${lat.toFixed(6)}`;
    setCenter([lng, lat]);
    setSelectedPos([lng, lat]);
    setManualCoordinates(coordinates);
    setMessage("正在查询坐标对应地址…");
    try {
      const result = await reverseGeocode(coordinates);
      setAddress(result.location.formatted_address || coordinates);
      setMessage(result.provenance.used_mock_data ? "地址由模拟回退补全，提交后请核对数据说明" : "已通过高德服务获取地址");
    } catch {
      setAddress(coordinates);
      setMessage("逆地理编码不可用，仍可直接使用该坐标分析");
    }
  };

  const handleMapClick = (event: AMap.MapsEvent) => {
    const lng = Number(event.lnglat.getLng?.() ?? event.lnglat.lng);
    const lat = Number(event.lnglat.getLat?.() ?? event.lnglat.lat);
    void selectCoordinates(lng, lat);
  };

  const handleSearch = async () => {
    if (!query.trim()) return;
    setIsSearching(true);
    setMessage(null);
    try {
      const result = await geocodeAddress(query.trim());
      const [lng, lat] = result.location.location.split(",").map(Number);
      if (!Number.isFinite(lng) || !Number.isFinite(lat)) throw new Error("地址服务没有返回有效坐标");
      setCenter([lng, lat]);
      setSelectedPos([lng, lat]);
      setManualCoordinates(`${lng.toFixed(6)},${lat.toFixed(6)}`);
      setAddress(result.location.formatted_address || query.trim());
      setMessage(result.provenance.used_mock_data ? "地址未能实时解析，当前坐标为模拟回退" : `已定位${result.location.matched_poi ? `：${result.location.matched_poi}` : ""}`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "地址定位失败");
    } finally {
      setIsSearching(false);
    }
  };

  const handleManualCoordinates = () => {
    const [lng, lat] = manualCoordinates.split(",").map((part) => Number(part.trim()));
    if (!Number.isFinite(lng) || !Number.isFinite(lat) || Math.abs(lng) > 180 || Math.abs(lat) > 90) {
      setMessage("请输入有效的“经度,纬度”，例如 116.475831,39.906540");
      return;
    }
    void selectCoordinates(lng, lat);
  };

  const handleConfirm = () => {
    if (!selectedPos) return;
    onSelect({ lng: selectedPos[0], lat: selectedPos[1], address: address || manualCoordinates });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-3 sm:p-6">
      <motion.button aria-label="关闭地图" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <motion.div initial={{ opacity: 0, scale: 0.96, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.96, y: 20 }} transition={{ type: "spring", stiffness: 300, damping: 25 }} className="relative flex h-[86vh] w-full max-w-4xl flex-col overflow-hidden rounded-3xl bg-white shadow-2xl dark:bg-[#1c1c1e]">
        <div className="flex items-center justify-between border-b border-[var(--glass-border)] p-4">
          <div>
            <h3 className="text-lg font-semibold">选择店铺位置</h3>
            <p className="text-sm text-system-gray">支持地址定位、地图点击和直接输入坐标</p>
          </div>
          <button aria-label="关闭" onClick={onClose} className="rounded-full p-2 transition-colors hover:bg-system-gray-6"><X className="h-5 w-5" /></button>
        </div>

        <div className="space-y-3 border-b border-[var(--glass-border)] p-4">
          <div className="flex gap-2">
            <input aria-label="地图地址搜索" value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => event.key === "Enter" && void handleSearch()} className="min-w-0 flex-1 rounded-xl border border-[var(--glass-border)] bg-white/60 px-4 py-2.5 outline-none focus:ring-2 focus:ring-system-blue/40 dark:bg-black/30" placeholder="输入完整地址或地标" />
            <button onClick={() => void handleSearch()} disabled={isSearching} className="flex items-center gap-2 rounded-xl bg-system-blue px-4 py-2.5 font-medium text-white disabled:opacity-50">
              {isSearching ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}定位
            </button>
          </div>
          <div className="flex gap-2">
            <input aria-label="手动坐标" value={manualCoordinates} onChange={(event) => setManualCoordinates(event.target.value)} className="min-w-0 flex-1 rounded-xl border border-[var(--glass-border)] bg-white/60 px-4 py-2 text-sm outline-none focus:ring-2 focus:ring-system-blue/40 dark:bg-black/30" placeholder="经度,纬度，例如 116.475831,39.906540" />
            <button onClick={handleManualCoordinates} className="flex items-center gap-2 rounded-xl border border-[var(--glass-border)] px-4 py-2 text-sm font-medium hover:bg-system-gray-6"><LocateFixed className="h-4 w-4" />使用坐标</button>
          </div>
          {message && <p className="text-xs text-system-gray">{message}</p>}
        </div>

        <div className="relative min-h-0 flex-1 bg-system-gray-6">
          {apiKey ? (
            <APILoader akey={apiKey} version="2.0" plugins={["AMap.Scale"]}>
              <Map zoom={14} center={center} onClick={handleMapClick} className="h-full w-full">
                {selectedPos && <Marker position={selectedPos} title={address} />}
              </Map>
            </APILoader>
          ) : (
            <div className="flex h-full flex-col items-center justify-center gap-4 p-8 text-center">
              <AlertTriangle className="h-12 w-12 text-system-orange" />
              <div><p className="text-lg font-medium">高德 JS 地图未配置</p><p className="mt-2 max-w-lg text-sm text-system-gray">仍可使用上方地址定位或直接输入坐标。地图显示需要 Web 端 JSAPI Key；后端真实 POI 查询使用独立的 Web 服务 Key。</p></div>
            </div>
          )}
        </div>

        <div className="flex flex-col items-center justify-between gap-4 border-t border-[var(--glass-border)] bg-background p-4 sm:flex-row">
          <div className="w-full min-w-0 flex-1 text-sm"><span className="mr-2 text-system-gray">已选位置：</span><span className="font-medium">{address || "请搜索、点击地图或输入坐标"}</span></div>
          <div className="flex w-full gap-3 sm:w-auto">
            <button onClick={onClose} className="flex-1 rounded-xl px-6 py-2.5 font-medium text-system-gray hover:bg-system-gray-6">取消</button>
            <button onClick={handleConfirm} disabled={!selectedPos} className="flex-1 rounded-xl bg-system-blue px-6 py-2.5 font-medium text-white disabled:cursor-not-allowed disabled:opacity-50 sm:flex-none">确认位置</button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
