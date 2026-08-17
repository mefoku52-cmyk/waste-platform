export const statusLabel = (status?: string) => {
  switch ((status || '').toLowerCase()) {
    case 'published': return 'Publikované';
    case 'open': return 'Otvorené';
    case 'closed': return 'Uzatvorené';
    case 'verified': return 'Overené';
    case 'pending': return 'Čaká na schválenie';
    case 'success': return 'Úspešné';
    default: return status || '—';
  }
};
