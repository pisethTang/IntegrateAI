"use client";

import { Button } from "@/components/ui/button";
import { Plus, MessageSquare } from "lucide-react";

import type Chat from "../types/Chat";

const mockChats: Chat[] = [
  { id: "1", title: "Smartsheet to Airtable setup", updatedAt: "2 min ago" },
  { id: "2", title: "Database sync question", updatedAt: "1 hour ago" },
  { id: "3", title: "New integration help", updatedAt: "Yesterday" },
];




export default function Sidebar({
  onNewChat,
}: {
  onNewChat: () => void;
}) {
  return (
    <aside className="flex h-full w-64 flex-col border-r bg-gray-100">
      {/* New Chat Button */}
      <div className="p-4">
        <Button onClick={onNewChat} className="w-full justify-start gap-2">
          <Plus className="h-4 w-4" />
          New Chat
        </Button>
      </div>

      {/* Navigation */}
      <nav className="px-2">
        <a
          href="/dashboard"
          className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200"
        >
          📊 Dashboard
        </a>
      </nav>

      {/* Chat History */}
      <div className="mt-4 flex-1 overflow-auto px-2">
        <p className="mb-2 px-3 text-xs font-semibold text-gray-500">
          Recent Chats
        </p>
        {mockChats.map((chat) => (
          <button
            key={chat.id}
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-200"
          >
            <MessageSquare className="h-4 w-4 shrink-0" />
            <div className="min-w-0">
              <p className="truncate">{chat.title}</p>
              <p className="text-xs text-gray-500">{chat.updatedAt}</p>
            </div>
          </button>
        ))}
      </div>
    </aside>
  );
}