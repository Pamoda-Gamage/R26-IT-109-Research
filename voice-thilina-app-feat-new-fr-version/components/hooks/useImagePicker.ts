"use client";
import { useCallback, useEffect, useRef, useState } from "react";

/**
 * File-input photo picker with an object-URL preview. UI-agnostic — render a
 * button that calls `pick()` and a hidden <input {...inputProps} />.
 */
export interface UseImagePicker {
  file: File | null;
  previewUrl: string | null;
  pick: () => void;
  discard: () => void;
  inputProps: {
    ref: React.RefObject<HTMLInputElement | null>;
    type: "file";
    accept: string;
    capture: "environment";
    hidden: true;
    onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  };
}

export function useImagePicker(): UseImagePicker {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const urlRef = useRef<string | null>(null);

  useEffect(() => {
    return () => {
      if (urlRef.current) URL.revokeObjectURL(urlRef.current);
    };
  }, []);

  const discard = useCallback(() => {
    if (urlRef.current) {
      URL.revokeObjectURL(urlRef.current);
      urlRef.current = null;
    }
    setFile(null);
    setPreviewUrl(null);
  }, []);

  const onChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const picked = e.target.files?.[0];
      e.target.value = ""; // allow re-selecting the same file
      if (!picked) return;
      if (urlRef.current) URL.revokeObjectURL(urlRef.current);
      urlRef.current = URL.createObjectURL(picked);
      setFile(picked);
      setPreviewUrl(urlRef.current);
    },
    [],
  );

  const pick = useCallback(() => inputRef.current?.click(), []);

  return {
    file,
    previewUrl,
    pick,
    discard,
    inputProps: {
      ref: inputRef,
      type: "file",
      accept: "image/*",
      capture: "environment",
      hidden: true,
      onChange,
    },
  };
}
