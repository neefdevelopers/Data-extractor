import React, { useState, useEffect } from 'react';
import {
  MapPin,
  Building,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Info,
  FileSpreadsheet,
  Hash,
  Calendar,
  Layers,
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
  Search,
  Sparkles
} from 'lucide-react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { UnknownLocationRecord, PostalOffice } from '../../types';
import { postalApi } from '../../services/postalApi';
import { locationApi } from '../../services/locationApi';
import { formatCurrency, formatDate } from '../../utils/formatters';

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

  // Raw details inspection state
  const [showRawDetails, setShowRawDetails] = useState(true);
  const [rawSearch, setRawSearch] = useState('');
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

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
      setShowRawDetails(true);
      setRawSearch('');

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
            if (data.offices[0].district) setDistrict(data.offices[0].district);
            if (data.offices[0].state) setState(data.offices[0].state);
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

  const handleSelectPostOffice = (poName: string) => {
    setPostOffice(poName);
    const office = availableOffices.find((o) => o.office_name === poName);
    if (office) {
      if (office.district) setDistrict(office.district);
      if (office.state) setState(office.state);
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

  const handleCopy = (text: string, keyName: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(keyName);
    setTimeout(() => setCopiedKey(null), 2000);
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

  // Prepare raw entries for full details display
  const rawEntries: [string, any][] = record.raw_row_data
    ? Object.entries(record.raw_row_data)
    : [
        ['Customer Name', record.customer_name],
        ['Contact Number', record.contact_number || record.normalized_contact || ''],
        ['Full Address', record.full_address || ''],
        ['Pincode', record.pincode || ''],
        ['Post Office', record.post_office || ''],
        ['Uploaded District', record.source_district || record.district || ''],
        ['State', record.state || 'Kerala'],
        ['Total Orders', record.total_orders],
        ['Total Spend', formatCurrency(record.total_spend)],
      ];

  const filteredRawEntries = rawEntries.filter(([key, val]) => {
    if (!rawSearch) return true;
    const q = rawSearch.toLowerCase();
    return key.toLowerCase().includes(q) || String(val).toLowerCase().includes(q);
  });

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
      <div className="space-y-4">
        {error && (
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* ------------------------------------------------------------- */}
        {/* SOURCE DOCUMENT & RAW ROW PROMINENT BANNER                     */}
        {/* ------------------------------------------------------------- */}
        <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white rounded-xl p-3.5 shadow-md border border-slate-800">
          <div className="flex flex-wrap items-center justify-between gap-3">
            {/* Document and Row Info */}
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-indigo-500/20 border border-indigo-400/30 flex items-center justify-center shrink-0">
                <FileSpreadsheet className="w-5 h-5 text-indigo-300" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-indigo-200 font-medium">Source Document:</span>
                  <span className="text-xs font-bold text-white tracking-wide truncate max-w-xs md:max-w-md">
                    {record.source_file_name || 'Direct Import / System Record'}
                  </span>
                </div>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-indigo-500/30 text-indigo-200 text-[11px] font-mono font-bold border border-indigo-400/40">
                    <Hash className="w-3 h-3 text-indigo-300" />
                    {record.source_row_number ? `Raw Row #${record.source_row_number}` : 'Row # Unspecified'}
                  </span>
                  <span className="text-[11px] text-slate-300 font-mono">Customer ID #{record.id}</span>
                </div>
              </div>
            </div>

            {/* Customer & Timestamp badge */}
            <div className="flex items-center gap-2">
              <div className="text-right hidden sm:block">
                <div className="text-xs font-semibold text-white">{record.customer_name}</div>
                <div className="text-[11px] text-indigo-200">
                  {record.contact_number || record.normalized_contact || 'No contact on file'}
                </div>
              </div>
              <div className="text-[10px] text-slate-300 bg-slate-800/80 px-2.5 py-1 rounded border border-slate-700 flex items-center gap-1">
                <Calendar className="w-3 h-3 text-slate-400" />
                {formatDate(record.created_at)}
              </div>
            </div>
          </div>
        </div>

        {/* ------------------------------------------------------------- */}
        {/* SECTION 1: Full Details of That Raw Row (Expandable / Clean)  */}
        {/* ------------------------------------------------------------- */}
        <div className="border border-slate-200 rounded-xl bg-white shadow-2xs overflow-hidden">
          <div
            className="p-3 bg-slate-50/80 border-b border-slate-200 flex items-center justify-between cursor-pointer hover:bg-slate-100/80 transition-colors"
            onClick={() => setShowRawDetails(!showRawDetails)}
          >
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-indigo-600" />
              <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Full Details of Uploaded Raw Row
              </span>
              <span className="text-[10px] font-semibold bg-indigo-100 text-indigo-800 px-2 py-0.5 rounded-full">
                {rawEntries.length} Columns / Values
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                className="text-xs font-semibold text-slate-500 hover:text-slate-800 flex items-center gap-1"
                onClick={(e) => {
                  e.stopPropagation();
                  setShowRawDetails(!showRawDetails);
                }}
              >
                <span>{showRawDetails ? 'Collapse Details' : 'View Full Raw Row'}</span>
                {showRawDetails ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              </button>
            </div>
          </div>

          {showRawDetails && (
            <div className="p-3 space-y-2.5 bg-slate-50/30">
              {/* Quick Filter Search for Raw Columns */}
              {rawEntries.length > 6 && (
                <div className="flex items-center justify-between gap-3">
                  <div className="relative flex-1 max-w-xs">
                    <Search className="w-3 h-3 absolute left-2.5 top-2 text-slate-400" />
                    <input
                      type="text"
                      placeholder="Filter raw columns..."
                      value={rawSearch}
                      onChange={(e) => setRawSearch(e.target.value)}
                      className="w-full bg-white border border-slate-200 rounded-md pl-7 pr-2 py-1 text-[11px] text-slate-800 placeholder-slate-400 focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                  <span className="text-[10px] text-slate-500">
                    Original uncleaned data extracted directly from spreadsheet
                  </span>
                </div>
              )}

              {/* Grid of All Raw Columns & Values */}
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 max-h-56 overflow-y-auto pr-1">
                {filteredRawEntries.map(([key, val]) => {
                  const valStr = val !== null && val !== undefined ? String(val) : '';
                  const isLocationKey = /pincode|district|address|location|city|town|post|state/i.test(key);
                  const isCopied = copiedKey === key;

                  return (
                    <div
                      key={key}
                      className={`p-2 rounded-lg border text-xs flex flex-col justify-between transition-all ${
                        isLocationKey
                          ? 'bg-amber-50/40 border-amber-200/70 hover:border-amber-300'
                          : 'bg-white border-slate-200 hover:border-slate-300'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-1 mb-1">
                        <span className="font-semibold text-slate-500 text-[10px] uppercase tracking-wider truncate">
                          {key}
                        </span>
                        {valStr && (
                          <button
                            type="button"
                            title="Copy value"
                            onClick={() => handleCopy(valStr, key)}
                            className="text-slate-400 hover:text-slate-700 p-0.5 rounded transition-colors"
                          >
                            {isCopied ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
                          </button>
                        )}
                      </div>
                      <div className="font-medium text-slate-900 break-words text-[11px] leading-relaxed">
                        {valStr ? (
                          valStr
                        ) : (
                          <span className="text-slate-400 italic text-[10px]">Empty / Not provided</span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* ------------------------------------------------------------- */}
        {/* SECTION 2: Current Location Status & India Post Auto-Lookup   */}
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
                onChange={(e) => handleSelectPostOffice(e.target.value)}
                className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-indigo-500 shadow-2xs font-medium"
              >
                <option value="">-- Select Post Office Branch --</option>
                {availableOffices.map((po, idx) => (
                  <option key={`${po.office_name}-${idx}`} value={po.office_name}>
                    {po.office_name} {po.delivery_status ? `(${po.delivery_status})` : ''} — {po.district || 'Kerala'}
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
              <label className="text-xs font-semibold text-slate-700">Correct Kerala District</label>
              <input
                type="text"
                list="kerala-districts-list"
                placeholder="e.g. Malappuram"
                value={district}
                onChange={(e) => setDistrict(e.target.value)}
                className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-indigo-500 shadow-2xs font-medium"
              />
              <datalist id="kerala-districts-list">
                <option value="Alappuzha" />
                <option value="Ernakulam" />
                <option value="Idukki" />
                <option value="Kannur" />
                <option value="Kasaragod" />
                <option value="Kollam" />
                <option value="Kottayam" />
                <option value="Kozhikode" />
                <option value="Malappuram" />
                <option value="Palakkad" />
                <option value="Pathanamthitta" />
                <option value="Thiruvananthapuram" />
                <option value="Thrissur" />
                <option value="Wayanad" />
              </datalist>
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
