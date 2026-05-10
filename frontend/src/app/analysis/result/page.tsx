"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Cookies from "js-cookie";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import api from "@/lib/api";

interface AnalysisResult {
  task_id: string;
  status: string;
  progress: number;
  final_report: string;
  requirements: any[];
  scoring_criteria: any[];
  bid_strategy: any;
}

function ResultContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const taskId = searchParams.get("task_id");

  const [result, setResult] = useState<AnalysisResult | null>(null);
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

    fetchResult();
  }, [taskId, router]);

  const fetchResult = async () => {
    try {
      const response = await api.get(`/analysis/${taskId}/result`, {
        headers: {
          Authorization: `Bearer ${Cookies.get("access_token")}`,
        },
      });

      if (response.data.code === 0) {
        setResult(response.data.data);
      }
    } catch (err) {
      console.error("Failed to fetch result:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p>加载中...</p>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p>未找到分析结果</p>
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

      <main className="container mx-auto px-4 py-8 space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>分析报告</CardTitle>
            <CardDescription>任务 ID: {result.task_id}</CardDescription>
          </CardHeader>
          <CardContent>
            <pre className="whitespace-pre-wrap text-sm">
              {result.final_report || "暂无报告内容"}
            </pre>
          </CardContent>
        </Card>

        {result.requirements && result.requirements.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>资格要求</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="list-disc pl-5 space-y-2">
                {result.requirements.map((req: any, idx: number) => (
                  <li key={idx}>
                    <strong>{req.category}:</strong> {req.content}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {result.scoring_criteria && result.scoring_criteria.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>评分标准</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="list-disc pl-5 space-y-2">
                {result.scoring_criteria.map((criteria: any, idx: number) => (
                  <li key={idx}>
                    <strong>{criteria.factor}</strong> (权重: {criteria.weight})
                    <br />
                    {criteria.details}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {result.bid_strategy && (
          <Card>
            <CardHeader>
              <CardTitle>投标策略</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <strong>策略方向：</strong>
                  <p>{result.bid_strategy.direction}</p>
                </div>
                <div>
                  <strong>重点材料：</strong>
                  <ul className="list-disc pl-5">
                    {(result.bid_strategy.key_materials || []).map((m: string, idx: number) => (
                      <li key={idx}>{m}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <strong>风险评估：</strong>
                  <p>{result.bid_strategy.risk_assessment}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  );
}

export default function AnalysisResultPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center min-h-screen"><p>加载中...</p></div>}>
      <ResultContent />
    </Suspense>
  );
}