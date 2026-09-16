import React from 'react';
import { Badge } from '../common/Badge';

interface BatchStatusBadgeProps {
  status: string;
}

export const BatchStatusBadge: React.FC<BatchStatusBadgeProps> = ({ status }) => {
  switch (status.toUpperCase()) {
    case 'COMPLETED':
      return <Badge variant="emerald">COMPLETED</Badge>;
    case 'PARTIALLY_COMPLETED':
      return <Badge variant="amber">PARTIALLY COMPLETED</Badge>;
    case 'PROCESSING':
      return <Badge variant="blue">PROCESSING</Badge>;
    case 'FAILED':
      return <Badge variant="rose">FAILED</Badge>;
    default:
      return <Badge variant="slate">{status}</Badge>;
  }
};
