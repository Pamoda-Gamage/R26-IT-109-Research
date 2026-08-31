"use client";

import { useState } from "react";
import { Camera, ImagePlus } from "lucide-react";

import { MATCH_API_BASE } from "@/lib/match-api";

interface ImageUploadProps {
  onUploadComplete: (url: string) => void;
  currentImage?: string | null;
}

export default function ImageUpload({ onUploadComplete, currentImage }: ImageUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [preview, setPreview] = useState(currentImage || "");
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
      setError("Only JPEG, PNG, and WebP images allowed"); return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setError("File size must be under 5MB"); return;
    }

    setError(null); setUploading(true);
    try {
      const reader = new FileReader();
      reader.onload = async (event) => {
        const base64Data = event.target?.result as string;
        setPreview(base64Data);
        try {
          const res = await fetch(`${MATCH_API_BASE}/providers/upload/image`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ data: base64Data, filename: file.name }),
          });
          if (!res.ok) {
            const data = await res.json().catch(() => ({ detail: "Upload failed" }));
            setError(data.detail || "Upload failed"); setPreview(""); return;
          }
          const data = await res.json();
          onUploadComplete(data.url);
        } catch (err) {
          setError(err instanceof Error ? err.message : "Upload failed"); setPreview("");
        } finally { setUploading(false); }
      };
      reader.readAsDataURL(file);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed"); setPreview(""); setUploading(false);
    }
  };

  return (
    <div className="flex flex-col gap-3">
      <div className="rounded-xl border-2 border-dashed border-blue-200 bg-blue-50/30 p-4 transition-colors hover:border-blue-400 hover:bg-blue-50/60">
        {preview ? (
          <div className="flex items-center gap-4">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={preview} alt="Provider preview" className="h-24 w-24 rounded-xl border-2 border-white object-cover shadow-md" />
            <label className="inline-flex cursor-pointer items-center gap-2 rounded-lg border border-blue-200 bg-white px-4 py-2 text-sm font-semibold text-blue-700 shadow-sm hover:bg-blue-50">
              <Camera size={17} /> {uploading ? "Uploading..." : "Change photo"}
              <input type="file" accept="image/*" onChange={handleFileChange} disabled={uploading} className="hidden" />
            </label>
          </div>
        ) : (
          <label className="flex cursor-pointer flex-col items-center gap-2 py-5 text-center">
            <span className="flex h-11 w-11 items-center justify-center rounded-full bg-blue-100 text-blue-600"><ImagePlus size={22} /></span>
            <span className="text-sm font-semibold text-slate-700">Upload provider photo</span>
            <span className="text-xs text-slate-400">JPEG, PNG or WebP / Maximum 5MB</span>
            <input type="file" accept="image/*" onChange={handleFileChange} disabled={uploading} className="hidden" />
          </label>
        )}
      </div>
      {error && <p className="text-sm text-destructive">{error}</p>}
    </div>
  );
}
