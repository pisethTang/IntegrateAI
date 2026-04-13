export type Integration = {
  id: string;
  name: string;
  source: string;
  target: string;
  status: string;
  lastSync: string;
  nextSync: string;
  syncCount: number;
};