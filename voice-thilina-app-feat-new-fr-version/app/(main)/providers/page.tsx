"use client";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowLeft, BriefcaseBusiness, Check, ChevronDown, MapPin, Pencil, Plus, ShieldCheck, Trash2, UsersRound } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import MapPicker from "@/components/MapPicker";
import ImageUpload from "@/components/ImageUpload";
import { MATCH_API_BASE } from "@/lib/match-api";

const API_BASE = MATCH_API_BASE;

const SERVICE_TYPES = ["plumbing", "carpentry", "electrical", "painting", "hvac", "roofing", "general"];
const REGIONS = ["colombo-01", "colombo-02", "dehiwala", "mount-lavinia", "kotte"];
const SERVICE_AREAS = ["colombo-01", "colombo-02", "dehiwala", "mount-lavinia", "kotte", "moratuwa", "ruwanella", "negombo"];

interface Provider {
  id: string;
  name: string;
  service_type: string;
  region: string;
  lat: number;
  lon: number;
  rating: number;
  years_experience: number;
  phone: string | null;
  avatar_url: string | null;
  service_areas: string | null;
}

interface ProviderForm {
  name: string;
  service_type: string;
  region: string;
  lat: number | "";
  lon: number | "";
  rating: number | "";
  years_experience: number | "";
  phone: string;
  avatar_url: string;
  service_areas: string;
}

interface AdminSelectProps {
  value: string;
  onValueChange: (value: string) => void;
  options: { value: string; label: string }[];
  placeholder?: string;
  icon: React.ReactNode;
  ariaLabel: string;
  disabled?: boolean;
}

