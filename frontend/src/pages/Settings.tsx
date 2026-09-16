import React, { useEffect, useState } from 'react';
import {
  Settings as SettingsIcon,
  Shield,
  Save,
  CheckCircle2,
  Database,
  Globe,
  Flame,
  AlertCircle
} from 'lucide-react';
import { Header } from '../components/layout/Header';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { LoadingSkeleton } from '../components/common/LoadingSkeleton';
import { settingsApi } from '../services/settingsApi';
import { SystemSettings } from '../types';

export const Settings: React.FC = () => {
  const [settings, setSettings] = useState<SystemSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    settingsApi
      .getSettings()
      .then((data) => setSettings(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const handleToggleRevenueRule = (key: keyof SystemSettings['revenue_rules']) => {
    if (!settings) return;
    setSettings({
      ...settings,
      revenue_rules: {
        ...settings.revenue_rules,
        [key]: !settings.revenue_rules[key],
      },
    });
  };

  const handleSaveRevenueRules = async () => {
    if (!settings) return;
    setIsSaving(true);
    setSuccessMsg(null);
    try {
      await settingsApi.updateRevenueRules(settings.revenue_rules);
      setSuccessMsg('Revenue eligibility rules updated! Order revenue and RFM scores have been recalculated.');
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err: any) {
      alert('Error saving rules: ' + err.message);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div>
      <Header
        title="Platform & Revenue Settings"
        subtitle="Configure centralized RevenueService eligibility rules, RFM algorithms, and local system parameters"
      />

      <div className="p-8 max-w-5xl mx-auto space-y-6">
        {successMsg && (
          <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center gap-2 text-xs text-emerald-800 shadow-2xs">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span className="font-medium">{successMsg}</span>
          </div>
        )}

        {loading || !settings ? (
          <LoadingSkeleton rows={6} />
        ) : (
          <div className="space-y-6">
            {/* Revenue Eligibility Card */}
            <Card
              title="RevenueService Qualification Rules"
              subtitle="Define which order statuses contribute to qualifying sales revenue, customer spend, and RFM scores"
            >
              <div className="space-y-4 pt-2">
                {/* Policy Explanations */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 p-3.5 bg-slate-50 rounded-xl border border-slate-200 text-xs">
                  <div className="space-y-1">
                    <span className="font-bold text-amber-800 flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-amber-500"></span>
                      Cash on Delivery (COD) Policy
                    </span>
                    <p className="text-[11px] text-slate-600 leading-relaxed">
                      COD revenue is recognized <strong>only upon successful delivery</strong> (<code className="text-slate-800 bg-white px-1 py-0.5 rounded border border-slate-200">DELIVERED</code> or <code className="text-slate-800 bg-white px-1 py-0.5 rounded border border-slate-200">COMPLETED</code>). Uncollected, pending, or returned (RTO) COD shipments contribute ₹0.
                    </p>
                  </div>

                  <div className="space-y-1">
                    <span className="font-bold text-blue-800 flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                      Prepaid Orders Policy
                    </span>
                    <p className="text-[11px] text-slate-600 leading-relaxed">
                      Prepaid transactions (Card, UPI, Netbanking) are recognized as realized sales. If an order is marked <code className="text-slate-800 bg-white px-1 py-0.5 rounded border border-slate-200">CANCELLED</code>, <code className="text-slate-800 bg-white px-1 py-0.5 rounded border border-slate-200">RETURNED</code>, or <code className="text-slate-800 bg-white px-1 py-0.5 rounded border border-slate-200">REFUNDED</code>, revenue is reversed.
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {[
                    { key: 'delivered_eligible', label: 'DELIVERED Orders', desc: 'Orders successfully delivered to customers (Recognizes both COD & Prepaid revenue)' },
                    { key: 'completed_eligible', label: 'COMPLETED Orders', desc: 'Fulfilled orders closed successfully' },
                    { key: 'pending_eligible', label: 'PENDING / PROCESSING Orders', desc: 'Orders currently being packed or dispatched' },
                    { key: 'returned_eligible', label: 'RETURNED / RTO Orders', desc: 'Orders returned by customer or courier' },
                    { key: 'refunded_eligible', label: 'REFUNDED Orders', desc: 'Orders where payments were refunded' },
                    { key: 'cancelled_eligible', label: 'CANCELLED Orders', desc: 'Orders cancelled prior to or post delivery' },
                  ].map((rule) => {
                    const isChecked = Boolean(settings.revenue_rules[rule.key as keyof SystemSettings['revenue_rules']]);
                    return (
                      <div
                        key={rule.key}
                        onClick={() => handleToggleRevenueRule(rule.key as keyof SystemSettings['revenue_rules'])}
                        className={`p-4 rounded-xl border cursor-pointer transition-all flex items-start justify-between gap-3 shadow-2xs ${
                          isChecked
                            ? 'bg-indigo-50/70 border-indigo-300'
                            : 'bg-white border-slate-200 hover:border-slate-300 hover:bg-slate-50/50'
                        }`}
                      >
                        <div>
                          <span className={`text-xs font-bold block ${isChecked ? 'text-indigo-900' : 'text-slate-800'}`}>
                            {rule.label}
                          </span>
                          <span className={`text-[11px] block mt-0.5 ${isChecked ? 'text-indigo-700' : 'text-slate-500'}`}>{rule.desc}</span>
                        </div>

                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => {}}
                          className="mt-0.5 h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 bg-white"
                        />
                      </div>
                    );
                  })}
                </div>

                <div className="flex justify-end pt-4 border-t border-slate-100">
                  <Button
                    size="sm"
                    variant="primary"
                    icon={<Save className="w-3.5 h-3.5" />}
                    isLoading={isSaving}
                    onClick={handleSaveRevenueRules}
                  >
                    Save & Recalculate Platform Revenue
                  </Button>
                </div>
              </div>
            </Card>

            {/* RFM Model & Weights Configuration */}
            <Card
              title="RFM Segmentation Engine & Dimension Weights"
              subtitle="Configure mathematical quintile weights and clustering parameters"
            >
              <div className="space-y-4 pt-2 text-xs">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5 shadow-2xs">
                    <span className="font-bold text-cyan-700 block">Recency Weight</span>
                    <span className="text-xl font-extrabold text-slate-900">
                      {((settings.rfm_settings?.recency_weight || 0.33) * 100).toFixed(0)}%
                    </span>
                    <span className="text-[11px] text-slate-500 block">Weight assigned to days since last purchase</span>
                  </div>

                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5 shadow-2xs">
                    <span className="font-bold text-emerald-700 block">Frequency Weight</span>
                    <span className="text-xl font-extrabold text-slate-900">
                      {((settings.rfm_settings?.frequency_weight || 0.33) * 100).toFixed(0)}%
                    </span>
                    <span className="text-[11px] text-slate-500 block">Weight assigned to repeat order count</span>
                  </div>

                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5 shadow-2xs">
                    <span className="font-bold text-amber-700 block">Monetary Weight</span>
                    <span className="text-xl font-extrabold text-slate-900">
                      {((settings.rfm_settings?.monetary_weight || 0.34) * 100).toFixed(0)}%
                    </span>
                    <span className="text-[11px] text-slate-500 block">Weight assigned to cumulative sales spend</span>
                  </div>
                </div>

                <div className="p-3 bg-indigo-50 border border-indigo-100 rounded-xl text-[11px] text-indigo-800 flex items-center justify-between">
                  <span>RFM scores are dynamically assigned via percentile quintiles (1 = Lowest 20%, 5 = Top 20%).</span>
                  <span className="font-semibold text-indigo-900">7 Segment Clusters Active</span>
                </div>
              </div>
            </Card>

            {/* Local Environment & Database Status */}
            <Card title="System Environment" subtitle="Local architecture parameters">
              <div className="space-y-3 pt-2 text-xs">
                <div className="flex items-center justify-between p-3 bg-slate-50 rounded-xl border border-slate-200 shadow-2xs">
                  <div className="flex items-center gap-2.5">
                    <Database className="w-4 h-4 text-emerald-600" />
                    <div>
                      <span className="font-semibold text-slate-800 block">Database Storage</span>
                      <span className="text-slate-500 text-[11px]">{settings.database_url_masked}</span>
                    </div>
                  </div>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                    ONLINE
                  </span>
                </div>

                <div className="flex items-center justify-between p-3 bg-slate-50 rounded-xl border border-slate-200 shadow-2xs">
                  <div className="flex items-center gap-2.5">
                    <Globe className="w-4 h-4 text-indigo-600" />
                    <div>
                      <span className="font-semibold text-slate-800 block">India Postal PIN API</span>
                      <span className="text-slate-500 text-[11px]">{settings.postal_api_url}</span>
                    </div>
                  </div>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
                    CACHED MASTER
                  </span>
                </div>
              </div>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
};
