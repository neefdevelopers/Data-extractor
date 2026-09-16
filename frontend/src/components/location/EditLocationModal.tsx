import React, { useState, useEffect } from 'react';
import {
  MapPin,
  Building,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Info
} from 'lucide-react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { UnknownLocationRecord, PostalOffice } from '../../types';
import { postalApi } from '../../services/postalApi';
import { locationApi } from '../../services/locationApi';
import { formatCurrency } from '../../utils/formatters';

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

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Correct Location Details"
      maxWidth="4xl"
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
        {/* SECTION 1: Exact Full Row Details as in Table                 */}
        {/* ------------------------------------------------------------- */}
        <div className="overflow-x-auto border border-slate-200 rounded-xl bg-slate-50/50 shadow-2xs">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-slate-100/90 border-b border-slate-200 text-slate-500 uppercase font-semibold text-[10px] tracking-wider">
              <tr>
                <th className="p-3 pl-3.5">Customer Information</th>
                <th className="p-3">Address on File</th>
                <th className="p-3">District</th>
                <th className="p-3">Pincode</th>
                <th className="p-3 pr-3.5">Orders & Spend</th>
              </tr>
            </thead>
            <tbody className="bg-white">
              <tr>
                <td className="p-3 pl-3.5 align-top">
                  <div className="space-y-0.5">
                    <span className="font-semibold text-slate-900 block">{record.customer_name}</span>
                    <span className="text-slate-500 text-[11px] block">
                      {record.contact_number || record.normalized_contact || 'No Contact'}
                    </span>
                    <span className="text-[10px] text-slate-400 font-mono">ID #{record.id}</span>
                  </div>
                </td>

                <td className="p-3 align-top max-w-xs">
                  <p className="text-slate-700 text-[11px] leading-relaxed">
                    {record.full_address || <span className="text-slate-400 italic">No address on file</span>}
                  </p>
                  {record.post_office && (
                    <span className="text-[10px] text-slate-500 font-medium block mt-0.5">
                      PO: {record.post_office}
                    </span>
                  )}
                </td>

                <td className="p-3 align-top">
                  {record.district ? (
                    <span className="font-semibold text-slate-900">{record.district}</span>
                  ) : (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
                      Unknown District
                    </span>
                  )}
                </td>

                <td className="p-3 align-top">
                  {record.pincode ? (
                    <span className="font-bold text-slate-900 font-mono tracking-wider">
                      {record.pincode}
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
                      Unknown PIN
                    </span>
                  )}
                </td>

                <td className="p-3 pr-3.5 align-top">
                  <div className="space-y-0.5 text-[11px]">
                    <span className="font-bold text-slate-800 block">
                      {formatCurrency(record.total_spend)}
                    </span>
                    <span className="text-slate-500">{record.total_orders} Orders</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
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
