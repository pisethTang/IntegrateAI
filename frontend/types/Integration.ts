export type Integration = {
  id: string;
  name: string;
  status: string;
  source: string;
  target: string;
  last_sync: string | null;
  next_sync: string | null;
  sync_count: number;
};