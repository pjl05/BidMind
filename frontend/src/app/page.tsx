"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import Cookies from "js-cookie";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { authService, taskService } from "@/lib/api";
import type { User } from "@/types/auth";

export default function HomePage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const token = Cookies.get("access_token");
    if (!token) {
      router.push("/login");
      return;
    }

    authService.getMe()
      .then((res) => {
        setUser(res.data);
        setLoading(false);
      })
      .catch(() => {
        Cookies.remove("access_token");
        router.push("/login");
      });
  }, [router]);

  const handleLogout = () => {
    authService.logout();
    router.push("/login");
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.type !== "application/pdf") {
      alert("请上传 PDF 文件");
      return;
    }

    if (file.size > 50 * 1024 * 1024) {
      alert("文件大小不能超过 50MB");
      return;
    }

    setUploading(true);
    try {
      const result = await taskService.create(file);
      const taskId = result.data?.task_id || result.data?.id;
      if (taskId) {
        router.push(`/analysis?task_id=${taskId}`);
      } else {
        alert("创建任务失败");
      }
    } catch (err) {
      console.error("Upload failed:", err);
      alert("上传失败，请重试");
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

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
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">
              {user?.nickname || user?.email}
            </span>
            <Button variant="outline" onClick={handleLogout}>
              退出登录
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <Card>
          <CardHeader>
            <CardTitle>欢迎使用 BidMind</CardTitle>
            <CardDescription>
              招投标智能分析Agent - 您的智能投标决策助手
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center gap-4">
              <p className="text-gray-600 text-center">
                上传您的招标文件，AI将自动分析资格要求、评分标准，
                并生成投标策略建议和方案大纲。
              </p>
              <input
                ref={fileInputRef}
                type="file"
                accept="application/pdf"
                className="hidden"
                onChange={handleFileSelect}
              />
              <Button
                onClick={triggerFileInput}
                disabled={uploading}
                className="w-full max-w-xs"
              >
                {uploading ? "上传中..." : "上传招标文件 (PDF)"}
              </Button>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}