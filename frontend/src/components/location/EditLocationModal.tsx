import React, { useState, useEffect } from 'react';
import {
  MapPin,
  Building,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Sparkles,
  Info,
  Phone,
  Home,
  ShoppingBag,
  IndianRupee,
  FileText,
  AlertTriangle
} from 'lucide-react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { UnknownLocationRecord, PostalOffice } from '../../types';
import { postalApi } from '../../services/postalApi';
import { locationApi } from '../../services/locationApi';
import { formatCurrency, formatNumber } from '../../utils/formatters';

interface EditLocationModalProps {
  isOpen: boolean;
  onClose: () => void;
  record: UnknownLocationRecord | null;
  onSuccess: () => void;
}

export const EditLocationModal: React.FC<EditLocationModalProps> = ({
  isOpen,
  onClose,
  record,
  onSuccess,
}) => {
  const [pincode, setPincode] = useState('');
  const [district, setDistrict] = useState('');
  const [postOffice, setPostOffice] = useState('');
  const [state, setState] = useState('');
  const [notes, setNotes] = useState('');

  // Postal API lookup state
  const [lookupLoading, setLookupLoading] = useState(false);
  const [availableOffices, setAvailableOffices] = useState<PostalOffice[]>([]);
  const [postalFound, setPostalFound] = useState<boolean | null>(null);

  // Form submission state
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (record) {
      setPincode(record.pincode || '');
      setDistrict(record.district || '');
      setPostOffice(record.post_office || '');
      setState(record.state || '');
      setNotes('');
      setAvailableOffices([]);
      setPostalFound(null);
      setError(null);

      // If record already has a valid 6-digit pin, look up offices for it
      if (record.pincode && record.pincode.length === 6 && /^\d{6}$/.test(record.pincode)) {
        handlePostalLookup(record.pincode, false);
      }
    }
  }, [record]);

  const handlePostalLookup = async (pin: string, autoFillDistrict = true) => {
    if (!pin || pin.length !== 6 || !/^\d{6}$/.test(pin)) {
      setAvailableOffices([]);
      setPostalFound(null);
      return;
    }

    setLookupLoading(true);
    setPostalFound(null);
    try {
      const data = await postalApi.getByPincode(pin);
      if (data) {
        setPostalFound(true);
        if (autoFillDistrict) {
          if (data.district) setDistrict(data.district);
          if (data.state) setState(data.state);
        }
        if (data.offices && data.offices.length > 0) {
          setAvailableOffices(data.offices);
          // If only 1 post office and none selected yet, auto-select it
          if (data.offices.length === 1 && !postOffice) {
            setPostOffice(data.offices[0].office_name);
          }
        } else {
          setAvailableOffices([]);
        }
      } else {
        setPostalFound(false);
        setAvailableOffices([]);
      }
    } catch (err) {
      console.error('Postal lookup error:', err);
      setPostalFound(false);
      setAvailableOffices([]);
    } finally {
      setLookupLoading(false);
    }
  };

  const handlePincodeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value.replace(/\D/g, '').slice(0, 6);
    setPincode(val);
    if (val.length === 6) {
      handlePostalLookup(val, true);
    } else {
      setAvailableOffices([]);
      setPostalFound(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!record) return;

    if (!pincode && !district) {
      setError('Please provide at least a valid Pincode or District.');
      return;
    }

    if (pincode && pincode.length !== 6) {
      setError('Pincode must be a valid 6-digit number.');
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      await locationApi.correctLocation(record.id, {
        pincode: pincode || undefined,
        district: district || undefined,
        post_office: postOffice || undefined,
        state: state || undefined,
        notes: notes || undefined,
        source: postalFound ? 'POSTAL_API' : 'MANUAL'
      });
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to correct location');
    } finally {
      setSubmitting(false);
    }
  };

  if (!record) return null;

  const isUnknownDistrict = !record.district || record.district.toLowerCase().includes('unknown') || record.district.toLowerCase().includes('unassigned');
  const isUnknownPincode = !record.pincode || record.pincode.toLowerCase().includes('unknown') || record.pincode === '000000' || record.pincode.length !== 6;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Correct Location Details"
      maxWidth="2xl"
      actionFooter={
        <div className="flex items-center justify-between w-full">
          <div className="text-xs text-slate-500">
            {postalFound ? (
              <span className="text-emerald-600 font-semibold flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> Verified via India Post
              </span>
            ) : (
              <span>Manual correction</span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={onClose} disabled={submitting}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleSubmit} isLoading={submitting}>
              Save & Verify Location
            </Button>
          </div>
        </div>
      }
    >
      <div className="space-y-5">
        {error && (
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* ------------------------------------------------------------- */}
        {/* SECTION 1: Complete Full Row Details of Customer on File     */}
        {/* ------------------------------------------------------------- */}
        <div className="border border-slate-200 rounded-xl bg-slate-50/70 p-4 space-y-3.5 shadow-2xs">
          {/* Header Row */}
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-3">
            <div>
              <div className="flex items-center gap-2">
                <h4 className="text-sm font-bold text-slate-900">{record.customer_name}</h4>
                <span className="text-[11px] font-mono font-semibold bg-white border border-slate-300 text-slate-600 px-2 py-0.5 rounded">
                  ID #{record.id}
                </span>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-600 mt-1">
                <Phone className="w-3.5 h-3.5 text-slate-400" />
                <span className="font-mono font-medium">{record.contact_number || record.normalized_contact || 'No Contact Number'}</span>
              </div>
            </div>

            {/* Issue Badges */}
            <div className="flex items-center gap-1.5">
              {isUnknownDistrict && (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
                  <AlertTriangle className="w-3 h-3 text-rose-600" /> Unknown District
                </span>
              )}
              {isUnknownPincode && (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
                  <AlertTriangle className="w-3 h-3 text-amber-600" /> Unknown Pincode
                </span>
              )}
            </div>
          </div>

          {/* Full Address on File */}
          <div className="bg-white p-3 rounded-lg border border-slate-200 space-y-1 shadow-2xs">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1">
              <Home className="w-3 h-3 text-slate-400" /> Full Shipping Address on File
            </span>
            <p className="text-xs text-slate-800 leading-relaxed font-medium">
              {record.full_address || <span className="text-slate-400 italic">No street address provided in raw file</span>}
            </p>
          </div>

          {/* Current Row Values Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs">
            <div className="bg-white p-2.5 rounded-lg border border-slate-200">
              <span className="text-[10px] font-semibold text-slate-500 block uppercase">District on File</span>
              <span className={`font-bold mt-0.5 block ${isUnknownDistrict ? 'text-rose-600' : 'text-slate-900'}`}>
                {record.district || 'Unknown'}
              </span>
            </div>

            <div className="bg-white p-2.5 rounded-lg border border-slate-200">
              <span className="text-[10px] font-semibold text-slate-500 block uppercase">Pincode on File</span>
              <span className={`font-mono font-bold mt-0.5 block ${isUnknownPincode ? 'text-amber-600' : 'text-slate-900'}`}>
                {record.pincode || 'Unknown'}
              </span>
            </div>

            <div className="bg-white p-2.5 rounded-lg border border-slate-200">
              <span className="text-[10px] font-semibold text-slate-500 block uppercase">Post Office</span>
              <span className="text-slate-800 font-medium mt-0.5 block truncate">
                {record.post_office || '—'}
              </span>
            </div>

            <div className="bg-white p-2.5 rounded-lg border border-slate-200">
              <span className="text-[10px] font-semibold text-slate-500 block uppercase">Total Spend & Orders</span>
              <span className="text-emerald-600 font-bold mt-0.5 block">
                {formatCurrency(record.total_spend)} <span className="text-slate-500 font-normal text-[11px]">({record.total_orders})</span>
              </span>
            </div>
          </div>
        </div>

        {/* ------------------------------------------------------------- */}
        {/* SECTION 2: Correction & Postal Enrichment Form                */}
        {/* ------------------------------------------------------------- */}
        <form onSubmit={handleSubmit} className="space-y-4 pt-1">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5 text-indigo-600" /> Location Correction & India Post Auto-Lookup
            </h4>
            <span className="text-[11px] text-slate-500">Entering 6-digit PIN auto-enriches District & State</span>
          </div>

          {/* PIN Code Input with Live Postal API Lookup */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5 text-indigo-600" /> New Postal PIN Code (6 Digits)
              </label>
              {lookupLoading && (
                <span className="text-[11px] text-indigo-600 flex items-center gap-1 font-medium">
                  <Loader2 className="w-3 h-3 animate-spin" /> Verifying India Post...
                </span>
              )}
              {postalFound === true && (
                <span className="text-[11px] text-emerald-600 flex items-center gap-1 font-medium">
                  <CheckCircle2 className="w-3 h-3" /> Postal Data Found & Enriched
                </span>
              )}
              {postalFound === false && (
                <span className="text-[11px] text-amber-600 flex items-center gap-1 font-medium">
                  <Info className="w-3 h-3" /> Not in postal cache (manual entry)
                </span>
              )}
            </div>
            <div className="relative">
              <input
                type="text"
                placeholder="e.g. 676505"
                value={pincode}
                onChange={handlePincodeChange}
                maxLength={6}
                className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-indigo-500 shadow-2xs font-mono tracking-wider font-semibold"
              />
            </div>
          </div>

          {/* Post Office (Dropdown if multiple POs exist for PIN) */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-700 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <Building className="w-3.5 h-3.5 text-slate-500" /> Post Office Branch
              </span>
              {availableOffices.length > 1 && (
                <span className="text-[10px] text-indigo-600 font-medium">
                  {availableOffices.length} branches available for PIN {pincode}
                </span>
              )}
            </label>

            {availableOffices.length > 0 ? (
              <select
                value={postOffice}
                onChange={(e) => setPostOffice(e.target.value)}
                className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-indigo-500 shadow-2xs font-medium"
              >
                <option value="">-- Select Post Office Branch --</option>
                {availableOffices.map((po, idx) => (
                  <option key={`${po.office_name}-${idx}`} value={po.office_name}>
                    {po.office_name} {po.delivery_status ? `(${po.delivery_status})` : ''}
                  </option>
                ))}
              </select>
            ) : (
              <input
                type="text"
                placeholder="e.g. Manjeri H.O"
                value={postOffice}
                onChange={(e) => setPostOffice(e.target.value)}
                className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-indigo-500 shadow-2xs"
              />
            )}
          </div>

          {/* District & State Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700">Correct District</label>
              <input
                type="text"
                placeholder="e.g. Malappuram"
                value={district}
                onChange={(e) => setDistrict(e.target.value)}
                className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-indigo-500 shadow-2xs font-medium"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700">State</label>
              <input
                type="text"
                placeholder="e.g. Kerala"
                value={state}
                onChange={(e) => setState(e.target.value)}
                className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-indigo-500 shadow-2xs"
              />
            </div>
          </div>

          {/* Correction Audit Notes */}
          <div className="space-y-1.5 pt-1">
            <label className="text-xs font-semibold text-slate-600">Correction Notes / Reason (Optional)</label>
            <input
              type="text"
              placeholder="e.g. Verified from customer shipping address on file"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full bg-white border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-slate-700 placeholder-slate-400 focus:outline-none focus:border-indigo-500 shadow-2xs"
            />
          </div>
        </form>
      </div>
    </Modal>
  );
};
