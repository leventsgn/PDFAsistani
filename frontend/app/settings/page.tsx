"use client";

import { useEffect, useState } from "react";
import type { ChangeEvent } from "react";

// Render'da NEXT_PUBLIC_API_URL sadece hostname döner, https:// ekle
const apiHost = process.env.NEXT_PUBLIC_API_URL;
const API_BASE = apiHost 
  ? (apiHost.startsWith("http") ? apiHost : `https://${apiHost}`)
  : (process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000");

type SettingsResponse = {
  chat_base_url: string;
  chat_model: string;
};

export default function SettingsPage() {
  const [chatBaseUrl, setChatBaseUrl] = useState("https://api.groq.com/openai/v1");
  const [chatModel, setChatModel] = useState("llama-3.3-70b-versatile");
  const [chatApiKey, setChatApiKey] = useState("");
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<string>("");

  async function loadSettings() {
    try {
      const r = await fetch(`${API_BASE}/settings`);
      if (!r.ok) throw new Error(await r.text());
      const data: SettingsResponse = await r.json();
      setChatBaseUrl(data.chat_base_url);
      setChatModel(data.chat_model);
      const storedKey = window.localStorage.getItem("llm_api_key") || "";
      setChatApiKey(storedKey);
    } catch (e: any) {
      setStatus(e?.message || String(e));
    }
  }

  useEffect(() => {
    loadSettings();
  }, []);

  async function onSave() {
    setSaving(true);
    setStatus("");
    try {
      window.localStorage.setItem("llm_api_key", chatApiKey);
      const r = await fetch(`${API_BASE}/settings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chat_base_url: chatBaseUrl,
          chat_model: chatModel,
          chat_api_key: chatApiKey || undefined,
        }),
      });
      if (!r.ok) throw new Error(await r.text());
      const data: SettingsResponse = await r.json();
      setChatBaseUrl(data.chat_base_url);
      setChatModel(data.chat_model);
      setStatus("Kaydedildi.");
    } catch (e: any) {
      setStatus(e?.message || String(e));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div style={{ maxWidth: 720 }}>
      <h2 style={{ marginTop: 0 }}>LLM Ayarları</h2>
      <div style={{ display: "grid", gap: 12 }}>
        <label style={{ display: "grid", gap: 6 }}>
          <span>Chat Base URL</span>
          <input
            value={chatBaseUrl}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setChatBaseUrl(e.target.value)}
            placeholder="https://api.groq.com/openai/v1"
            style={{ padding: 10, borderRadius: 8, border: "1px solid #ddd" }}
          />
        </label>

        <label style={{ display: "grid", gap: 6 }}>
          <span>Chat Model</span>
          <input
            value={chatModel}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setChatModel(e.target.value)}
            placeholder="gpt-oss-20b"
            style={{ padding: 10, borderRadius: 8, border: "1px solid #ddd" }}
          />
        </label>

        <label style={{ display: "grid", gap: 6 }}>
          <span>API Key</span>
          <input
            value={chatApiKey}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setChatApiKey(e.target.value)}
            placeholder="sk-..."
            type="password"
            style={{ padding: 10, borderRadius: 8, border: "1px solid #ddd" }}
          />
          <span style={{ fontSize: 12, color: "#666" }}>
            API key sadece bu tarayıcıdan gönderilir; sunucudan geri okunmaz.
          </span>
        </label>

        <button
          onClick={onSave}
          disabled={saving}
          style={{ padding: "10px 14px", borderRadius: 8, border: "1px solid #ddd", background: "#fafafa" }}
        >
          {saving ? "Kaydediliyor..." : "Kaydet"}
        </button>

        {status && <div style={{ color: status === "Kaydedildi." ? "#1a7f37" : "#b42318" }}>{status}</div>}
      </div>
    </div>
  );
}
