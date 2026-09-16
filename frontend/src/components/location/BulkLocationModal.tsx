import React, { useState } from 'react';
import {
  Layers,
  AlertCircle,
  MapPin,
  Building,
  CheckCircle2
} from 'lucide-react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { locationApi } from '../../services/locationApi';
import { postalApi } from '../../services/postalApi';

interface BulkLocationModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedIds: number[];
  onSuccess: () => void;
}

export const BulkLocationModal: React.FC<BulkLocationModalProps> = ({
  isOpen,
  onClose,
  selectedIds,
  onSuccess,
}) => {
  const [district, setDistrict] = useState('');
  const [pincode, setPincode] = useState('');
  const [postOffice, setPostOffice] = useState('');
  const [state, setState] = useState('');
  const [notes, setNotes] = useState('');

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedIds.length === 0) return;

    if (!district && !pincode && !postOffice && !state) {
      setError('Please provide at least one field to update.');
      return;
    }

    if (pincode && pincode.length !== 6) {
      setError('Pincode must be a 6-digit number.');
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      await locationApi.bulkCorrectLocations({
        customer_ids: selectedIds,
        district: district || undefined,
        pincode: pincode || undefined,
        post_office: postOffice || undefined,
        state: state || undefined,
        notes: notes || `Bulk update for ${selectedIds.length} records`,
        source: 'BULK_UPDATE'
      });
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to apply bulk update');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Bulk Update Location Data"
      maxWidth="md"
      actionFooter={
        <div className="flex items-center justify-end gap-2 w-full">
          <Button variant="outline" onClick={onClose} disabled={submitting}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleSubmit} isLoading={submitting}>
            Apply to {selectedIds.length} Records
          </Button>
        </div>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <p className="text-xs text-slate-500 mb-2">
          Apply verified location values to <span className="font-semibold text-slate-800">{selectedIds.length}</span> selected customer records.
        </p>
        {error && (
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-amber-800 text-xs space-y-1">
          <p className="font-semibold flex items-center gap-1.5">
            <Layers className="w-4 h-4 text-amber-600" /> Safe Bulk Update Rules:
          </p>
          <p className="text-[11px] text-amber-700/90 leading-relaxed">
            Only filled fields will be updated. Blank fields will preserve each customer's existing data without overwriting.
          </p>
        </div>

        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-700">District to Apply</label>
          <input
            type="text"
            placeholder="e.g. Malappuram (leave empty to keep unchanged)"
            value={district}
            onChange={(e) => setDistrict(e.target.value)}
            className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-indigo-500 shadow-2xs"
          />
        </div>

        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-700">Pincode to Apply</label>
          <input
            type="text"
            placeholder="e.g. 676505 (leave empty to keep unchanged)"
            value={pincode}
            onChange={(e) => setPincode(e.target.value.replace(/\D/g, '').slice(0, 6))}
            maxLength={6}
            className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-indigo-500 shadow-2xs font-mono"
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-700">Post Office (Optional)</label>
            <input
              type="text"
              placeholder="e.g. Manjeri H.O"
              value={postOffice}
              onChange={(e) => setPostOffice(e.target.value)}
              className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-indigo-500 shadow-2xs"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-700">State (Optional)</label>
            <input
              type="text"
              placeholder="e.g. Kerala"
              value={state}
              onChange={(e) => setState(e.target.value)}
              className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-indigo-500 shadow-2xs"
            />
          </div>
        </div>

        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-600">Bulk Update Reason / Notes</label>
          <input
            type="text"
            placeholder="e.g. Regional customer batch resolution"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="w-full bg-white border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-slate-700 placeholder-slate-400 focus:outline-none focus:border-indigo-500 shadow-2xs"
          />
        </div>
      </form>
    </Modal>
  );
};
