"use client";
import { useEffect, useRef } from "react";
import type L from "leaflet";

interface MapPickerProps {
  lat: number;
  lon: number;
  onLocationChange: (lat: number, lon: number) => void;
}

export default function MapPicker({ lat, lon, onLocationChange }: MapPickerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const markerRef = useRef<L.Marker | null>(null);
  const onLocationChangeRef = useRef(onLocationChange);
  const locationRef = useRef({ lat, lon });

  useEffect(() => {
    onLocationChangeRef.current = onLocationChange;
  }, [onLocationChange]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || mapRef.current) return;

    let cancelled = false;

    const loadMap = async () => {
      const L = (await import("leaflet")).default;
      await import("leaflet/dist/leaflet.css");

      if (cancelled || !container.isConnected || mapRef.current) return;

      const currentLocation = locationRef.current;
      const initialLat = currentLocation.lat || 6.9271;
      const initialLon = currentLocation.lon || 80.7789;
      const map = L.map(container).setView([initialLat, initialLon], 12);
      mapRef.current = map;

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "© OpenStreetMap contributors",
        maxZoom: 19,
      }).addTo(map);

      const customIcon = L.icon({
        iconUrl: "/marker.png",
        iconSize: [40, 50],
        iconAnchor: [20, 50],
        popupAnchor: [0, -50],
      });

      const updateMarker = (newLat: number, newLon: number) => {
        if (markerRef.current) {
          markerRef.current.setLatLng([newLat, newLon]);
        } else {
          markerRef.current = L.marker([newLat, newLon], { draggable: true, icon: customIcon }).addTo(map);
          markerRef.current.on("dragend", () => {
            const pos = markerRef.current!.getLatLng();
            onLocationChangeRef.current(pos.lat, pos.lng);
          });
        }
      };

      updateMarker(initialLat, initialLon);

      map.on("click", (e: L.LeafletMouseEvent) => {
        updateMarker(e.latlng.lat, e.latlng.lng);
        onLocationChangeRef.current(e.latlng.lat, e.latlng.lng);
      });
    };

    void loadMap();

    return () => {
      cancelled = true;
      markerRef.current = null;
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    locationRef.current = { lat, lon };

    if (!markerRef.current || !mapRef.current) return;

    const nextLat = lat || 6.9271;
    const nextLon = lon || 80.7789;
    markerRef.current.setLatLng([nextLat, nextLon]);
    mapRef.current.panTo([nextLat, nextLon]);
  }, [lat, lon]);

  return (
    <div
      ref={containerRef}
      className="h-64 w-full rounded-md border border-input"
      style={{ background: "#e5e7eb" }}
    />
  );
}
