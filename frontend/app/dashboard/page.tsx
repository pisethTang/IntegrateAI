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
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

// Mock data
const integrations = [
  {
    id: "1",
    name: "Smartsheet → Airtable",
    source: "Projects",
    target: "Active Projects",
    status: "active",
    lastSync: "2 min ago",
    nextSync: "58 min",
    syncCount: 128,
  },
  {
    id: "2",
    name: "PostgreSQL → S3",
    source: "analytics",
    target: "s3://integrateai-bucket/",
    status: "paused",
    lastSync: "1 hour ago",
    nextSync: "23 hours",
    syncCount: 45,
  },
];

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

const recentSyncs = [
  { id: "1", integration: "Smartsheet → Airtable", time: "2 min ago", rows: 45, status: "success" },
  { id: "2", integration: "PostgreSQL → S3", time: "1 hour ago", size: "1.2 MB", status: "success" },
  { id: "3", integration: "Smartsheet → Airtable", time: "3 hours ago", rows: 23, status: "error" },
];



const API_URL = "http://localhost:8000";






export default function DashboardPage() {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchIntegrations();
  }, []);

  const fetchIntegrations = async () => {
    try {
      const response = await fetch(`${API_URL}/integrations`);
      const data = await response.json();
      setIntegrations(data);
    } catch (error) {
      console.error("Failed to fetch integrations:", error);
    } finally {
      setLoading(false);
    }
  };

  const triggerSync = async (integrationId: string) => {
    try {
      const response = await fetch(`${API_URL}/sync/${integrationId}/trigger`, {
        method: "POST",
      });
      const data = await response.json();
      alert(data.message);
      // Refresh integrations
      fetchIntegrations();
    } catch (error) {
      alert("Failed to trigger sync");
    }
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
          <section>
            <h2 className="mb-4 text-lg font-semibold">Active Integrations</h2>
            {loading ? (
              <p>Loading...</p>
            ) : (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {integrations.map((integration) => (
                  <Card key={integration.id}>
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-base">{integration.name}</CardTitle>
                        <Badge
                          variant={integration.status === "active" ? "default" : "secondary"}
                        >
                          {integration.status}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-gray-600">
                        {integration.source} → {integration.target}
                      </p>
                      <div className="mt-3 space-y-1 text-xs text-gray-500">
                        <p>Last sync: {integration.lastSync}</p>
                        <p>Next sync: {integration.nextSync}</p>
                        <p>Total syncs: {integration.syncCount}</p>
                      </div>
                      <div className="mt-4 flex gap-2">
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => triggerSync(integration.id)}
                        >
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
                ))}
              </div>
            )}
          </section>

          <div className="grid gap-6 lg:grid-cols-2">
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
          </div>

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
                    <TableHead>Data</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {recentSyncs.map((sync) => (
                    <TableRow key={sync.id}>
                      <TableCell>{sync.integration}</TableCell>
                      <TableCell>{sync.time}</TableCell>
                      <TableCell>{sync.rows ? `${sync.rows} rows` : sync.size}</TableCell>
                      <TableCell>
                        <Badge variant={sync.status === "success" ? "default" : "destructive"}>
                          {sync.status}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}