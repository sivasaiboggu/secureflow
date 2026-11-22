import { apiUnavailableReason } from '../../services/api';
import { Notice } from './Workspace';

export function ApiUnavailableBanner() {
  return apiUnavailableReason ? <div className="api-banner"><Notice tone="warning">{apiUnavailableReason}</Notice></div> : null;
}