function AdminSelect({ value, onValueChange, options, placeholder, icon, ariaLabel, disabled }: AdminSelectProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const selected = options.find((option) => option.value === value);

  useEffect(() => {
    if (!open) return;
    const close = (event: MouseEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) setOpen(false);
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", close);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("mousedown", close);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [open]);

  return (
    <div ref={containerRef} className="relative">
      <button type="button" disabled={disabled} className="admin-select-trigger" aria-label={ariaLabel} aria-haspopup="listbox" aria-expanded={open} onClick={() => setOpen((current) => !current)}>
        <span className="admin-select-icon">{icon}</span>
        <span>{selected?.label ?? placeholder}</span>
        <ChevronDown size={18} className={`ml-auto text-slate-400 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      {open && (
        <div className="admin-select-content absolute left-0 top-full mt-1.5" role="listbox" aria-label={ariaLabel}>
          <div className="admin-select-viewport">
            {options.map((option) => (
              <button
                type="button"
                role="option"
                aria-selected={option.value === value}
                key={option.value}
                className="admin-select-item w-full"
                onClick={() => { onValueChange(option.value); setOpen(false); }}
              >
                <span>{option.label}</span>
                {option.value === value && <Check className="ml-auto text-blue-600" size={17} strokeWidth={2.5} />}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function AdminProvidersPage() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [form, setForm] = useState<ProviderForm>({
    name: "",
    service_type: "plumbing",
    region: "colombo-01",
    lat: "",
    lon: "",
    rating: 4.5,
    years_experience: 1,
    phone: "",
    avatar_url: "",
    service_areas: "",
  });
  const [editingId, setEditingId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [listLoading, setListLoading] = useState(true);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  const loadProviders = useCallback(async () => {
    try {
      setListLoading(true);
      const res = await fetch(`${API_BASE}/providers/`, {
        headers: { "Content-Type": "application/json" },
      });
      if (res.ok) {
        setProviders(await res.json());
      }
    } catch (e) {
      console.error("Failed to load providers", e);
    } finally {
      setListLoading(false);
    }
  }, []);

  useEffect(() => {
    const role = localStorage.getItem("auth_role");
    if (role !== "admin") {
      window.location.href = "/auth/admin";
      return;
    }
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadProviders();
  }, [loadProviders]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: ["lat", "lon", "rating", "years_experience"].includes(name) ? parseFloat(value) || "" : value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    if (!form.name.trim()) {
      setError("Provider name is required");
      setLoading(false);
      return;
    }

    if (typeof form.lat !== "number" || typeof form.lon !== "number") {
      setError("Please select a location on the map");
      setLoading(false);
      return;
    }

    try {
      const method = editingId ? "PUT" : "POST";
      const url = editingId ? `${API_BASE}/providers/${editingId}` : `${API_BASE}/providers/`;

      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: form.name,
          service_type: form.service_type,
          region: form.region,
          lat: form.lat,
          lon: form.lon,
          rating: form.rating,
          years_experience: form.years_experience,
          phone: form.phone || null,
          avatar_url: form.avatar_url || null,
          service_areas: form.service_areas || null,
        }),
      });

      if (!res.ok) {
        setError(`Failed to ${editingId ? "update" : "create"} provider`);
        return;
      }

      const data = await res.json();
      setSuccess(`Provider "${data.name}" ${editingId ? "updated" : "created"} successfully`);
      setForm({
        name: "",
        service_type: "plumbing",
        region: "colombo-01",
        lat: "",
        lon: "",
        rating: 4.5,
        years_experience: 1,
        phone: "",
        avatar_url: "",
        service_areas: "",
      });
      setEditingId(null);
      loadProviders();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save provider");
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (provider: Provider) => {
    setForm({
      name: provider.name,
      service_type: provider.service_type,
      region: provider.region,
      lat: provider.lat,
      lon: provider.lon,
      rating: provider.rating,
      years_experience: provider.years_experience,
      phone: provider.phone || "",
      avatar_url: provider.avatar_url || "",
      service_areas: provider.service_areas || "",
    });
    setEditingId(provider.id);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleDelete = async (id: string) => {
    try {
      const res = await fetch(`${API_BASE}/providers/${id}`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
      });
      if (res.ok) {
        setSuccess("Provider deleted successfully");
        setDeleteConfirm(null);
        loadProviders();
      } else {
        setError("Failed to delete provider");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete provider");
    }
  };

  const handleCancel = () => {
    setEditingId(null);
    setForm({
      name: "",
      service_type: "plumbing",
      region: "colombo-01",
      lat: "",
      lon: "",
      rating: 4.5,
      years_experience: 1,
      phone: "",
      avatar_url: "",
      service_areas: "",
    });
  };

  return (
    <div className="admin-provider-page">
      <div className="site-container flex flex-col gap-7 py-8 sm:py-10">
      <div className="admin-provider-hero">
        <div className="relative z-10">
          <p className="mb-2 text-xs font-bold uppercase tracking-[0.2em] text-blue-600">Provider Management</p>
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">Create and Manage Service Providers</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600 sm:text-base">Create, update, and manage verified service provider profiles to connect with customers.</p>
        </div>
        <Button asChild variant="outline" className="relative z-10 shrink-0">
          <Link href="/"><ArrowLeft size={17} /> Back</Link>
        </Button>
        <UsersRound className="absolute -bottom-8 right-28 h-40 w-40 text-blue-100/70" strokeWidth={1.2} aria-hidden="true" />
      </div>

      <Card className="overflow-hidden border-0 shadow-xl shadow-blue-950/10">
        <CardHeader className="border-b border-slate-100 bg-slate-50/60 px-6 py-5 sm:px-8">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-100 text-blue-600">{editingId ? <Pencil size={20} /> : <Plus size={22} />}</span>
            <div><CardTitle>{editingId ? "Edit provider" : "Create new provider"}</CardTitle><CardDescription className="mt-1">Fill in the provider details below</CardDescription></div>
          </div>
        </CardHeader>
        <CardContent className="p-6 sm:p-8">
          <form onSubmit={handleSubmit} className="flex flex-col gap-6">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="admin-field">
                <label className="admin-label">Provider name <span>*</span></label>
                <Input
                  type="text"
                  name="name"
                  placeholder="John's Plumbing"
                  value={form.name}
                  onChange={handleChange}
                  required
                  disabled={loading}
                />
              </div>
              <div className="admin-field">
                <label className="admin-label">Service type <span>*</span></label>
                <AdminSelect
                  value={form.service_type}
                  disabled={loading}
                  onValueChange={(service_type) => setForm((prev) => ({ ...prev, service_type }))}
                  options={SERVICE_TYPES.map((item) => ({ value: item, label: item.charAt(0).toUpperCase() + item.slice(1) }))}
                  icon={<BriefcaseBusiness size={18} />}
                  ariaLabel="Service type"
                />
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="admin-field">
                <label className="admin-label">Region <span>*</span></label>
                <AdminSelect
                  value={form.region}
                  disabled={loading}
                  onValueChange={(region) => setForm((prev) => ({ ...prev, region }))}
                  options={REGIONS.map((item) => ({ value: item, label: item.split("-").map((part) => part.charAt(0).toUpperCase() + part.slice(1)).join(" ") }))}
                  icon={<MapPin size={18} />}
                  ariaLabel="Region"
                />
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium">Rating (0-5)</label>
                <Input
                  type="number"
                  name="rating"
                  placeholder="4.5"
                  step="0.1"
                  min="0"
                  max="5"
                  value={form.rating}
                  onChange={handleChange}
                  disabled={loading}
                />
              </div>
            </div>

            <div className="admin-field">
              <label className="admin-label">Service Area</label>
              <AdminSelect
                value={form.service_areas || "__none"}
                onValueChange={(service_areas) => setForm((prev) => ({ ...prev, service_areas: service_areas === "__none" ? "" : service_areas }))}
                disabled={loading}
                options={[{ value: "__none", label: "Select a service area" }, ...SERVICE_AREAS.map((item) => ({ value: item, label: item.split("-").map((part) => part.charAt(0).toUpperCase() + part.slice(1)).join(" ") }))]}
                icon={<MapPin size={18} />}
                ariaLabel="Service area"
              />
              <p className="text-xs text-muted-foreground">Select the areas where this provider offers services</p>
            </div>

            <div className="admin-field rounded-2xl border border-slate-100 bg-slate-50/70 p-4 sm:p-5">
              <label className="admin-label">
                Provider location <span>*</span>
                {typeof form.lat !== "number" && <span className="text-destructive"> (required)</span>}
              </label>
              <p className="-mt-1 mb-1 text-xs text-slate-500">Click the map or drag the marker to set the provider&apos;s exact service location.</p>
              <MapPicker
                lat={typeof form.lat === "number" ? form.lat : 6.9271}
                lon={typeof form.lon === "number" ? form.lon : 80.7789}
                onLocationChange={(lat, lon) =>
                  setForm((prev) => ({ ...prev, lat, lon }))
                }
              />
              <p className="flex items-center gap-1.5 text-xs font-medium text-slate-500">
                <MapPin size={14} className="text-blue-500" />
                Latitude: {typeof form.lat === "number" ? form.lat.toFixed(4) : "Not set"} | Longitude:{" "}
                {typeof form.lon === "number" ? form.lon.toFixed(4) : "Not set"}
              </p>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium">Phone</label>
                <Input
                  type="tel"
                  name="phone"
                  placeholder="+94 71 234 5678"
                  value={form.phone}
                  onChange={handleChange}
                  disabled={loading}
                />
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium">Years experience</label>
                <Input
                  type="number"
                  name="years_experience"
                  placeholder="5"
                  min="1"
                  value={form.years_experience}
                  onChange={handleChange}
                  disabled={loading}
                />
              </div>
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium">Provider Photo</label>
              <ImageUpload
                currentImage={form.avatar_url}
                onUploadComplete={(url) => setForm((prev) => ({ ...prev, avatar_url: url }))}
              />
            </div>

            {error && <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-destructive">{error}</p>}
            {success && <p className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700"><ShieldCheck size={17} />{success}</p>}

            <div className="flex gap-2">
              <Button type="submit" disabled={loading} size="lg" className="flex-1">
                {!loading && (editingId ? <Pencil size={18} /> : <Plus size={19} />)}
                {loading ? (editingId ? "Updating..." : "Creating...") : editingId ? "Update provider" : "Create provider"}
              </Button>
              {editingId && (
                <Button type="button" variant="outline" onClick={handleCancel} disabled={loading}>
                  Cancel
                </Button>
              )}
            </div>
          </form>
        </CardContent>
        <section className="border-t border-slate-200">
        <CardHeader className="border-b border-slate-100 bg-slate-50/40 px-6 py-5 sm:px-8">
          <div className="flex items-center justify-between gap-4">
            <div><CardTitle className="flex items-center gap-2"><UsersRound size={20} className="text-blue-600" /> All Providers</CardTitle><CardDescription className="mt-1">Manage existing provider profiles</CardDescription></div>
            <span className="rounded-full bg-blue-50 px-3 py-1.5 text-xs font-bold text-blue-700">{providers.length} total</span>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {listLoading ? (
            <p className="p-6 text-sm text-muted-foreground sm:p-8">Loading providers...</p>
          ) : providers.length === 0 ? (
            <p className="p-6 text-sm text-muted-foreground sm:p-8">No providers created yet. Create one above to get started.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="admin-provider-table">
                <thead>
                  <tr>
                    <th>Name</th><th>Service Type</th><th>Region</th><th>Rating</th><th>Experience</th><th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {providers.map((provider) => (
                    <tr key={provider.id}>
                      <td className="font-semibold text-slate-800">{provider.name}</td>
                      <td><span className="admin-service-badge">{provider.service_type}</span></td>
                      <td className="capitalize text-slate-600">{provider.region.replace("-", " ")}</td>
                      <td><span className="font-semibold text-amber-500">★</span> {provider.rating.toFixed(1)}</td>
                      <td>{provider.years_experience} yr{provider.years_experience !== 1 ? "s" : ""}</td>
                      <td><div className="flex gap-2">
                        <Button size="sm" variant="outline" onClick={() => handleEdit(provider)}>
                          <Pencil size={14} /> Edit
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() => setDeleteConfirm(provider.id)}
                          disabled={deleteConfirm === provider.id}
                        >
                          <Trash2 size={14} /> {deleteConfirm === provider.id ? "Sure?" : "Delete"}
                        </Button>
                        {deleteConfirm === provider.id && (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => {
                              handleDelete(provider.id);
                            }}
                          >
                            Confirm
                          </Button>
                        )}
                      </div></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
        </section>
      </Card>
      </div>
    </div>
  );
}
