"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2, Send } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import Sidebar from "../components/Sidebar";

import Message from "../types/Message";




const API_URL = "http://localhost:8000";

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "Welcome! I'm your integration assistant. I can help you connect systems like Smartsheet, Airtable, and databases. What would you like to do?",
      actions: [
        { label: "Connect Smartsheet", action: "select_smartsheet" },
        { label: "Connect Airtable", action: "select_airtable" },
        { label: "Connect Database", action: "select_database" },
      ],
    },
  ]);
  const [input, setInput] = useState("");
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingMessageId]);

  const handleAction = async (action: string) => {
    const actionLabels: Record<string, string> = {
      select_smartsheet: "I want to connect Smartsheet",
      select_airtable: "I want to connect Airtable",
      select_database: "I want to connect a database",
      auth_smartsheet: "Connect to Smartsheet",
      auth_airtable: "Connect to Airtable",
    };

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: actionLabels[action] || action,
    };
    setMessages((prev) => [...prev, userMessage]);

    await sendToBackend(actionLabels[action] || action);
  };

  const sendToBackend = async (message: string) => {
    const aiMessageId = (Date.now() + 1).toString();
    setMessages((prev) => [
      ...prev,
      {
        id: aiMessageId,
        role: "assistant",
        content: "",
        isStreaming: true,
      },
    ]);
    setStreamingMessageId(aiMessageId);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });

      const data = await response.json();
      if (!response.ok) {
        const detail = typeof data?.detail === "string" ? data.detail : "Backend request failed";
        throw new Error(detail);
      }

      setStreamingMessageId(null);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === aiMessageId
            ? {
                ...m,
                content: data.response,
                isStreaming: false,
                actions: data.actions,
              }
            : m
        )
      );
    } catch (error) {
      console.error("Chat request failed:", error);
      setStreamingMessageId(null);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === aiMessageId
            ? {
                ...m,
                content: "Sorry, I couldn't connect to the server. Is the backend running?",
                isStreaming: false,
              }
            : m
        )
      );
    }
  };

  const handleNewChat = () => {
    setMessages([
      {
        id: "welcome",
        role: "assistant",
        content: "Welcome! I'm your integration assistant. What would you like to do?",
        actions: [
          { label: "Connect Smartsheet", action: "select_smartsheet" },
          { label: "Connect Airtable", action: "select_airtable" },
          { label: "Connect Database", action: "select_database" },
        ],
      },
    ]);
    setStreamingMessageId(null);
  };

  const handleSend = () => {
    const trimmedInput = input.trim();
    if (!trimmedInput) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: trimmedInput,
    };
    setMessages((prev) => [...prev, userMessage]);

    sendToBackend(trimmedInput);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar onNewChat={handleNewChat} />

      <div className="flex flex-1 flex-col">
        <header className="border-b bg-white px-6 py-4">
          <h1 className="text-xl font-semibold">🔗 IntegrateAI</h1>
        </header>

        <ScrollArea className="flex-1 px-4 py-6">
          <div className="mx-auto max-w-3xl space-y-6">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-4 ${
                  message.role === "user" ? "flex-row-reverse" : ""
                }`}
              >
                <Avatar className="h-8 w-8">
                  <AvatarFallback>
                    {message.role === "user" ? "U" : "🤖"}
                  </AvatarFallback>
                </Avatar>
                <div className={`max-w-[80%] ${message.role === "user" ? "" : "w-full"}`}>
                  <Card
                    className={`px-4 py-3 ${
                      message.role === "user"
                        ? "bg-blue-600 text-white"
                        : "bg-white"
                    }`}
                  >
                    <div className="text-sm leading-relaxed">
                      {message.role === "assistant" && message.isStreaming && !message.content ? (
                        <div className="flex items-center gap-2 text-gray-600">
                          <Loader2 className="h-4 w-4 animate-spin" />
                          <span>Gemini is thinking...</span>
                        </div>
                      ) : message.role === "assistant" ? (
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          components={{
                            p: ({ ...props }) => <p className="mb-2 last:mb-0" {...props} />,
                            ul: ({ ...props }) => <ul className="list-disc space-y-1 pl-5" {...props} />,
                            ol: ({ ...props }) => <ol className="list-decimal space-y-1 pl-5" {...props} />,
                            code: ({ ...props }) => (
                              <code className="rounded bg-gray-100 px-1 py-0.5 text-xs" {...props} />
                            ),
                          }}
                        >
                          {message.content}
                        </ReactMarkdown>
                      ) : (
                        <p className="whitespace-pre-wrap">{message.content}</p>
                      )}
                    </div>
                  </Card>
                  {message.actions && message.actions.length > 0 && !message.isStreaming && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {message.actions.map((action, idx) => (
                        <Button
                          key={idx}
                          variant="outline"
                          size="sm"
                          onClick={() => handleAction(action.action)}
                          className="bg-white hover:bg-gray-100"
                        >
                          {action.label}
                        </Button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            <div ref={scrollRef} />
          </div>
        </ScrollArea>

        <div className="border-t bg-white px-4 py-4">
          <div className="mx-auto flex max-w-3xl gap-2">
            <Input
              placeholder="Type a message..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              className="flex-1"
            />
            <Button onClick={handleSend} size="icon">
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}