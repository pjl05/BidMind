"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Cookies from "js-cookie";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { authService } from "@/lib/api";
import type { User } from "@/types/auth";

export default function HomePage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

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
            <p className="text-gray-600">
              上传您的招标文件，AI将自动分析资格要求、评分标准，
              并生成投标策略建议和方案大纲。
            </p>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}