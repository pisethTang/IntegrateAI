"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import type { Integration } from "@/types/Integration";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Plus, RefreshCw, Settings, FileText } from "lucide-react";
import {
  // BarChart,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";


const syncData = [
  { day: "Mon", syncs: 12 },
  { day: "Tue", syncs: 18 },
  { day: "Wed", syncs: 15 },
  { day: "Thu", syncs: 22 },
  { day: "Fri", syncs: 28 },
  { day: "Sat", syncs: 8 },
  { day: "Sun", syncs: 10 },
];

const apiUsage = [
  { name: "Smartsheet", used: 234, limit: 500 },
  { name: "Airtable", used: 89, limit: 1000 },
  { name: "PostgreSQL", used: 1200, limit: 10000 },
];


const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const formatTimestamp = (timestamp: string | null) => {
  if (!timestamp) return "Never";
  return new Date(timestamp).toLocaleString("en-AU", {
    timeZone: "Australia/Adelaide",
    dateStyle: "short",
    timeStyle: "short",
  });
  
};






export default function DashboardPage() {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [loading, setLoading] = useState(true);
  const [recentSyncs, setRecentSyncs] = useState([]);


  const [metrics, setMetrics] = useState({
    total_syncs: 0,
    wasted_syncs: 0,
    efficiency: 0,
    sync_history: []
  });

  useEffect(() => {
    fetchIntegrations();
    fetchMetrics();
    fetchSyncHistory();
  }, []);


  const fetchMetrics = async () => {
    try {
      const response = await fetch(`${API_URL}/metrics/efficiency`);
      const data = await response.json();
      setMetrics(data);
    } catch (error) {
      console.error("Failed to fetch metrics:", error);
    }
  };

  const fetchSyncHistory = async () => {
    try {
      const response = await fetch(`${API_URL}/metrics/sync-history`);
      const data = await response.json();
      setRecentSyncs(data.metrics || []);
    } catch (error) {
      console.error("Failed to fetch sync history:", error);
    }
  };

  const triggerSync = async (integrationId: string) => {
    try {
      const response = await fetch(`${API_URL}/sync/${integrationId}/trigger`, {
        method: "POST",
      });
      const data = await response.json();

      console.log("Trigger sync response:", data);

      
      if (!response.ok) {
        throw new Error(data.error);
      }

      alert(`Sync complete: ${data.rows_written} rows written`);
      // fetchIntegrations();
      fetchMetrics();
      fetchSyncHistory();
    } catch (error) {
      alert("Failed to trigger sync");
    }
  };

  const fetchIntegrations = async () => {
    try {
      const response = await fetch(`${API_URL}/integrations`);
      const data = await response.json();
      console.log("Fetched integrations:", data);
      setIntegrations(data);
    } catch (error) {
      console.error("Failed to fetch integrations:", error);
    } finally {
      setLoading(false);
    }
  };


  // testing: run 5 syncs in a row to see efficiency impact
  const runTestSyncs = async () => {
    for (let i = 0; i < 5; i++) {
      await fetch(`${API_URL}/sync/1/trigger`, { method: "POST" });
      await new Promise(r => setTimeout(r, 300));
    }
    fetchIntegrations();
    fetchMetrics();
    fetchSyncHistory();
    alert("5 test syncs completed!");
  };


  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b bg-white px-6 py-4">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold">📊 Dashboard</h1>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Integration
          </Button>
        </div>
      </header>

      <main className="p-6">
        <div className="mx-auto max-w-6xl space-y-6">
          {/* Integrations */}
          <section>
            <h2 className="mb-4 text-lg font-semibold">Active Integrations</h2>
            {loading ? (
              <p>Loading...</p>
            ) : (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {integrations.map(
                  
                  (integration) => (

                  <Card key={integration.id}>
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-base">{integration.name}</CardTitle>
                        <Badge variant={integration.status === "active" ? "default" : "secondary"}>
                          {integration.status}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      {/* <p className="text-sm text-gray-600">
                        {integration.source} → {integration.target}
                      </p> */}
                      <div className="mt-3 space-y-1 text-xs text-gray-500">
                        <p>Last sync: {formatTimestamp(integration.last_sync)}</p>
                        <p>Next sync: {integration.next_sync ?? "On demand"}</p>
                        <p>Total syncs: {integration.sync_count}</p>
                      </div>
                      <div className="mt-4 flex gap-2">
                        <Button variant="outline" size="sm" onClick={() => triggerSync(integration.id)}>
                          <RefreshCw className="mr-1 h-3 w-3" />
                          Sync Now
                        </Button>
                        <Button variant="outline" size="sm">
                          <FileText className="mr-1 h-3 w-3" />
                          Logs
                        </Button>
                        <Button variant="outline" size="sm">
                          <Settings className="h-3 w-3" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>


                )
                
                
                )}
              </div>
            )}
          </section>

          {/* Charts Row */}
          <div className="grid gap-6 lg:grid-cols-3">
            {/* Sync Activity */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Sync Activity (7 days)</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={syncData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="day" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="syncs" stroke="#2563eb" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* API Usage */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">API Usage</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {apiUsage.map((api) => (
                  <div key={api.name}>
                    <div className="mb-1 flex justify-between text-sm">
                      <span>{api.name}</span>
                      <span className="text-gray-500">{api.used}/{api.limit}</span>
                    </div>
                    <Progress value={(api.used / api.limit) * 100} />
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* NEW: Sync Efficiency */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Sync Efficiency</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Total Syncs</span>
                  <span className="font-semibold">{metrics.total_syncs}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Wasted Syncs</span>
                  <span className="font-semibold text-red-500">{metrics.wasted_syncs}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Efficiency</span>
                  <span className={`font-semibold ${metrics.efficiency >= 70 ? 'text-green-500' : 'text-yellow-500'}`}>
                    {metrics.efficiency.toFixed(1)}%
                  </span>
                </div>
                <Progress value={metrics.efficiency} className="h-2" />
                <div className="flex gap-2 pt-2">
                  <Button size="sm" variant="outline" onClick={runTestSyncs}>
                    Run 5 Test Syncs
                  </Button>
                  <Button size="sm" variant="outline">
                    Train RL Agent
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Recent Syncs */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Recent Syncs</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Integration</TableHead>
                    <TableHead>Time</TableHead>
                    <TableHead>Rows</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {recentSyncs.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={4} className="text-center text-gray-500">
                        No syncs yet. Click "Sync Now" or "Run 5 Test Syncs"
                      </TableCell>
                    </TableRow>
                  ) : (
                    recentSyncs.map((sync: any, idx: number) => (
                      <TableRow key={idx}>
                        <TableCell>{sync.integration_id || "Google Sheets → Airtable"}</TableCell>
                        <TableCell>{new Date(sync.timestamp).toLocaleString()}</TableCell>
                        <TableCell>{sync.rows_written}</TableCell>
                        <TableCell>
                          <Badge variant={sync.rows_written > 0 ? "default" : "secondary"}>
                            {sync.rows_written > 0 ? "Success" : "No data"}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );

}