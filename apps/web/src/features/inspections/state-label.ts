import type { InspectionState } from './types';

const STATE_LABEL: Record<InspectionState, string> = {
  created: 'created',
  room_created: 'roomCreated',
  requested: 'requested',
  accepted: 'accepted',
  live: 'live',
  ended: 'ended',
};

export function inspectionStateLabel(state: InspectionState): string {
  return STATE_LABEL[state] ?? String(state);
}
