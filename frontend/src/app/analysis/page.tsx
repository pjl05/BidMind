"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Cookies from "js-cookie";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { taskService } from "@/lib/api";
import type { Task } from "@/types/auth";

function AnalysisContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const taskId = searchParams.get("task_id");

  const [task, setTask] = useState<Task | null>(null);
  const [progress, setProgress] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!taskId) {
      router.push("/");
      return;
    }

    const token = Cookies.get("access_token");
    if (!token) {
      router.push("/login");
      return;
    }

    fetchTask();
    startAnalysis();
  }, [taskId, router]);

  const fetchTask = async () => {
    try {
      const response = await taskService.list(1, 10);
      const found = response.data?.items?.find((t: Task) => t.task_id === taskId);
      if (found) {
        setTask(found);
        setProgress(found.progress || 0);
      }
    } catch (err) {
      console.error("Failed to fetch task:", err);
    } finally {
      setLoading(false);
    }
  };

  const startAnalysis = async () => {
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL}/analysis/${taskId}/start`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${Cookies.get("access_token")}`,
        },
      });
    } catch (err) {
      console.error("Start analysis failed:", err);
    }
  };

  useEffect(() => {
    if (!taskId || progress >= 100) return;

    const interval = setInterval(async () => {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/analysis/${taskId}/result`,
          {
            headers: {
              Authorization: `Bearer ${Cookies.get("access_token")}`,
            },
          }
        );
        const data = await response.json();
        if (data.code === 0 && data.data) {
          setProgress(data.data.progress || 0);
          if (data.data.status === "completed") {
            clearInterval(interval);
          }
        }
      } catch (err) {
        console.error("Progress update failed:", err);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [taskId, progress]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p>加载中...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-primary">BidMind</h1>
          <Button variant="outline" onClick={() => router.push("/")}>
            返回首页
          </Button>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <Card>
          <CardHeader>
            <CardTitle>文档分析中</CardTitle>
            <CardDescription>{task?.file_name}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span>分析进度</span>
                  <span>{progress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-primary h-2 rounded-full transition-all"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>

              {progress >= 100 && (
                <div className="mt-6">
                  <Button onClick={() => router.push(`/analysis/result?task_id=${taskId}`)}>
                    查看分析结果
                  </Button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}

export default function AnalysisPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center min-h-screen"><p>加载中...</p></div>}>
      <AnalysisContent />
    </Suspense>
  );
}